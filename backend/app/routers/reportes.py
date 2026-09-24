"""Reporte diario de ventas en JSON, PDF y Excel."""

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dinero import a_decimal
from app.crud import venta as venta_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado
from app.dependencies.common import RESPUESTAS_AUTH
from app.models.usuario import Usuario
from app.services.excel import generar_reporte_ventas_excel
from app.services.pdf import generar_reporte_ventas_pdf

router = APIRouter(prefix="/reportes", tags=["Reportes"], responses=RESPUESTAS_AUTH)

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

DiaQuery = Query(
    default=None,
    description="Fecha del reporte en formato AAAA-MM-DD. Por defecto, hoy.",
)


def _dia_o_hoy(dia: date | None) -> date:
    return dia or datetime.now(timezone.utc).date()


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
    dia: date | None = DiaQuery,
    db: AsyncSession = Depends(get_db),
    _u: Usuario = Depends(admin_o_empleado),
):
    fecha = _dia_o_hoy(dia)
    ventas = await venta_crud.ventas_del_dia(db, fecha)

    return {
        "fecha": fecha.isoformat(),
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
    dia: date | None = DiaQuery,
    db: AsyncSession = Depends(get_db),
    _u: Usuario = Depends(admin_o_empleado),
):
    fecha = _dia_o_hoy(dia)
    ventas = await venta_crud.ventas_del_dia(db, fecha)
    pdf = generar_reporte_ventas_pdf(ventas, fecha)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="reporte-ventas-{fecha.isoformat()}.pdf"'
        },
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
    dia: date | None = DiaQuery,
    db: AsyncSession = Depends(get_db),
    _u: Usuario = Depends(admin_o_empleado),
):
    fecha = _dia_o_hoy(dia)
    ventas = await venta_crud.ventas_del_dia(db, fecha)
    libro = generar_reporte_ventas_excel(ventas, fecha)
    return Response(
        content=libro,
        media_type=TIPO_EXCEL,
        headers={
            "Content-Disposition": f'attachment; filename="reporte-ventas-{fecha.isoformat()}.xlsx"'
        },
    )
