from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.core.security import create_access_token, verify_password
from app.crud.usuario import create_usuario, get_by_email
from app.database import AsyncSessionLocal, get_db
from app.dependencies.auth import get_current_user
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenOut, UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/auth", tags=["autenticación"])


async def _registrar_auditoria(usuario_id: int, accion: str) -> None:
    """Tarea en segundo plano: registra la acción en su propia sesión de DB.

    Maneja sus propios errores para no afectar la respuesta principal.
    """
    try:
        async with AsyncSessionLocal() as db:
            # Auditoría mínima: se podría persistir en una tabla `auditoria`.
            # Aquí se deja preparado el patrón (sesión propia + manejo de errores).
            print(f"[AUDITORÍA] usuario_id={usuario_id} accion={accion}")
    except Exception as exc:  # nunca debe tumbar la operación principal
        print(f"[AUDITORÍA][ERROR] no se pudo registrar: {exc}")


@router.post("/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def registro(
    data: UsuarioCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        usuario = await create_usuario(db, data, rol_nombre="cliente")
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    background_tasks.add_task(_registrar_auditoria, usuario.id, "registro")
    return usuario


@router.post("/login", response_model=TokenOut)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    usuario = await get_by_email(db, data.email)
    if not usuario or not verify_password(data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo.")

    token = create_access_token(sub=usuario.email, rol=usuario.rol.nombre)
    return TokenOut(access_token=token, usuario=usuario)


@router.post("/token", response_model=TokenOut)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint compatible con OAuth2 password flow, usado por el botón Authorize de Swagger.
    El frontend real usa /auth/login (JSON) en su lugar."""
    return await login(LoginRequest(email=form_data.username, password=form_data.password), db)


@router.get("/me", response_model=UsuarioOut)
async def me(usuario: Usuario = Depends(get_current_user)):
    return usuario
