"""Pedidos: la orden que el cliente arma desde el sitio web."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import pedido as pedido_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado, get_current_user, solo_cliente
from app.dependencies.common import RESPUESTA_404, RESPUESTA_422, RESPUESTAS_AUTH, IdPath
from app.dependencies.pagination import PaginationParams, pagination_params
from app.models.pedido import EstadoPedido
from app.models.usuario import Usuario
from app.schemas.common import Page
from app.schemas.pedido import PedidoCambioEstado, PedidoCreate, PedidoOut
from app.services import email as email_service

router = APIRouter(prefix="/pedidos", tags=["Pedidos"], responses=RESPUESTAS_AUTH)


@router.get(
    "",
    response_model=Page[PedidoOut],
    summary="Listar pedidos",
    description=(
        "El alcance depende del rol: un **cliente** solo ve sus propios "
        "pedidos; **administrador** y **empleado** los ven todos. El filtro "
        "lo impone el backend, no el frontend."
    ),
)
async def listar_pedidos(
    estado: EstadoPedido | None = Query(default=None, description="Filtra por estado."),
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    cliente_id = usuario.id if usuario.rol.nombre == "cliente" else None
    items, total = await pedido_crud.list_pedidos(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        cliente_id=cliente_id,
        estado=estado,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get(
    "/{pedido_id}",
    response_model=PedidoOut,
    summary="Consultar un pedido",
    description="Un cliente que pida un pedido ajeno recibe un 403.",
    responses=RESPUESTA_404,
)
async def obtener_pedido(
    pedido_id: IdPath,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        pedido = await pedido_crud.get_by_id(db, pedido_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    if usuario.rol.nombre == "cliente" and pedido.cliente_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este pedido no es tuyo.")
    return pedido


@router.post(
    "",
    response_model=PedidoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un pedido",
    description=(
        "Solo el rol **cliente**. Cada línea puede ser una obra o un servicio.\n\n"
        "El backend valida la disponibilidad y el stock, calcula el total con "
        "los precios vigentes en la base de datos (nunca con los que envíe el "
        "cliente) y **reserva el inventario**. Si alguna línea falla, no se "
        "reserva nada."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def crear_pedido(
    data: PedidoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(solo_cliente),
):
    try:
        return await pedido_crud.create_pedido(db, usuario.id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch(
    "/{pedido_id}/estado",
    response_model=PedidoOut,
    summary="Cambiar el estado de un pedido",
    description=(
        "Operación de negocio, no un CRUD: la transición se valida contra una "
        "máquina de estados.\n\n"
        "```\n"
        "pendiente  → confirmado | cancelado\n"
        "confirmado → entregado  | cancelado\n"
        "entregado  → (final)\n"
        "cancelado  → (final)\n"
        "```\n\n"
        "**Confirmar genera automáticamente la venta** correspondiente. "
        "**Cancelar devuelve el inventario** reservado. Cualquier otra "
        "transición se rechaza con 422.\n\n"
        "El aviso por correo al cliente se envía en segundo plano."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def cambiar_estado_pedido(
    pedido_id: IdPath,
    data: PedidoCambioEstado,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(admin_o_empleado),
):
    try:
        pedido, venta = await pedido_crud.cambiar_estado(
            db, pedido_id, data.nuevo_estado, usuario.id
        )
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    # Tareas no bloqueantes: la respuesta no espera a que salgan los correos.
    if pedido.cliente:
        background_tasks.add_task(
            email_service.enviar_cambio_estado_pedido,
            pedido.cliente.nombre,
            pedido.cliente.email,
            pedido.id,
            pedido.estado.value,
        )
    if venta is not None:
        background_tasks.add_task(email_service.enviar_confirmacion_compra, venta, None)
    return pedido
