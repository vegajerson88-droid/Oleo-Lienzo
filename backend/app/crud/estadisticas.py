"""Agregaciones que alimentan los dashboards.

Todos los indicadores y series salen de consultas SQL con GROUP BY; el
frontend nunca calcula ni inventa un número (requisito 15 del quinto avance).

Las consultas aceptan los criterios de `FiltrosDashboard`: fecha inicial,
fecha final, producto, servicio, estado y cliente (requisito 13).

`func.date()` se usa para agrupar por día porque es la única expresión que
funciona igual en PostgreSQL y en SQLite (el CAST a DATE no lo es).
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detalle_venta import DetalleVenta
from app.models.factura import Factura
from app.models.obra import Obra
from app.models.pedido import Pedido
from app.models.pqr import PQR, EstadoPQR
from app.models.servicio import Servicio
from app.models.usuario import Usuario
from app.models.venta import EstadoVenta, Venta

# Estados que cuentan como ingreso real.
VENTAS_EFECTIVAS = (EstadoVenta.pagada, EstadoVenta.pendiente_pago)


@dataclass(frozen=True)
class FiltrosDashboard:
    """Criterios de filtrado del dashboard (requisito 13 del quinto avance)."""

    desde: date | None = None
    hasta: date | None = None
    cliente_id: int | None = None
    obra_id: int | None = None
    servicio_id: int | None = None
    estado: EstadoVenta | None = None

    @property
    def estados_efectivos(self) -> tuple[EstadoVenta, ...]:
        """El estado pedido, o los que cuentan como venta real si no se pide ninguno."""
        return (self.estado,) if self.estado else VENTAS_EFECTIVAS


SIN_FILTROS = FiltrosDashboard()


def _inicio(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def _fin(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=timezone.utc)


def _en_rango(query: Select, columna, desde: date | None, hasta: date | None) -> Select:
    if desde:
        query = query.where(columna >= _inicio(desde))
    if hasta:
        query = query.where(columna <= _fin(hasta))
    return query


def _ventas_con_linea(f: FiltrosDashboard) -> Select | None:
    """IDs de las ventas que incluyen la obra o el servicio filtrados.

    Se resuelve como subconsulta en lugar de con un JOIN: unir el detalle
    multiplicaría la venta por sus líneas y descuadraría cualquier SUM.
    """
    if not (f.obra_id or f.servicio_id):
        return None
    lineas = select(DetalleVenta.venta_id)
    if f.obra_id:
        lineas = lineas.where(DetalleVenta.obra_id == f.obra_id)
    if f.servicio_id:
        lineas = lineas.where(DetalleVenta.servicio_id == f.servicio_id)
    return lineas


def _filtrar_ventas(query: Select, f: FiltrosDashboard) -> Select:
    """Aplica fecha, cliente, obra y servicio a una consulta sobre `ventas`."""
    query = _en_rango(query, Venta.creado_en, f.desde, f.hasta)
    if f.cliente_id:
        query = query.where(Venta.cliente_id == f.cliente_id)
    lineas = _ventas_con_linea(f)
    if lineas is not None:
        query = query.where(Venta.id.in_(lineas))
    return query


def _filtrar_facturas(query: Select, f: FiltrosDashboard) -> Select:
    """Los mismos criterios, aplicados a `facturas` a través de su venta."""
    query = _en_rango(query, Factura.fecha_emision, f.desde, f.hasta)
    if f.cliente_id:
        query = query.where(Factura.cliente_id == f.cliente_id)
    lineas = _ventas_con_linea(f)
    if lineas is not None:
        query = query.where(Factura.venta_id.in_(lineas))
    if f.estado:
        query = query.where(Factura.venta_id.in_(select(Venta.id).where(Venta.estado == f.estado)))
    return query


def _a_etiqueta_fecha(valor) -> str:
    """Normaliza el resultado de func.date(): PostgreSQL devuelve date, SQLite str."""
    return valor.isoformat() if isinstance(valor, (date, datetime)) else str(valor)


async def _escalar(db: AsyncSession, query: Select, por_defecto=0):
    resultado = (await db.execute(query)).scalar()
    return resultado if resultado is not None else por_defecto


async def indicadores_admin(db: AsyncSession, f: FiltrosDashboard = SIN_FILTROS) -> dict:
    """Panorama completo del sistema para el rol administrador."""
    ventas_q = _filtrar_ventas(select(Venta).where(Venta.estado.in_(f.estados_efectivos)), f)
    facturado_q = _filtrar_facturas(select(func.coalesce(func.sum(Factura.total), 0)), f)
    facturas_q = _filtrar_facturas(select(Factura), f)
    ingresos_q = _filtrar_ventas(
        select(func.coalesce(func.sum(Venta.total), 0)).where(
            Venta.estado == EstadoVenta.pagada,
            Venta.estado.in_(f.estados_efectivos),
        ),
        f,
    )
    pedidos_q = _en_rango(select(Pedido), Pedido.creado_en, f.desde, f.hasta)
    if f.cliente_id:
        pedidos_q = pedidos_q.where(Pedido.cliente_id == f.cliente_id)

    return {
        "total_usuarios": await _escalar(db, select(func.count()).select_from(Usuario)),
        "usuarios_activos": await _escalar(
            db, select(func.count()).select_from(Usuario).where(Usuario.activo.is_(True))
        ),
        "total_obras": await _escalar(db, select(func.count()).select_from(Obra)),
        "obras_disponibles": await _escalar(
            db, select(func.count()).select_from(Obra).where(Obra.disponible.is_(True))
        ),
        "total_servicios": await _escalar(
            db, select(func.count()).select_from(Servicio).where(Servicio.activo.is_(True))
        ),
        "total_ventas": await _escalar(db, select(func.count()).select_from(ventas_q.subquery())),
        "ingresos": float(await _escalar(db, ingresos_q)),
        "total_facturado": float(await _escalar(db, facturado_q)),
        "total_facturas": await _escalar(
            db, select(func.count()).select_from(facturas_q.subquery())
        ),
        "pqr_recibidas": await _escalar(db, select(func.count()).select_from(PQR)),
        "pqr_pendientes": await _escalar(
            db,
            select(func.count())
            .select_from(PQR)
            .where(PQR.estado.in_((EstadoPQR.pendiente, EstadoPQR.en_proceso))),
        ),
        "total_pedidos": await _escalar(db, select(func.count()).select_from(pedidos_q.subquery())),
    }


async def indicadores_empleado(db: AsyncSession, f: FiltrosDashboard = SIN_FILTROS) -> dict:
    """Subconjunto operativo: el empleado no ve usuarios ni facturación global."""
    completo = await indicadores_admin(db, f)
    visibles = (
        "total_obras",
        "obras_disponibles",
        "total_servicios",
        "total_ventas",
        "total_pedidos",
        "pqr_pendientes",
    )
    return {k: completo[k] for k in visibles}


async def indicadores_cliente(
    db: AsyncSession, cliente_id: int, f: FiltrosDashboard = SIN_FILTROS
) -> dict:
    """Solo la información del propio cliente."""
    # El cliente nunca puede consultar datos de otro: su id manda sobre el filtro.
    propio = FiltrosDashboard(
        desde=f.desde,
        hasta=f.hasta,
        cliente_id=cliente_id,
        obra_id=f.obra_id,
        servicio_id=f.servicio_id,
        estado=f.estado,
    )
    mis_ventas = _filtrar_ventas(select(Venta), propio)
    if propio.estado:
        mis_ventas = mis_ventas.where(Venta.estado == propio.estado)
    invertido_q = _filtrar_ventas(
        select(func.coalesce(func.sum(Venta.total), 0)).where(Venta.estado == EstadoVenta.pagada),
        propio,
    )
    facturas_q = _filtrar_facturas(select(Factura), propio)

    return {
        "mis_pedidos": await _escalar(
            db, select(func.count()).select_from(Pedido).where(Pedido.cliente_id == cliente_id)
        ),
        "mis_compras": await _escalar(db, select(func.count()).select_from(mis_ventas.subquery())),
        "total_invertido": float(await _escalar(db, invertido_q)),
        "mis_facturas": await _escalar(db, select(func.count()).select_from(facturas_q.subquery())),
        "mis_pqr_abiertas": await _escalar(
            db,
            select(func.count())
            .select_from(PQR)
            .where(
                PQR.cliente_id == cliente_id,
                PQR.estado.in_((EstadoPQR.pendiente, EstadoPQR.en_proceso)),
            ),
        ),
    }


async def serie_ventas_por_dia(
    db: AsyncSession, f: FiltrosDashboard = SIN_FILTROS
) -> list[tuple[str, float]]:
    """Total vendido por día: alimenta el gráfico lineal."""
    dia = func.date(Venta.creado_en).label("dia")
    query = (
        select(dia, func.coalesce(func.sum(Venta.total), 0))
        .where(Venta.estado.in_(f.estados_efectivos))
        .group_by(dia)
        .order_by(dia)
    )
    filas = (await db.execute(_filtrar_ventas(query, f))).all()
    return [(_a_etiqueta_fecha(fila[0]), float(fila[1])) for fila in filas]


async def serie_ventas_por_estado(
    db: AsyncSession, f: FiltrosDashboard = SIN_FILTROS
) -> list[tuple[str, float]]:
    """Cuántas ventas hay en cada estado: gráfico de barras.

    Aquí no se filtra por los estados «efectivos»: el sentido del gráfico es
    precisamente mostrar el reparto entre todos ellos.
    """
    query = select(Venta.estado, func.count()).group_by(Venta.estado).order_by(Venta.estado)
    if f.estado:
        query = query.where(Venta.estado == f.estado)
    filas = (await db.execute(_filtrar_ventas(query, f))).all()
    return [
        (fila[0].value if hasattr(fila[0], "value") else str(fila[0]), float(fila[1]))
        for fila in filas
    ]


async def top_productos(
    db: AsyncSession, f: FiltrosDashboard = SIN_FILTROS, limite: int = 5
) -> list[tuple[str, float]]:
    """Obras y servicios más vendidos por importe: gráfico de barras."""
    query = (
        select(DetalleVenta.descripcion, func.coalesce(func.sum(DetalleVenta.subtotal), 0))
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .where(Venta.estado.in_(f.estados_efectivos))
        .group_by(DetalleVenta.descripcion)
        .order_by(func.coalesce(func.sum(DetalleVenta.subtotal), 0).desc())
        .limit(limite)
    )
    # Al agrupar por línea, el producto filtrado se aplica sobre el detalle.
    if f.obra_id:
        query = query.where(DetalleVenta.obra_id == f.obra_id)
    if f.servicio_id:
        query = query.where(DetalleVenta.servicio_id == f.servicio_id)
    query = _en_rango(query, Venta.creado_en, f.desde, f.hasta)
    if f.cliente_id:
        query = query.where(Venta.cliente_id == f.cliente_id)
    filas = (await db.execute(query)).all()
    return [(fila[0], float(fila[1])) for fila in filas]


async def serie_pqr_por_estado(db: AsyncSession) -> list[tuple[str, float]]:
    query = select(PQR.estado, func.count()).group_by(PQR.estado).order_by(PQR.estado)
    filas = (await db.execute(query)).all()
    return [
        (fila[0].value if hasattr(fila[0], "value") else str(fila[0]), float(fila[1]))
        for fila in filas
    ]


async def variacion_ingresos(db: AsyncSession, dias: int = 7) -> float | None:
    """Variación porcentual de ingresos frente al periodo anterior de igual duración."""
    hoy = datetime.now(timezone.utc).date()
    inicio_actual = hoy - timedelta(days=dias - 1)
    inicio_previo = inicio_actual - timedelta(days=dias)
    fin_previo = inicio_actual - timedelta(days=1)

    async def suma(desde: date, hasta: date) -> float:
        q = _en_rango(
            select(func.coalesce(func.sum(Venta.total), 0)).where(
                Venta.estado == EstadoVenta.pagada
            ),
            Venta.creado_en,
            desde,
            hasta,
        )
        return float(await _escalar(db, q))

    actual = await suma(inicio_actual, hoy)
    previo = await suma(inicio_previo, fin_previo)
    if previo == 0:
        # Sin base de comparación no se inventa un porcentaje.
        return None if actual == 0 else 100.0
    return round((actual - previo) / previo * 100, 2)
