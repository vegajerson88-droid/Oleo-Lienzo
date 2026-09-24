"""Lógica de negocio y persistencia de los pedidos del sitio web."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dinero import a_decimal, calcular_linea
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.crud.base import contar, paginar
from app.crud.venta import construir_venta_desde_pedido
from app.crud.venta import get_by_id as get_venta_by_id
from app.models.detalle_pedido import DetallePedido
from app.models.obra import Obra
from app.models.pedido import TRANSICIONES_VALIDAS, EstadoPedido, Pedido
from app.models.servicio import Servicio
from app.schemas.pedido import PedidoCreate

_RELACIONES = (
    selectinload(Pedido.detalles).selectinload(DetallePedido.obra),
    selectinload(Pedido.detalles).selectinload(DetallePedido.servicio),
    # `venta` se carga por adelantado: al confirmar hay que comprobar si el
    # pedido ya generó una, y una carga diferida aquí fallaría en async.
    selectinload(Pedido.venta),
)


async def get_by_id(db: AsyncSession, pedido_id: int) -> Pedido:
    query = select(Pedido).where(Pedido.id == pedido_id).options(*_RELACIONES)
    pedido = (await db.execute(query)).unique().scalar_one_or_none()
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
    query = select(Pedido).options(*_RELACIONES)
    if cliente_id is not None:
        query = query.where(Pedido.cliente_id == cliente_id)
    if estado is not None:
        query = query.where(Pedido.estado == estado)
    total = await contar(db, query)
    query = paginar(query.order_by(Pedido.id.desc()), page, page_size)
    return list((await db.execute(query)).unique().scalars().all()), total


async def create_pedido(db: AsyncSession, cliente_id: int, data: PedidoCreate) -> Pedido:
    """Crea el pedido y reserva el inventario de las obras incluidas."""
    pedido = Pedido(cliente_id=cliente_id, estado=EstadoPedido.pendiente, total=0)
    total = a_decimal(0)
    reservas: list[tuple[Obra, int]] = []

    for item in data.detalles:
        if item.obra_id:
            obra = await db.get(Obra, item.obra_id)
            if not obra:
                raise NotFoundError(f"Obra {item.obra_id} no encontrada.")
            if not obra.disponible:
                raise BusinessRuleError(f"La obra '{obra.titulo}' no está disponible.")
            if obra.stock < item.cantidad:
                raise BusinessRuleError(
                    f"Stock insuficiente de '{obra.titulo}': "
                    f"quedan {obra.stock} y se pidieron {item.cantidad}."
                )
            precio = a_decimal(obra.precio)
            pedido.detalles.append(
                DetallePedido(
                    obra_id=obra.id,
                    descripcion=f"{obra.titulo} — {obra.artista}",
                    cantidad=item.cantidad,
                    precio_unitario=precio,
                )
            )
            reservas.append((obra, item.cantidad))
        else:
            servicio = await db.get(Servicio, item.servicio_id)
            if not servicio:
                raise NotFoundError(f"Servicio {item.servicio_id} no encontrado.")
            if not servicio.activo:
                raise BusinessRuleError(f"El servicio '{servicio.nombre}' no está activo.")
            precio = a_decimal(servicio.precio)
            pedido.detalles.append(
                DetallePedido(
                    servicio_id=servicio.id,
                    descripcion=servicio.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=precio,
                )
            )
        total += calcular_linea(precio, item.cantidad)

    pedido.total = total
    db.add(pedido)

    # El inventario se reserva solo cuando todas las líneas son válidas.
    for obra, cantidad in reservas:
        obra.stock -= cantidad
        if obra.stock == 0:
            obra.disponible = False

    await db.commit()
    return await get_by_id(db, pedido.id)


async def cambiar_estado(
    db: AsyncSession,
    pedido_id: int,
    nuevo_estado: EstadoPedido,
    usuario_id: int | None = None,
):
    """Transición de estado del pedido.

    pendiente → confirmado → entregado, con cancelación posible desde
    pendiente o confirmado. Confirmar genera automáticamente la venta;
    cancelar devuelve el inventario reservado.

    Devuelve la tupla (pedido, venta_generada_o_None).
    """
    pedido = await get_by_id(db, pedido_id)
    permitidos = TRANSICIONES_VALIDAS.get(pedido.estado, set())
    if nuevo_estado not in permitidos:
        raise BusinessRuleError(
            f"No se puede pasar de '{pedido.estado.value}' a '{nuevo_estado.value}'. "
            f"Transiciones válidas desde '{pedido.estado.value}': "
            f"{sorted(e.value for e in permitidos) or 'ninguna'}."
        )

    if nuevo_estado == EstadoPedido.cancelado:
        for linea in pedido.detalles:
            if linea.obra_id and linea.obra:
                linea.obra.stock += linea.cantidad
                linea.obra.disponible = True

    pedido.estado = nuevo_estado

    # El cambio de estado y la venta que genera viajan en la MISMA
    # transacción: si algo falla, el pedido no queda confirmado a medias.
    venta = None
    if nuevo_estado == EstadoPedido.confirmado and pedido.venta is None:
        venta = await construir_venta_desde_pedido(db, pedido, usuario_id)

    await db.commit()

    venta_completa = await get_venta_by_id(db, venta.id) if venta else None
    return await get_by_id(db, pedido_id), venta_completa
