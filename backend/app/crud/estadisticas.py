"""Agregaciones que alimentan los dashboards.

Todos los indicadores y series salen de consultas SQL con GROUP BY; el
frontend nunca calcula ni inventa un número (requisito 15 del quinto avance).

`func.date()` se usa para agrupar por día porque es la única expresión que
funciona igual en PostgreSQL y en SQLite (el CAST a DATE no lo es).
"""
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


def _a_etiqueta_fecha(valor) -> str:
    """Normaliza el resultado de func.date(): PostgreSQL devuelve date, SQLite str."""
    return valor.isoformat() if isinstance(valor, (date, datetime)) else str(valor)


async def _escalar(db: AsyncSession, query: Select, por_defecto=0):
    resultado = (await db.execute(query)).scalar()
    return resultado if resultado is not None else por_defecto


async def indicadores_admin(
    db: AsyncSession, desde: date | None = None, hasta: date | None = None
) -> dict:
    """Panorama completo del sistema para el rol administrador."""
    ventas_q = _en_rango(
        select(Venta).where(Venta.estado.in_(VENTAS_EFECTIVAS)),
        Venta.creado_en, desde, hasta,
    )
    facturado_q = _en_rango(
        select(func.coalesce(func.sum(Factura.total), 0)), Factura.fecha_emision, desde, hasta
    )
    ingresos_q = _en_rango(
        select(func.coalesce(func.sum(Venta.total), 0)).where(
            Venta.estado == EstadoVenta.pagada
        ),
        Venta.creado_en, desde, hasta,
    )

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
        "total_ventas": await _escalar(
            db, select(func.count()).select_from(ventas_q.subquery())
        ),
        "ingresos": float(await _escalar(db, ingresos_q)),
        "total_facturado": float(await _escalar(db, facturado_q)),
        "total_facturas": await _escalar(db, select(func.count()).select_from(Factura)),
        "pqr_recibidas": await _escalar(db, select(func.count()).select_from(PQR)),
        "pqr_pendientes": await _escalar(
            db,
            select(func.count()).select_from(PQR).where(
                PQR.estado.in_((EstadoPQR.pendiente, EstadoPQR.en_proceso))
            ),
        ),
        "total_pedidos": await _escalar(db, select(func.count()).select_from(Pedido)),
    }


async def indicadores_empleado(
    db: AsyncSession, desde: date | None = None, hasta: date | None = None
) -> dict:
    """Subconjunto operativo: el empleado no ve usuarios ni facturación global."""
    completo = await indicadores_admin(db, desde, hasta)
    visibles = (
        "total_obras", "obras_disponibles", "total_servicios",
        "total_ventas", "total_pedidos", "pqr_pendientes",
    )
    return {k: completo[k] for k in visibles}


async def indicadores_cliente(db: AsyncSession, cliente_id: int) -> dict:
    """Solo la información del propio cliente."""
    mis_ventas = select(Venta).where(Venta.cliente_id == cliente_id)
    return {
        "mis_pedidos": await _escalar(
            db, select(func.count()).select_from(Pedido).where(Pedido.cliente_id == cliente_id)
        ),
        "mis_compras": await _escalar(db, select(func.count()).select_from(mis_ventas.subquery())),
        "total_invertido": float(
            await _escalar(
                db,
                select(func.coalesce(func.sum(Venta.total), 0)).where(
                    Venta.cliente_id == cliente_id, Venta.estado == EstadoVenta.pagada
                ),
            )
        ),
        "mis_facturas": await _escalar(
            db, select(func.count()).select_from(Factura).where(Factura.cliente_id == cliente_id)
        ),
        "mis_pqr_abiertas": await _escalar(
            db,
            select(func.count()).select_from(PQR).where(
                PQR.cliente_id == cliente_id,
                PQR.estado.in_((EstadoPQR.pendiente, EstadoPQR.en_proceso)),
            ),
        ),
    }


async def serie_ventas_por_dia(
    db: AsyncSession,
    desde: date | None = None,
    hasta: date | None = None,
    cliente_id: int | None = None,
) -> list[tuple[str, float]]:
    """Total vendido por día: alimenta el gráfico lineal."""
    dia = func.date(Venta.creado_en).label("dia")
    query = (
        select(dia, func.coalesce(func.sum(Venta.total), 0))
        .where(Venta.estado.in_(VENTAS_EFECTIVAS))
        .group_by(dia)
        .order_by(dia)
    )
    query = _en_rango(query, Venta.creado_en, desde, hasta)
    if cliente_id:
        query = query.where(Venta.cliente_id == cliente_id)
    filas = (await db.execute(query)).all()
    return [(_a_etiqueta_fecha(f[0]), float(f[1])) for f in filas]


async def serie_ventas_por_estado(
    db: AsyncSession, desde: date | None = None, hasta: date | None = None
) -> list[tuple[str, float]]:
    """Cuántas ventas hay en cada estado: gráfico de barras."""
    query = select(Venta.estado, func.count()).group_by(Venta.estado).order_by(Venta.estado)
    query = _en_rango(query, Venta.creado_en, desde, hasta)
    filas = (await db.execute(query)).all()
    return [(f[0].value if hasattr(f[0], "value") else str(f[0]), float(f[1])) for f in filas]


async def top_productos(
    db: AsyncSession,
    desde: date | None = None,
    hasta: date | None = None,
    limite: int = 5,
) -> list[tuple[str, float]]:
    """Obras y servicios más vendidos por importe: gráfico de barras."""
    query = (
        select(DetalleVenta.descripcion, func.coalesce(func.sum(DetalleVenta.subtotal), 0))
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .where(Venta.estado.in_(VENTAS_EFECTIVAS))
        .group_by(DetalleVenta.descripcion)
        .order_by(func.coalesce(func.sum(DetalleVenta.subtotal), 0).desc())
        .limit(limite)
    )
    query = _en_rango(query, Venta.creado_en, desde, hasta)
    filas = (await db.execute(query)).all()
    return [(f[0], float(f[1])) for f in filas]


async def serie_pqr_por_estado(db: AsyncSession) -> list[tuple[str, float]]:
    query = select(PQR.estado, func.count()).group_by(PQR.estado).order_by(PQR.estado)
    filas = (await db.execute(query)).all()
    return [(f[0].value if hasattr(f[0], "value") else str(f[0]), float(f[1])) for f in filas]


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
            Venta.creado_en, desde, hasta,
        )
        return float(await _escalar(db, q))

    actual = await suma(inicio_actual, hoy)
    previo = await suma(inicio_previo, fin_previo)
    if previo == 0:
        # Sin base de comparación no se inventa un porcentaje.
        return None if actual == 0 else 100.0
    return round((actual - previo) / previo * 100, 2)
