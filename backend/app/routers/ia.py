from fastapi import APIRouter, Depends, Query, Request

from app.dependencies.auth import require_roles
from app.services import ai_external, ai_local

router = APIRouter(prefix="/ia", tags=["inteligencia artificial"])


@router.get("/precio-sugerido")
async def precio_sugerido(
    request: Request,
    anio: int = Query(...),
    tecnica: str = Query(...),
    _u=Depends(require_roles("administrador", "empleado")),
):
    modelo = getattr(request.app.state, "ai_local_model", None)
    return ai_local.predecir_precio(modelo, anio, tecnica)


@router.get("/descripcion-sugerida")
async def descripcion_sugerida(
    titulo: str = Query(...),
    tecnica: str = Query(...),
    _u=Depends(require_roles("administrador", "empleado")),
):
    return await ai_external.generar_descripcion_sugerida(titulo, tecnica)
