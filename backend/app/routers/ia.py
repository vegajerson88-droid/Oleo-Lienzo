"""Endpoints de Inteligencia Artificial aplicada al catálogo."""

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies.auth import admin_o_empleado
from app.dependencies.common import RESPUESTAS_AUTH
from app.services import ai_external, ai_local

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"], responses=RESPUESTAS_AUTH)


@router.get(
    "/precio-sugerido",
    summary="Sugerir un precio con el modelo propio",
    description=(
        "Estima el precio de una obra con un modelo de **regresión lineal "
        "entrenado con el propio catálogo** (scikit-learn), a partir del año "
        "y de si la técnica es óleo.\n\n"
        "El modelo se entrena con `seed.py` y se carga **una sola vez** en el "
        "arranque de la aplicación (`app.state`), no en cada petición.\n\n"
        "Si todavía no se ha entrenado, responde `disponible: false` con el "
        "motivo en lugar de devolver un número inventado."
    ),
)
async def precio_sugerido(
    request: Request,
    anio: int = Query(ge=1400, le=2100, description="Año de creación de la obra."),
    tecnica: str = Query(min_length=2, max_length=80, description="Técnica empleada."),
    _u=Depends(admin_o_empleado),
):
    modelo = getattr(request.app.state, "ai_local_model", None)
    return ai_local.predecir_precio(modelo, anio, tecnica)


@router.get(
    "/descripcion-sugerida",
    summary="Redactar una descripción con IA externa",
    description=(
        "Pide a **Groq** una frase de catálogo para una obra. La clave vive en "
        "`GROQ_API_KEY` y no sale del servidor.\n\n"
        "Reintenta una vez ante fallos de red y, si aun así no hay respuesta, "
        "devuelve `disponible: false` con el motivo: no inventa un texto "
        "haciéndolo pasar por generado."
    ),
)
async def descripcion_sugerida(
    titulo: str = Query(min_length=2, max_length=120, description="Título de la obra."),
    tecnica: str = Query(min_length=2, max_length=80, description="Técnica empleada."),
    _u=Depends(admin_o_empleado),
):
    return await ai_external.generar_descripcion_sugerida(titulo, tecnica)
