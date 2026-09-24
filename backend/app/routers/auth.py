"""Autenticación: registro, inicio de sesión y gestión de la contraseña."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    create_reset_token,
    decode_reset_token,
    verify_password,
)
from app.crud import usuario as usuario_crud
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.common import RESPUESTA_409, RESPUESTA_422, RESPUESTAS_AUTH
from app.models.usuario import Usuario
from app.schemas.common import MensajeRespuesta
from app.schemas.usuario import (
    CambiarPasswordRequest,
    LoginRequest,
    RecuperarPasswordRequest,
    RestablecerPasswordRequest,
    TokenOut,
    UsuarioCreate,
    UsuarioOut,
)
from app.services import email as email_service

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un cliente nuevo",
    description=(
        "Da de alta un cliente desde el formulario público del sitio.\n\n"
        "El backend **revalida** todos los campos aunque React ya los haya "
        "validado, comprueba que el correo y el documento no estén repetidos, "
        "convierte la contraseña en un hash bcrypt y envía el correo de "
        "bienvenida en segundo plano (`BackgroundTasks`), sin hacer esperar "
        "la respuesta.\n\n"
        "La contraseña original nunca se almacena."
    ),
    responses={**RESPUESTA_409, **RESPUESTA_422},
)
async def registro(
    data: UsuarioCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        usuario = await usuario_crud.create_usuario(db, data, rol_nombre="cliente")
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    # Tarea no bloqueante: el correo se envía después de responder al cliente.
    background_tasks.add_task(email_service.enviar_bienvenida, usuario.nombre, usuario.email)
    return usuario


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Iniciar sesión y obtener el JWT",
    description=(
        "Valida las credenciales y devuelve un JSON Web Token firmado junto "
        "con los datos del usuario.\n\n"
        "El token se envía en las peticiones protegidas como "
        "`Authorization: Bearer <token>`.\n\n"
        "Limitado por IP para frenar ataques de fuerza bruta."
    ),
    responses={
        401: {"description": "Correo o contraseña incorrectos."},
        403: {"description": "La cuenta está inactiva."},
        429: {"description": "Demasiados intentos: espera un minuto."},
    },
)
@limiter.limit(settings.login_rate_limit)
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    usuario = await usuario_crud.get_by_email(db, data.email)

    # Mismo mensaje para «no existe» y «contraseña incorrecta»: así no se
    # puede averiguar qué correos están registrados.
    if not usuario or not verify_password(data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu cuenta está inactiva. Contacta con la galería.",
        )

    token = create_access_token(sub=usuario.email, rol=usuario.rol.nombre)
    return TokenOut(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        usuario=usuario,
    )


@router.post(
    "/token",
    response_model=TokenOut,
    summary="Inicio de sesión compatible con OAuth2 (botón Authorize de Swagger)",
    description=(
        "Variante del login que acepta `application/x-www-form-urlencoded`, "
        "como exige el flujo *OAuth2 password*. Sirve para autenticarse desde "
        "el botón **Authorize** de esta misma documentación.\n\n"
        "Usa el correo en el campo `username`. El frontend usa `/auth/login`."
    ),
    responses=RESPUESTAS_AUTH,
)
async def token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await login(
        request, LoginRequest(email=form_data.username, password=form_data.password), db
    )


@router.get(
    "/me",
    response_model=UsuarioOut,
    summary="Datos del usuario autenticado",
    description=(
        "Devuelve el perfil asociado al token, con su rol y permisos. "
        "React la usa al cargar para restaurar la sesión y decidir qué panel "
        "mostrar."
    ),
    responses=RESPUESTAS_AUTH,
)
async def me(usuario: Usuario = Depends(get_current_user)):
    return usuario


@router.post(
    "/recuperar-password",
    response_model=MensajeRespuesta,
    summary="Solicitar el enlace de recuperación de contraseña",
    description=(
        "Envía por correo un enlace con un token temporal.\n\n"
        "Responde siempre lo mismo exista o no la cuenta: de lo contrario, "
        "este endpoint permitiría averiguar qué correos están registrados."
    ),
    responses={429: {"description": "Demasiadas solicitudes: espera un minuto."}},
)
@limiter.limit(settings.login_rate_limit)
async def recuperar_password(
    request: Request,
    data: RecuperarPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    usuario = await usuario_crud.get_by_email(db, data.email)
    if usuario and usuario.activo:
        token = create_reset_token(sub=usuario.email)
        background_tasks.add_task(
            email_service.enviar_recuperacion, usuario.nombre, usuario.email, token
        )
    return MensajeRespuesta(
        mensaje=(
            "Si el correo está registrado, recibirás las instrucciones para "
            "restablecer tu contraseña en unos minutos."
        )
    )


@router.post(
    "/restablecer-password",
    response_model=MensajeRespuesta,
    summary="Fijar una contraseña nueva con el token del correo",
    description=(
        "Comprueba la firma y la vigencia del token de recuperación y guarda "
        "el hash de la contraseña nueva. El token caduca a los "
        f"{settings.reset_token_expire_minutes} minutos y no sirve para "
        "autenticarse en el resto de la API."
    ),
    responses={400: {"description": "El token es inválido o ya caducó."}, **RESPUESTA_422},
)
async def restablecer_password(
    data: RestablecerPasswordRequest, db: AsyncSession = Depends(get_db)
):
    try:
        payload = decode_reset_token(data.token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación es inválido o ya caducó. Solicita uno nuevo.",
        )

    usuario = await usuario_crud.get_by_email(db, payload.get("sub", ""))
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="El enlace ya no es válido."
        )

    await usuario_crud.actualizar_password(db, usuario, data.password)
    return MensajeRespuesta(mensaje="Tu contraseña se actualizó correctamente.")


@router.post(
    "/cambiar-password",
    response_model=MensajeRespuesta,
    summary="Cambiar la contraseña con la sesión iniciada",
    description="Pide la contraseña actual antes de aceptar la nueva.",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_422},
)
async def cambiar_password(
    data: CambiarPasswordRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if not verify_password(data.password_actual, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="La contraseña actual no es correcta."
        )
    await usuario_crud.actualizar_password(db, usuario, data.password_nueva)
    return MensajeRespuesta(mensaje="Contraseña actualizada correctamente.")
