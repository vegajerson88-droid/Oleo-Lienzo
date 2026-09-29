"""Endpoints de Inteligencia Artificial aplicada al catálogo."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import obra as obra_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado
from app.dependencies.common import RESPUESTA_404, RESPUESTA_422, RESPUESTAS_AUTH
from app.services import ai_external, ai_local

router = APIRouter(
    prefix="/ia",
    tags=["Inteligencia Artificial"],
    # La regla vale para todo el recurso: se declara una sola vez aquí.
    dependencies=[Depends(admin_o_empleado)],
    responses=RESPUESTAS_AUTH,
)


@router.get(
    "/precio-sugerido",
    summary="Sugerir un precio con el modelo propio",
    description=(
        "Estima el precio de una obra con un modelo de **regresión lineal "
        "entrenado con el propio catálogo** (scikit-learn), a partir del año "
        "y de si la técnica es óleo.\n\n"
        "El modelo se entrena con `seed.py` y se carga **una sola vez** en el "
        "arranque de la aplicación (`app.state`), no en cada petición.\n\n"
        "Hay dos formas de usarlo:\n\n"
        "- Con `obra_id`: el servidor **lee la obra de la base de datos** y "
        "deriva de ella las variables. El cliente no aporta ningún dato.\n"
        "- Con `anio` y `tecnica`: para estimar el precio de una obra que "
        "todavía no existe, mientras se rellena el formulario.\n\n"
        "En ambos casos el vector de variables lo construye el servidor: el "
        "cliente nunca envía los valores que consume el modelo.\n\n"
        "La predicción se ejecuta con `run_in_threadpool`, porque scikit-learn "
        "es síncrono y bloquearía el bucle de eventos.\n\n"
        "Si el modelo aún no se ha entrenado, responde `disponible: false` con "
        "el motivo en lugar de devolver un número inventado."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def precio_sugerido(
    request: Request,
    obra_id: int | None = Query(
        default=None, ge=1, description="Derivar las variables de esta obra del catálogo."
    ),
    anio: int | None = Query(
        default=None, ge=1400, le=2100, description="Año de creación, si la obra aún no existe."
    ),
    tecnica: str | None = Query(
        default=None, min_length=2, max_length=80, description="Técnica empleada."
    ),
    db: AsyncSession = Depends(get_db),
):
    if obra_id is not None:
        # Las variables salen de los datos propios, no de lo que envíe nadie.
        obra = await obra_crud.get_by_id(db, obra_id)
        anio, tecnica = obra.anio, obra.tecnica
    elif anio is None or tecnica is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Indica `obra_id`, o bien `anio` y `tecnica` juntos.",
        )

    modelo = getattr(request.app.state, "ai_local_model", None)
    # La inferencia es cálculo síncrono: se aparta a un hilo para no bloquear.
    return await run_in_threadpool(ai_local.predecir_precio, modelo, anio, tecnica)


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
):
    return await ai_external.generar_descripcion_sugerida(titulo, tecnica)
