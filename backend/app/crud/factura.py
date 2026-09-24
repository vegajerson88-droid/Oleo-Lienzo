"""Emisión y consulta de facturas de venta.

La factura congela los datos del cliente y los importes en el momento de
emitirse: si luego cambian el perfil del cliente o el catálogo, el documento
ya emitido no se altera.
"""
from datetime import date, datetime, time, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.crud.base import contar, paginar
from app.crud.venta import get_by_id as get_venta_by_id
from app.models.detalle_venta import DetalleVenta
from app.models.factura import TRANSICIONES_FACTURA, EstadoFactura, Factura
from app.models.usuario import Usuario
from app.models.venta import EstadoVenta, Venta

settings = get_settings()

_RELACIONES = (
    selectinload(Factura.venta).selectinload(Venta.detalles).selectinload(DetalleVenta.obra),
    selectinload(Factura.venta).selectinload(Venta.detalles).selectinload(DetalleVenta.servicio),
)


def _numero_factura(factura_id: int) -> str:
    return f"{settings.factura_prefijo}-{factura_id:06d}"


async def get_by_id(db: AsyncSession, factura_id: int) -> Factura:
    query = select(Factura).where(Factura.id == factura_id).options(*_RELACIONES)
    factura = (await db.execute(query)).unique().scalar_one_or_none()
    if not factura:
        raise NotFoundError(f"Factura {factura_id} no encontrada.")
    return factura


async def emitir_factura(
    db: AsyncSession, venta_id: int, observaciones: str | None = None
) -> Factura:
    """Emite la factura de una venta. Una venta solo puede facturarse una vez."""
    venta = await get_venta_by_id(db, venta_id)

    if venta.factura is not None:
        raise ConflictError(
            f"La venta {venta.numero} ya tiene la factura {venta.factura.numero}."
        )
    if venta.estado == EstadoVenta.anulada:
        raise BusinessRuleError("No se puede facturar una venta anulada.")

    cliente = await db.get(Usuario, venta.cliente_id)
    if not cliente:
        raise NotFoundError(f"El cliente {venta.cliente_id} de la venta no existe.")

    factura = Factura(
        numero="",  # se asigna tras el flush
        venta_id=venta.id,
        cliente_id=cliente.id,
        estado=(
            EstadoFactura.pagada
            if venta.estado == EstadoVenta.pagada
            else EstadoFactura.emitida
        ),
        fecha_emision=datetime.now(timezone.utc),
        cliente_nombre=f"{cliente.nombre} {cliente.apellido}",
        cliente_documento=f"{cliente.tipo_documento} {cliente.numero_documento}",
        cliente_email=cliente.email,
        cliente_direccion=cliente.direccion,
        cliente_telefono=cliente.telefono,
        subtotal=venta.subtotal,
        descuento=venta.descuento,
        impuestos=venta.impuestos,
        iva_porcentaje=settings.iva_porcentaje,
        total=venta.total,
        observaciones=observaciones,
    )
    db.add(factura)
    await db.flush()
    factura.numero = _numero_factura(factura.id)
    await db.commit()
    return await get_by_id(db, factura.id)


async def list_facturas(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    numero: str | None = None,
    cliente_id: int | None = None,
    estado: EstadoFactura | None = None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    buscar: str | None = None,
) -> tuple[list[Factura], int]:
    """Consulta de facturas por número, cliente, estado o rango de fechas."""
    query = select(Factura).options(*_RELACIONES)
    if numero:
        query = query.where(Factura.numero.ilike(f"%{numero}%"))
    if cliente_id:
        query = query.where(Factura.cliente_id == cliente_id)
    if estado:
        query = query.where(Factura.estado == estado)
    if fecha_inicio:
        query = query.where(
            Factura.fecha_emision
            >= datetime.combine(fecha_inicio, time.min, tzinfo=timezone.utc)
        )
    if fecha_fin:
        query = query.where(
            Factura.fecha_emision
            <= datetime.combine(fecha_fin, time.max, tzinfo=timezone.utc)
        )
    if buscar:
        patron = f"%{buscar}%"
        query = query.where(
            or_(
                Factura.numero.ilike(patron),
                Factura.cliente_nombre.ilike(patron),
                Factura.cliente_documento.ilike(patron),
            )
        )

    total = await contar(db, query)
    query = paginar(query.order_by(Factura.fecha_emision.desc(), Factura.id.desc()), page, page_size)
    return list((await db.execute(query)).unique().scalars().all()), total


async def cambiar_estado(
    db: AsyncSession, factura_id: int, nuevo_estado: EstadoFactura
) -> Factura:
    factura = await get_by_id(db, factura_id)
    permitidos = TRANSICIONES_FACTURA.get(factura.estado, set())
    if nuevo_estado not in permitidos:
        raise BusinessRuleError(
            f"No se puede pasar de '{factura.estado.value}' a '{nuevo_estado.value}'. "
            f"Transiciones válidas desde '{factura.estado.value}': "
            f"{sorted(e.value for e in permitidos) or 'ninguna'}."
        )
    factura.estado = nuevo_estado
    await db.commit()
    return await get_by_id(db, factura_id)
