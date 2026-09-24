from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.crud.obra import get_by_id as get_obra_by_id
from app.models.detalle_pedido import DetallePedido
from app.models.pedido import TRANSICIONES_VALIDAS, EstadoPedido, Pedido
from app.schemas.pedido import PedidoCreate


async def get_by_id(db: AsyncSession, pedido_id: int) -> Pedido:
    query = select(Pedido).where(Pedido.id == pedido_id).options(selectinload(Pedido.detalles))
    result = await db.execute(query)
    pedido = result.scalar_one_or_none()
    if not pedido:
        raise NotFoundError(f"Pedido {pedido_id} no encontrado.")
    return pedido


async def list_pedidos(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    cliente_id: int | None = None,
    estado: EstadoPedido | None = None,
) -> tuple[list[Pedido], int]:
    query = select(Pedido).options(selectinload(Pedido.detalles))
    if cliente_id is not None:
        query = query.where(Pedido.cliente_id == cliente_id)
    if estado is not None:
        query = query.where(Pedido.estado == estado)

    total = len((await db.execute(query)).scalars().all())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_pedido(db: AsyncSession, cliente_id: int, data: PedidoCreate) -> Pedido:
    pedido = Pedido(cliente_id=cliente_id, estado=EstadoPedido.pendiente, total=0)
    total = 0.0
    for item in data.detalles:
        obra = await get_obra_by_id(db, item.obra_id)
        if not obra.disponible:
            raise BusinessRuleError(f"La obra '{obra.titulo}' no está disponible.")
        precio = float(obra.precio)
        total += precio * item.cantidad
        pedido.detalles.append(
            DetallePedido(obra_id=obra.id, cantidad=item.cantidad, precio_unitario=precio)
        )
    pedido.total = total
    db.add(pedido)
    await db.commit()
    await db.refresh(pedido, attribute_names=["detalles", "cliente"])
    return pedido


async def cambiar_estado(db: AsyncSession, pedido_id: int, nuevo_estado: EstadoPedido) -> Pedido:
    """Operación de negocio no-CRUD: transición de estado del pedido.

    pendiente -> confirmado -> entregado, con posibilidad de cancelar
    desde pendiente o confirmado. No se permite ninguna otra transición.
    """
    pedido = await get_by_id(db, pedido_id)
    permitidos = TRANSICIONES_VALIDAS.get(pedido.estado, set())
    if nuevo_estado not in permitidos:
        raise BusinessRuleError(
            f"No se puede pasar de '{pedido.estado.value}' a '{nuevo_estado.value}'. "
            f"Transiciones válidas desde '{pedido.estado.value}': "
            f"{sorted(e.value for e in permitidos) or 'ninguna'}."
        )
    pedido.estado = nuevo_estado
    await db.commit()
    await db.refresh(pedido, attribute_names=["detalles", "cliente"])
    return pedido
