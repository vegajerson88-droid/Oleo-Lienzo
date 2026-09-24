"""Diagnóstico y estado del sistema."""
import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database import get_db
from app.dependencies.auth import solo_admin
from app.dependencies.common import RESPUESTAS_AUTH
from app.services import chatbot as chatbot_service
from app.services import email as email_service
from app.services import pagos as pagos_service

router = APIRouter(prefix="/sistema", tags=["Sistema"])
settings = get_settings()


def _medir(inicio: float) -> float:
    return round((time.perf_counter() - inicio) * 1000, 2)


async def _check_db(db: AsyncSession) -> dict:
    """Ejecuta una consulta real contra la base de datos.

    La salud la determina el `SELECT 1`. La versión del motor es información
    adicional y solo existe en PostgreSQL, así que su ausencia no convierte
    una base sana en un fallo.
    """
    inicio = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        return {"estado": "error", "latencia_ms": _medir(inicio), "detalle": str(exc)}

    latencia = _medir(inicio)
    motor = db.bind.dialect.name if db.bind is not None else "desconocido"
    try:
        version = (await db.execute(text("SELECT version()"))).scalar()
        if version:
            motor = str(version).split(",")[0]
    except Exception:
        await db.rollback()  # la consulta fallida deja la transacción abortada
    return {"estado": "ok", "latencia_ms": latencia, "detalle": motor}


async def _check_ia_local(request: Request) -> dict:
    inicio = time.perf_counter()
    modelo = getattr(request.app.state, "ai_local_model", None)
    return {
        "estado": "ok" if modelo is not None else "no_disponible",
        "latencia_ms": _medir(inicio),
        "detalle": (
            f"Modelo {modelo.version} cargado en memoria."
            if modelo is not None
            else "Modelo local no entrenado. Ejecuta `python seed.py`."
        ),
    }


async def _check_ia_externa() -> dict:
    """Llama de verdad a Groq: no se limita a mirar si hay una clave escrita."""
    inicio = time.perf_counter()
    resultado = await chatbot_service.comprobar_disponibilidad()
    estado = "ok" if resultado["disponible"] else (
        "no_configurado" if not settings.groq_configurado else "error"
    )
    return {"estado": estado, "latencia_ms": _medir(inicio), "detalle": resultado["detalle"]}


async def _check_stripe() -> dict:
    inicio = time.perf_counter()
    resultado = await pagos_service.comprobar_disponibilidad()
    estado = "ok" if resultado["disponible"] else (
        "no_configurado" if not settings.stripe_configurado else "error"
    )
    return {"estado": estado, "latencia_ms": _medir(inicio), "detalle": resultado["detalle"]}


async def _check_email() -> dict:
    """Abre una conexión SMTP real y cierra: comprueba host, puerto y credenciales."""
    import asyncio
    import smtplib

    inicio = time.perf_counter()
    if not settings.email_configurado:
        return {
            "estado": "no_configurado",
            "latencia_ms": _medir(inicio),
            "detalle": "Faltan EMAIL_HOST, EMAIL_USER o EMAIL_PASSWORD en .env.",
        }

    def probar() -> str:
        with smtplib.SMTP(
            settings.email_host, settings.email_port, timeout=settings.email_timeout_seconds
        ) as servidor:
            if settings.email_use_tls:
                servidor.starttls()
            servidor.login(settings.email_user, settings.email_password)
        return f"Conexión SMTP con {settings.email_host} verificada."

    try:
        detalle = await asyncio.to_thread(probar)
        return {"estado": "ok", "latencia_ms": _medir(inicio), "detalle": detalle}
    except Exception as exc:
        return {
            "estado": "error",
            "latencia_ms": _medir(inicio),
            "detalle": f"{type(exc).__name__}: {exc}",
        }


@router.get(
    "/salud",
    summary="Comprobación rápida de vida",
    description=(
        "Endpoint público y ligero para balanceadores y plataformas de "
        "despliegue. No consulta servicios externos."
    ),
)
async def salud():
    return {"estado": "ok", "servicio": settings.app_name, "version": settings.app_version}


@router.get(
    "/diagnostico",
    summary="Diagnóstico completo de dependencias",
    description=(
        "Comprueba **de verdad** cada dependencia, una por una, y no se limita "
        "a devolver `ok`:\n\n"
        "- **Base de datos**: ejecuta una consulta real y reporta el motor.\n"
        "- **IA local**: comprueba si el modelo está cargado en memoria.\n"
        "- **IA externa (Groq)**: hace una llamada real a la API.\n"
        "- **Stripe**: consulta el balance para validar las credenciales.\n"
        "- **Correo SMTP**: abre la conexión y autentica.\n\n"
        "Cada componente reporta estado, latencia en milisegundos y un "
        "detalle. El fallo de uno **no tumba** la comprobación de los demás.\n\n"
        "El estado general es `degradado` si algún componente está en `error`; "
        "`no_configurado` no cuenta como fallo, porque las integraciones "
        "opcionales pueden estar apagadas a propósito."
    ),
    responses=RESPUESTAS_AUTH,
)
async def diagnostico(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(solo_admin),
):
    componentes = {
        "base_de_datos": await _check_db(db),
        "ia_local": await _check_ia_local(request),
        "ia_externa": await _check_ia_externa(),
        "pasarela_pago": await _check_stripe(),
        "correo": await _check_email(),
    }
    hay_errores = any(c["estado"] == "error" for c in componentes.values())
    return {
        "estado_general": "degradado" if hay_errores else "ok",
        "entorno": settings.environment,
        "version": settings.app_version,
        "componentes": componentes,
    }
