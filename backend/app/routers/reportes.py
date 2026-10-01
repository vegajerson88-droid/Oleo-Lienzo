"""Reportes de ventas en JSON, PDF y Excel, por día, quincena o mes."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import periodos
from app.core.dinero import a_decimal
from app.core.periodos import Periodo, TipoPeriodo
from app.crud import venta as venta_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado
from app.dependencies.common import RESPUESTAS_AUTH
from app.services.excel import generar_reporte_ventas_excel
from app.services.pdf import generar_reporte_ventas_pdf

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    # La regla vale para todo el recurso: se declara una sola vez aquí.
    dependencies=[Depends(admin_o_empleado)],
    responses=RESPUESTAS_AUTH,
)

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

DiaQuery = Query(
    default=None,
    description="Fecha de referencia (AAAA-MM-DD). Por defecto, hoy.",
)
PeriodoQuery = Query(
    default=TipoPeriodo.dia,
    description=(
        "Qué abarca el reporte:\n\n"
        "- `dia`: solo la fecha de `dia` (por defecto, hoy).\n"
        "- `quincena`: los últimos 15 días contando esa fecha.\n"
        "- `mes`: desde el día 1 de ese mes hasta esa fecha.\n"
        "- `personalizado`: el rango `desde`–`hasta`."
    ),
)
DesdeQuery = Query(default=None, description="Inicio del rango personalizado.")
HastaQuery = Query(default=None, description="Fin del rango personalizado.")


def obtener_periodo(
    periodo: TipoPeriodo = PeriodoQuery,
    dia: date | None = DiaQuery,
    desde: date | None = DesdeQuery,
    hasta: date | None = HastaQuery,
) -> Periodo:
    """Resuelve el rango del reporte. Es dependencia para no repetirla en los tres endpoints."""
    try:
        return periodos.construir(periodo, dia=dia, desde=desde, hasta=hasta)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get(
    "/ventas-diarias",
    summary="Reporte diario de ventas (JSON)",
    description=(
        "Devuelve las ventas de una fecha con su detalle y los totales "
        "consolidados. Es la misma información que alimenta las versiones en "
        "PDF y Excel, para que el frontend pueda mostrarla antes de exportar."
    ),
)
async def reporte_ventas_diarias(
    periodo: Periodo = Depends(obtener_periodo),
    db: AsyncSession = Depends(get_db),
):
    ventas = await venta_crud.ventas_del_rango(db, periodo.desde, periodo.hasta)

    return {
        # `fecha` se conserva por compatibilidad: es el final del rango.
        "fecha": periodo.hasta.isoformat(),
        "periodo": {
            "tipo": periodo.tipo.value,
            "desde": periodo.desde.isoformat(),
            "hasta": periodo.hasta.isoformat(),
            "titulo": periodo.titulo,
            "descripcion": periodo.descripcion,
        },
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "empresa": {"nombre": "Óleo & Lienzo"},
        "resumen": {
            "ventas_registradas": len(ventas),
            "unidades_vendidas": sum(d.cantidad for v in ventas for d in v.detalles),
            "subtotal": float(sum((a_decimal(v.subtotal) for v in ventas), a_decimal(0))),
            "descuentos": float(sum((a_decimal(v.descuento) for v in ventas), a_decimal(0))),
            "iva": float(sum((a_decimal(v.impuestos) for v in ventas), a_decimal(0))),
            "total": float(sum((a_decimal(v.total) for v in ventas), a_decimal(0))),
        },
        "ventas": [
            {
                "numero": v.numero,
                "fecha_hora": v.creado_en.isoformat(),
                "cliente": f"{v.cliente.nombre} {v.cliente.apellido}" if v.cliente else None,
                "estado": v.estado.value,
                "metodo_pago": v.metodo_pago.value,
                "factura": v.factura.numero if v.factura else None,
                "items": [
                    {
                        "descripcion": d.descripcion,
                        "tipo": d.tipo,
                        "cantidad": d.cantidad,
                        "precio_unitario": float(d.precio_unitario),
                        "subtotal": float(d.subtotal),
                    }
                    for d in v.detalles
                ],
                "total": float(v.total),
            }
            for v in ventas
        ],
    }


@router.get(
    "/ventas-diarias/pdf",
    summary="Reporte diario de ventas en PDF",
    description=(
        "Genera el reporte en PDF (horizontal) con la cabecera corporativa, "
        "cuatro tarjetas de resumen —ventas, unidades, IVA recaudado y total—, "
        "la tabla de ventas del día con estado en color y el total general.\n\n"
        "Se construye en el servidor con ReportLab y se entrega como descarga."
    ),
    responses={200: {"content": {"application/pdf": {}}, "description": "Reporte en PDF."}},
    response_class=Response,
)
async def reporte_ventas_pdf(
    periodo: Periodo = Depends(obtener_periodo),
    db: AsyncSession = Depends(get_db),
):
    ventas = await venta_crud.ventas_del_rango(db, periodo.desde, periodo.hasta)
    pdf = generar_reporte_ventas_pdf(ventas, periodo)
    nombre = f"reporte-ventas-{periodo.sufijo_archivo}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get(
    "/ventas-diarias/excel",
    summary="Reporte diario de ventas en Excel (.xlsx)",
    description=(
        "Exporta el mismo reporte a Excel con una columna por dato, importes "
        "como números reales (no texto), fila de totales con fórmulas `SUM`, "
        "autofiltro, paneles congelados y una segunda hoja de resumen por "
        "estado. Queda listo para filtrar o hacer tablas dinámicas."
    ),
    responses={200: {"content": {TIPO_EXCEL: {}}, "description": "Libro de Excel."}},
    response_class=Response,
)
async def reporte_ventas_excel(
    periodo: Periodo = Depends(obtener_periodo),
    db: AsyncSession = Depends(get_db),
):
    ventas = await venta_crud.ventas_del_rango(db, periodo.desde, periodo.hasta)
    libro = generar_reporte_ventas_excel(ventas, periodo)
    nombre = f"reporte-ventas-{periodo.sufijo_archivo}.xlsx"
    return Response(
        content=libro,
        media_type=TIPO_EXCEL,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
