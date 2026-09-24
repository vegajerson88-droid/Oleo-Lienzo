import time

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database import get_db
from app.dependencies.auth import require_roles
from app.services import ai_external

router = APIRouter(prefix="/sistema", tags=["sistema"])
settings = get_settings()


async def _check_db(db: AsyncSession) -> dict:
    inicio = time.perf_counter()
    try:
        await db.execute(text("SELECT 1"))
        return {"estado": "ok", "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2)}
    except Exception as exc:
        return {
            "estado": "error",
            "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
            "detalle": str(exc),
        }


async def _check_ia_local(request: Request) -> dict:
    inicio = time.perf_counter()
    modelo = getattr(request.app.state, "ai_local_model", None)
    return {
        "estado": "ok" if modelo is not None else "no_disponible",
        "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
        "detalle": None if modelo is not None else "Modelo local no entrenado/cargado.",
    }


async def _check_ia_externa() -> dict:
    inicio = time.perf_counter()
    if not settings.external_ai_api_key:
        return {
            "estado": "no_configurado",
            "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
            "detalle": "Falta EXTERNAL_AI_API_KEY en .env.",
        }
    resultado = await ai_external.generar_descripcion_sugerida("prueba", "óleo")
    return {
        "estado": "ok" if resultado.get("disponible") else "error",
        "latencia_ms": round((time.perf_counter() - inicio) * 1000, 2),
        "detalle": resultado.get("detalle"),
    }


@router.get("/diagnostico")
async def diagnostico(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("administrador")),
):
    """Comprueba cada dependencia por separado; un fallo en una no tumba a las demás."""
    db_status = await _check_db(db)
    ia_local_status = await _check_ia_local(request)
    ia_externa_status = await _check_ia_externa()

    componentes = {
        "base_de_datos": db_status,
        "ia_local": ia_local_status,
        "ia_externa": ia_externa_status,
    }
    estado_general = (
        "ok" if all(c["estado"] in ("ok", "no_disponible", "no_configurado") for c in componentes.values())
        else "degradado"
    )
    return {"estado_general": estado_general, "componentes": componentes}
