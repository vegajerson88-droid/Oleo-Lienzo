"""Módulo de PQR: peticiones, quejas, reclamos y sugerencias."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import pqr as pqr_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado, get_current_user, get_current_user_opcional
from app.dependencies.common import (
    RESPUESTA_404,
    RESPUESTA_422,
    RESPUESTAS_AUTH,
    BuscarQuery,
    IdPath,
)
from app.dependencies.pagination import PaginationParams, pagination_params
from app.models.pqr import EstadoPQR, TipoPQR
from app.models.usuario import Usuario
from app.schemas.common import Page
from app.schemas.pqr import PQRCambioEstado, PQRCreate, PQROut, PQRResponder
from app.services import email as email_service

router = APIRouter(prefix="/pqr", tags=["PQR"])


@router.post(
    "",
    response_model=PQROut,
    status_code=status.HTTP_201_CREATED,
    summary="Radicar una PQR",
    description=(
        "Radica una petición, queja, reclamo o sugerencia y devuelve un "
        "**número de radicado** (`PQR-NNNNNN`) para hacer seguimiento.\n\n"
        "Funciona con y sin sesión iniciada: con sesión toma los datos del "
        "usuario; sin ella hay que enviar `contacto_nombre` y "
        "`contacto_email` (es la vía que usa el chatbot con visitantes).\n\n"
        "El acuse de recibo se envía por correo en segundo plano."
    ),
    responses=RESPUESTA_422,
)
async def radicar_pqr(
    data: PQRCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario | None = Depends(get_current_user_opcional),
):
    try:
        pqr = await pqr_crud.crear_pqr(db, data, usuario)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    background_tasks.add_task(email_service.enviar_pqr_radicada, pqr)
    return pqr


@router.get(
    "",
    response_model=Page[PQROut],
    summary="Listar PQR",
    description=(
        "Un **cliente** solo ve las PQR que él radicó; administrador y "
        "empleado las ven todas. Admite filtrar por estado y tipo, y buscar "
        "por radicado, asunto o correo."
    ),
    responses=RESPUESTAS_AUTH,
)
async def listar_pqr(
    estado: EstadoPQR | None = Query(default=None),
    tipo: TipoPQR | None = Query(default=None),
    buscar: BuscarQuery = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    cliente_id = usuario.id if usuario.rol.nombre == "cliente" else None
    items, total = await pqr_crud.list_pqr(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        cliente_id=cliente_id,
        estado=estado,
        tipo=tipo,
        buscar=buscar,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get(
    "/{pqr_id}",
    response_model=PQROut,
    summary="Consultar una PQR",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404},
)
async def obtener_pqr(
    pqr_id: IdPath,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        pqr = await pqr_crud.get_by_id(db, pqr_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    if usuario.rol.nombre == "cliente" and pqr.cliente_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Esta PQR no es tuya."
        )
    return pqr


@router.post(
    "/{pqr_id}/responder",
    response_model=PQROut,
    summary="Responder una PQR",
    description=(
        "Guarda la respuesta, registra quién y cuándo respondió, y pasa la PQR "
        "a estado `respondida`. Notifica al cliente por correo en segundo "
        "plano. Una PQR cerrada no se puede responder (422)."
    ),
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_422},
)
async def responder_pqr(
    pqr_id: IdPath,
    data: PQRResponder,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(admin_o_empleado),
):
    try:
        pqr = await pqr_crud.responder(db, pqr_id, data.respuesta, usuario.id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    background_tasks.add_task(email_service.enviar_pqr_respondida, pqr)
    return pqr


@router.patch(
    "/{pqr_id}/estado",
    response_model=PQROut,
    summary="Cambiar el estado de una PQR",
    description=(
        "Transiciones permitidas:\n\n"
        "```\n"
        "pendiente  → en_proceso | respondida | cerrada\n"
        "en_proceso → respondida | cerrada\n"
        "respondida → cerrada    | en_proceso   (si el cliente no queda conforme)\n"
        "cerrada    → (final)\n"
        "```\n\n"
        "No se puede marcar como `respondida` una PQR que todavía no tiene "
        "respuesta escrita."
    ),
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_422},
)
async def cambiar_estado_pqr(
    pqr_id: IdPath,
    data: PQRCambioEstado,
    db: AsyncSession = Depends(get_db),
    _u: Usuario = Depends(admin_o_empleado),
):
    try:
        return await pqr_crud.cambiar_estado(db, pqr_id, data.nuevo_estado)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
