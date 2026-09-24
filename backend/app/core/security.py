"""Hashing de contraseñas y emisión/verificación de JSON Web Tokens."""

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# bcrypt: algoritmo de hashing lento y con sal automática, pensado para
# contraseñas. Nunca se guarda la contraseña en claro.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Distingue el token de sesión del de recuperación de contraseña: un token de
# recuperación no debe servir para autenticarse en la API.
TIPO_ACCESO = "acceso"
TIPO_RESET = "reset"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password_plano: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password_plano, password_hash)
    except ValueError:
        # Hash corrupto o con formato desconocido: se trata como no coincidente.
        return False


def create_access_token(sub: str, rol: str, expires_minutes: int | None = None) -> str:
    """Token de sesión. Incluye el rol para que el frontend adapte su interfaz."""
    minutos = expires_minutes or settings.jwt_expire_minutes
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "rol": rol,
        "tipo": TIPO_ACCESO,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=minutos),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_reset_token(sub: str) -> str:
    """Token de un solo uso para restablecer la contraseña."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "tipo": TIPO_RESET,
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.reset_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decodifica un token de sesión. Lanza JWTError si no es válido.

    Rechaza explícitamente los tokens de recuperación: sin esta comprobación,
    el enlace del correo serviría para entrar en la API.
    """
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("tipo") not in (TIPO_ACCESO, None):
        from jose import JWTError

        raise JWTError("El token no es de tipo acceso.")
    return payload


def decode_reset_token(token: str) -> dict:
    """Decodifica un token de recuperación. Lanza JWTError si no es válido."""
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("tipo") != TIPO_RESET:
        from jose import JWTError

        raise JWTError("El token no es de tipo recuperación.")
    return payload
