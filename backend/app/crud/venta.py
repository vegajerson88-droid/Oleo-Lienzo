"""Lógica de negocio y persistencia del módulo de ventas.

Una venta nace de dos formas:
  * `crear_venta` — registro manual desde el panel (venta presencial);
  * `crear_venta_desde_pedido` — automática, al confirmarse un pedido web.

En ambos casos se recalculan los importes del lado del servidor a partir de
los precios vigentes en la base de datos. Nunca se confía en el total que
envíe el cliente.
"""
from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.dinero import a_decimal, calcular_linea, calcular_totales
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.crud.base import contar, paginar
from app.models.detalle_venta import DetalleVenta
from app.models.obra import Obra
from app.models.servicio import Servicio
from app.models.venta import TRANSICIONES_VENTA, EstadoVenta, MetodoPago, Venta
from app.schemas.venta import DetalleVentaCreate, VentaCreate, VentaFiltros

settings = get_settings()

_RELACIONES = (
    selectinload(Venta.detalles).selectinload(DetalleVenta.obra),
    selectinload(Venta.detalles).selectinload(DetalleVenta.servicio),
    selectinload(Venta.factura),
    selectinload(Venta.pagos),
)


def _numero_venta(venta_id: int, momento: datetime) -> str:
    return f"V-{momento.year}-{venta_id:06d}"


async def get_by_id(db: AsyncSession, venta_id: int) -> Venta:
    query = select(Venta).where(Venta.id == venta_id).options(*_RELACIONES)
    venta = (await db.execute(query)).unique().scalar_one_or_none()
    if not venta:
        raise NotFoundError(f"Venta {venta_id} no encontrada.")
    return venta


async def _resolver_linea(
    db: AsyncSession, item: DetalleVentaCreate
) -> tuple[DetalleVenta, Obra | None]:
    """Convierte una línea solicitada en una línea de venta con precio real."""
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
        descuento = a_decimal(getattr(item, "descuento", 0))
        if descuento > precio * item.cantidad:
            raise BusinessRuleError(
                f"El descuento de '{obra.titulo}' supera el valor de la línea."
            )
        linea = DetalleVenta(
            obra_id=obra.id,
            descripcion=f"{obra.titulo} — {obra.artista}",
            cantidad=item.cantidad,
            precio_unitario=precio,
            descuento=descuento,
            subtotal=calcular_linea(precio, item.cantidad, descuento),
        )
        return linea, obra

    servicio = await db.get(Servicio, item.servicio_id)
    if not servicio:
        raise NotFoundError(f"Servicio {item.servicio_id} no encontrado.")
    if not servicio.activo:
        raise BusinessRuleError(f"El servicio '{servicio.nombre}' no está activo.")
    precio = a_decimal(servicio.precio)
    descuento = a_decimal(getattr(item, "descuento", 0))
    if descuento > precio * item.cantidad:
        raise BusinessRuleError(
            f"El descuento de '{servicio.nombre}' supera el valor de la línea."
        )
    linea = DetalleVenta(
        servicio_id=servicio.id,
        descripcion=servicio.nombre,
        cantidad=item.cantidad,
        precio_unitario=precio,
        descuento=descuento,
        subtotal=calcular_linea(precio, item.cantidad, descuento),
    )
    return linea, None


async def _armar_venta(
    db: AsyncSession,
    cliente_id: int,
    detalles: list[DetalleVentaCreate],
    descuento_global,
    metodo_pago: MetodoPago,
    observaciones: str | None,
    usuario_id: int | None,
    pedido_id: int | None,
) -> Venta:
    lineas: list[DetalleVenta] = []
    obras_a_descontar: list[tuple[Obra, int]] = []

    for item in detalles:
        linea, obra = await _resolver_linea(db, item)
        lineas.append(linea)
        if obra is not None:
            obras_a_descontar.append((obra, item.cantidad))

    totales = calcular_totales(
        [l.subtotal for l in lineas], descuento_global, settings.iva_tasa
    )

    venta = Venta(
        numero="",  # se asigna tras el flush, cuando ya existe el id
        cliente_id=cliente_id,
        usuario_id=usuario_id,
        pedido_id=pedido_id,
        estado=EstadoVenta.pendiente_pago,
        metodo_pago=metodo_pago,
        subtotal=totales["subtotal"],
        descuento=totales["descuento"],
        impuestos=totales["impuestos"],
        total=totales["total"],
        observaciones=observaciones,
    )
    venta.detalles = lineas
    db.add(venta)
    await db.flush()
    venta.numero = _numero_venta(venta.id, datetime.now(timezone.utc))

    # Descontar inventario solo después de validar todas las líneas.
    for obra, cantidad in obras_a_descontar:
        obra.stock -= cantidad
        if obra.stock == 0:
            obra.disponible = False

    await db.commit()
    return await get_by_id(db, venta.id)


async def crear_venta(db: AsyncSession, data: VentaCreate, usuario_id: int | None) -> Venta:
    """Venta registrada manualmente por un administrador o empleado."""
    return await _armar_venta(
        db,
        cliente_id=data.cliente_id,
        detalles=data.detalles,
        descuento_global=data.descuento,
        metodo_pago=data.metodo_pago,
        observaciones=data.observaciones,
        usuario_id=usuario_id,
        pedido_id=None,
    )


