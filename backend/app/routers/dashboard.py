"""Dashboards diferenciados por rol.

Todos los indicadores y series se calculan en la base de datos. El frontend
solo los dibuja: no escribe ni un número a mano.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import estadisticas
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.common import RESPUESTAS_AUTH
from app.models.usuario import Usuario
from app.schemas.dashboard import DashboardOut, IndicadorCard, PuntoSerie, SerieGrafico

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], responses=RESPUESTAS_AUTH)

# Etiqueta y formato de presentación de cada indicador.
ETIQUETAS: dict[str, tuple[str, str]] = {
    "total_usuarios": ("Usuarios registrados", "numero"),
    "usuarios_activos": ("Usuarios activos", "numero"),
    "total_obras": ("Obras en catálogo", "numero"),
    "obras_disponibles": ("Obras disponibles", "numero"),
    "total_servicios": ("Servicios activos", "numero"),
    "total_ventas": ("Ventas registradas", "numero"),
    "ingresos": ("Ingresos cobrados", "moneda"),
    "total_facturado": ("Total facturado", "moneda"),
    "total_facturas": ("Facturas emitidas", "numero"),
    "pqr_recibidas": ("PQR recibidas", "numero"),
    "pqr_pendientes": ("PQR pendientes", "numero"),
    "total_pedidos": ("Pedidos", "numero"),
    "mis_pedidos": ("Mis pedidos", "numero"),
    "mis_compras": ("Mis compras", "numero"),
    "total_invertido": ("Total invertido", "moneda"),
    "mis_facturas": ("Mis facturas", "numero"),
    "mis_pqr_abiertas": ("Mis PQR abiertas", "numero"),
}


def _a_cards(datos: dict, variaciones: dict | None = None) -> list[IndicadorCard]:
    variaciones = variaciones or {}
    tarjetas = []
    for clave, valor in datos.items():
        etiqueta, formato = ETIQUETAS.get(clave, (clave.replace("_", " ").capitalize(), "numero"))
        tarjetas.append(
            IndicadorCard(
                clave=clave,
                etiqueta=etiqueta,
                valor=float(valor),
                formato=formato,
                variacion=variaciones.get(clave),
            )
        )
    return tarjetas


def _serie(nombre: str, tipo: str, puntos: list[tuple[str, float]]) -> SerieGrafico:
    return SerieGrafico(
        nombre=nombre,
        tipo=tipo,
        puntos=[PuntoSerie(etiqueta=e, valor=v) for e, v in puntos],
    )


@router.get(
    "",
    response_model=DashboardOut,
    summary="Dashboard del usuario autenticado",
    description=(
        "Devuelve los indicadores y gráficos que corresponden al **rol de "
        "quien consulta**, sin que el frontend tenga que pedir uno concreto:\n\n"
        "- **Administrador**: usuarios, obras, servicios, ventas, facturación "
        "y PQR, con la evolución diaria de ventas, el reparto por estado, los "
        "productos más vendidos y el estado de las PQR.\n"
        "- **Empleado**: solo lo operativo (catálogo, ventas, pedidos y PQR "
        "pendientes). No ve usuarios ni ingresos globales.\n"
        "- **Cliente**: únicamente su propia actividad: pedidos, compras, "
        "total invertido, facturas y PQR abiertas.\n\n"
        "Acepta `fecha_inicio` y `fecha_fin` para acotar el periodo."
    ),
)
async def obtener_dashboard(
    fecha_inicio: date | None = Query(default=None, description="Inicio del periodo."),
    fecha_fin: date | None = Query(default=None, description="Fin del periodo."),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="fecha_inicio no puede ser posterior a fecha_fin.",
        )

    rol = usuario.rol.nombre

    if rol == "administrador":
        datos = await estadisticas.indicadores_admin(db, fecha_inicio, fecha_fin)
        variacion = await estadisticas.variacion_ingresos(db)
        graficos = [
            _serie(
                "Ventas por día",
                "linea",
                await estadisticas.serie_ventas_por_dia(db, fecha_inicio, fecha_fin),
            ),
            _serie(
                "Ventas por estado",
                "barras",
                await estadisticas.serie_ventas_por_estado(db, fecha_inicio, fecha_fin),
            ),
            _serie(
                "Productos y servicios más vendidos",
                "barras",
                await estadisticas.top_productos(db, fecha_inicio, fecha_fin),
            ),
            _serie("PQR por estado", "barras", await estadisticas.serie_pqr_por_estado(db)),
        ]
        tarjetas = _a_cards(datos, {"ingresos": variacion})

    elif rol == "empleado":
        datos = await estadisticas.indicadores_empleado(db, fecha_inicio, fecha_fin)
        graficos = [
            _serie(
                "Ventas por día",
                "linea",
                await estadisticas.serie_ventas_por_dia(db, fecha_inicio, fecha_fin),
            ),
            _serie(
                "Productos y servicios más vendidos",
                "barras",
                await estadisticas.top_productos(db, fecha_inicio, fecha_fin),
            ),
        ]
        tarjetas = _a_cards(datos)

    else:  # cliente
        datos = await estadisticas.indicadores_cliente(db, usuario.id)
        graficos = [
            _serie(
                "Mis compras por día",
                "linea",
                await estadisticas.serie_ventas_por_dia(
                    db, fecha_inicio, fecha_fin, cliente_id=usuario.id
                ),
            )
        ]
        tarjetas = _a_cards(datos)

    return DashboardOut(
        rol=rol,
        periodo_inicio=fecha_inicio.isoformat() if fecha_inicio else None,
        periodo_fin=fecha_fin.isoformat() if fecha_fin else None,
        indicadores=tarjetas,
        graficos=graficos,
    )
