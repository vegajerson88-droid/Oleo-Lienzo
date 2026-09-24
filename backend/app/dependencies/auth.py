"""Dependencias de autenticación y autorización.

La autorización definitiva es siempre responsabilidad del backend: el frontend
puede ocultar botones, pero quien decide es esta capa.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.crud.usuario import get_by_email
from app.database import get_db
from app.models.usuario import Usuario

# `auto_error=False` para poder devolver un 401 con nuestro formato de error
# uniforme en lugar del de Starlette.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)

CREDENCIALES_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado o token inválido.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Usuario autenticado a partir del JWT del encabezado Authorization.

    Verifica existencia, firma, expiración y que el usuario siga activo.
    """
    if not token:
        raise CREDENCIALES_INVALIDAS
    try:
        payload = decode_access_token(token)
    except JWTError:
        # Cubre firma inválida, token manipulado y token expirado.
        raise CREDENCIALES_INVALIDAS

    email: str | None = payload.get("sub")
    if not email:
        raise CREDENCIALES_INVALIDAS

    usuario = await get_by_email(db, email)
    if not usuario or not usuario.activo:
        raise CREDENCIALES_INVALIDAS
    return usuario


async def get_current_user_opcional(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario | None:
    """Igual que `get_current_user`, pero devuelve None si no hay sesión.

    La usan los endpoints públicos que enriquecen su respuesta cuando el
    visitante sí ha iniciado sesión, como el chatbot y la radicación de PQR.
    """
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


def require_roles(*roles_permitidos: str):
    """Exige que el usuario autenticado tenga uno de los roles indicados."""

    async def verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol.nombre not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Esta operación requiere uno de estos roles: "
                    f"{', '.join(roles_permitidos)}. Tu rol es '{usuario.rol.nombre}'."
                ),
            )
        return usuario

    return verificar


def require_permiso(codigo: str):
    """Exige un permiso concreto del catálogo de permisos.

    Es más fino que `require_roles`: permite cambiar qué puede hacer un rol
    sin tocar el código, simplemente reasignando permisos en la base de datos.
    """

    async def verificar(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if not usuario.tiene_permiso(codigo):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu rol '{usuario.rol.nombre}' no tiene el permiso '{codigo}'.",
            )
        return usuario

    return verificar


# Atajos usados en toda la API.
solo_admin = require_roles("administrador")
admin_o_empleado = require_roles("administrador", "empleado")
solo_cliente = require_roles("cliente")