async def construir_venta_desde_pedido(
    db: AsyncSession, pedido, usuario_id: int | None
) -> Venta:
    """Prepara la venta de un pedido confirmado **sin hacer commit**.

    La deja añadida a la sesión y con su consecutivo asignado, para que quien
    la llame confirme la transacción junto con el cambio de estado del pedido.
    Así, o se guardan ambas cosas o no se guarda ninguna.

    El stock ya se reservó al crear el pedido, así que aquí se copian las
    líneas tal cual en lugar de volver a descontarlo.
    """
    lineas = [
        DetalleVenta(
            obra_id=d.obra_id,
            servicio_id=d.servicio_id,
            descripcion=d.descripcion,
            cantidad=d.cantidad,
            precio_unitario=a_decimal(d.precio_unitario),
            descuento=Decimal("0.00"),
            subtotal=calcular_linea(d.precio_unitario, d.cantidad),
        )
        for d in pedido.detalles
    ]
    totales = calcular_totales([l.subtotal for l in lineas], 0, settings.iva_tasa)

    venta = Venta(
        numero="",
        cliente_id=pedido.cliente_id,
        usuario_id=usuario_id,
        pedido_id=pedido.id,
        estado=EstadoVenta.pendiente_pago,
        metodo_pago=MetodoPago.tarjeta,
        subtotal=totales["subtotal"],
        descuento=totales["descuento"],
        impuestos=totales["impuestos"],
        total=totales["total"],
        observaciones=f"Generada automáticamente desde el pedido #{pedido.id}.",
    )
    venta.detalles = lineas
    db.add(venta)
    await db.flush()
    venta.numero = _numero_venta(venta.id, datetime.now(timezone.utc))
    return venta


def _aplicar_filtros(query: Select, f: VentaFiltros) -> Select:
    if f.fecha_inicio:
        query = query.where(
            Venta.creado_en >= datetime.combine(f.fecha_inicio, time.min, tzinfo=timezone.utc)
        )
    if f.fecha_fin:
        query = query.where(
            Venta.creado_en <= datetime.combine(f.fecha_fin, time.max, tzinfo=timezone.utc)
        )
    if f.cliente_id:
        query = query.where(Venta.cliente_id == f.cliente_id)
    if f.estado:
        query = query.where(Venta.estado == f.estado)
    if f.total_min is not None:
        query = query.where(Venta.total >= f.total_min)
    if f.total_max is not None:
        query = query.where(Venta.total <= f.total_max)
    if f.obra_id or f.servicio_id:
        sub = select(DetalleVenta.venta_id)
        if f.obra_id:
            sub = sub.where(DetalleVenta.obra_id == f.obra_id)
        if f.servicio_id:
            sub = sub.where(DetalleVenta.servicio_id == f.servicio_id)
        query = query.where(Venta.id.in_(sub))
    return query


async def list_ventas(
    db: AsyncSession, filtros: VentaFiltros, page: int = 1, page_size: int = 10
) -> tuple[list[Venta], int]:
    """Historial de ventas con todos los criterios del quinto avance."""
    query = _aplicar_filtros(select(Venta).options(*_RELACIONES), filtros)
    total = await contar(db, query)
    query = paginar(query.order_by(Venta.creado_en.desc(), Venta.id.desc()), page, page_size)
    return list((await db.execute(query)).unique().scalars().all()), total


async def ventas_del_dia(db: AsyncSession, dia: date) -> list[Venta]:
    """Todas las ventas de una fecha, para el reporte diario."""
    filtros = VentaFiltros(fecha_inicio=dia, fecha_fin=dia)
    query = _aplicar_filtros(select(Venta).options(*_RELACIONES), filtros)
    return list(
        (await db.execute(query.order_by(Venta.creado_en))).unique().scalars().all()
    )


async def cambiar_estado(db: AsyncSession, venta_id: int, nuevo_estado: EstadoVenta) -> Venta:
    """Transición de estado de la venta, validada contra la máquina de estados."""
    venta = await get_by_id(db, venta_id)
    permitidos = TRANSICIONES_VENTA.get(venta.estado, set())
    if nuevo_estado not in permitidos:
        raise BusinessRuleError(
            f"No se puede pasar de '{venta.estado.value}' a '{nuevo_estado.value}'. "
            f"Transiciones válidas desde '{venta.estado.value}': "
            f"{sorted(e.value for e in permitidos) or 'ninguna'}."
        )

    # Anular o reembolsar devuelve las obras al inventario.
    if nuevo_estado in (EstadoVenta.anulada, EstadoVenta.reembolsada):
        for linea in venta.detalles:
            if linea.obra_id and linea.obra:
                linea.obra.stock += linea.cantidad
                linea.obra.disponible = True

    venta.estado = nuevo_estado
    await db.commit()
    return await get_by_id(db, venta_id)


async def marcar_pagada_por_referencia(db: AsyncSession, venta_id: int) -> Venta | None:
    """Marca la venta como pagada si aún estaba pendiente (idempotente).

    La llama el webhook de Stripe, que puede reintentarse varias veces para el
    mismo evento.
    """
    venta = await get_by_id(db, venta_id)
    if venta.estado != EstadoVenta.pendiente_pago:
        return venta
    venta.estado = EstadoVenta.pagada
    await db.commit()
    return await get_by_id(db, venta_id)
