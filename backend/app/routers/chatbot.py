"""Chatbot de atención al cliente con Inteligencia Artificial."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import chat as chat_crud
from app.database import get_db
from app.dependencies.auth import get_current_user_opcional, solo_admin
from app.dependencies.common import RESPUESTA_404, RESPUESTA_422, RESPUESTAS_AUTH, IdPath
from app.dependencies.pagination import PaginationParams, pagination_params
from app.models.chat import RolMensaje
from app.models.usuario import Usuario
from app.schemas.chat import ChatRequest, ChatResponse, ConversacionOut
from app.schemas.common import Page
from app.services import chatbot as chatbot_service

router = APIRouter(prefix="/chatbot", tags=["Chatbot IA"])


@router.post(
    "/mensaje",
    response_model=ChatResponse,
    summary="Conversar con el asistente",
    description=(
        "Envía un mensaje al chatbot y devuelve su respuesta.\n\n"
        "**Cómo funciona.** El backend arma el contexto con el catálogo real "
        "de obras y servicios de la base de datos y los últimos mensajes de la "
        "conversación, y se lo pasa al modelo de **Groq**. La clave de API se "
        "lee de `GROQ_API_KEY` y nunca llega al navegador.\n\n"
        "**Qué resuelve.** Preguntas frecuentes, orientación sobre obras y "
        "servicios, guía del proceso de compra y radicación de PQR.\n\n"
        "**Si la IA no está disponible** (sin clave, tiempo agotado o error "
        "del proveedor), responde un modo local basado en reglas y lo declara "
        "en `generado_por_ia: false` junto con el motivo en `detalle`. Nunca "
        "finge que contestó la IA.\n\n"
        "No requiere iniciar sesión; si hay sesión, la conversación queda "
        "asociada al usuario."
    ),
    responses=RESPUESTA_422,
)
async def enviar_mensaje(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario | None = Depends(get_current_user_opcional),
):
    conversacion = await chat_crud.obtener_o_crear_conversacion(
        db, data.session_id, usuario.id if usuario else None
    )
    historial = await chat_crud.historial_reciente(db, conversacion.id)
    catalogo = await chatbot_service.construir_contexto_catalogo(db)

    await chat_crud.agregar_mensaje(db, conversacion, RolMensaje.usuario, data.mensaje)
    resultado = await chatbot_service.generar_respuesta(data.mensaje, historial, catalogo)
    await chat_crud.agregar_mensaje(db, conversacion, RolMensaje.asistente, resultado["respuesta"])

    return ChatResponse(conversacion_id=conversacion.id, **resultado)


@router.get(
    "/conversaciones",
    response_model=Page[ConversacionOut],
    summary="Listar conversaciones (auditoría)",
    description=(
        "Permite al administrador revisar qué se le ha preguntado al asistente y qué respondió."
    ),
    responses=RESPUESTAS_AUTH,
)
async def listar_conversaciones(
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(solo_admin),
):
    items, total = await chat_crud.list_conversaciones(
        db, page=pagination.page, page_size=pagination.page_size
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get(
    "/conversaciones/{conversacion_id}",
    response_model=ConversacionOut,
    summary="Consultar una conversación completa",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404},
)
async def obtener_conversacion(
    conversacion_id: IdPath,
    db: AsyncSession = Depends(get_db),
    _admin: Usuario = Depends(solo_admin),
):
    try:
        return await chat_crud.get_conversacion(db, conversacion_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
