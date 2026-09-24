"""Facturación: emisión, consulta y descarga en PDF."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import factura as factura_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado, get_current_user
from app.dependencies.common import (
    RESPUESTA_404,
    RESPUESTA_409,
    RESPUESTA_422,
    RESPUESTAS_AUTH,
    BuscarQuery,
    IdPath,
)
from app.dependencies.pagination import PaginationParams, pagination_params
from app.models.factura import EstadoFactura
from app.models.usuario import Usuario
from app.schemas.common import Page
from app.schemas.factura import FacturaCambioEstado, FacturaCreate, FacturaOut
from app.services.pdf import generar_factura_pdf

router = APIRouter(prefix="/facturas", tags=["Facturación"], responses=RESPUESTAS_AUTH)


@router.get(
    "",
    response_model=Page[FacturaOut],
    summary="Consultar facturas",
    description=(
        "Busca facturas por número, cliente, estado o rango de fechas de "
        "emisión. El parámetro `buscar` cubre a la vez número, nombre y "
        "documento del cliente.\n\n"
        "Un **cliente** solo ve sus propias facturas."
    ),
)
async def listar_facturas(
    numero: str | None = Query(default=None, max_length=24, description="Número de factura."),
    cliente_id: int | None = Query(default=None, ge=1),
    estado: EstadoFactura | None = Query(default=None),
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    buscar: BuscarQuery = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if usuario.rol.nombre == "cliente":
        cliente_id = usuario.id

    items, total = await factura_crud.list_facturas(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        numero=numero,
        cliente_id=cliente_id,
        estado=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        buscar=buscar,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


async def _factura_autorizada(db: AsyncSession, factura_id: int, usuario: Usuario):
    try:
        factura = await factura_crud.get_by_id(db, factura_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    if usuario.rol.nombre == "cliente" and factura.cliente_id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Esta factura no es tuya."
        )
    return factura


@router.get(
    "/{factura_id}",
    response_model=FacturaOut,
    summary="Consultar una factura",
    responses=RESPUESTA_404,
)
async def obtener_factura(
    factura_id: IdPath,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return await _factura_autorizada(db, factura_id, usuario)


@router.get(
    "/{factura_id}/pdf",
    summary="Descargar la factura en PDF",
    description=(
        "Genera el PDF **en el servidor** y lo devuelve como descarga.\n\n"
        "Incluye logotipo, razón social, NIT, datos del cliente, número y "
        "fecha, líneas con cantidades y precios, subtotal, descuento, IVA "
        "desglosado, total, método de pago, estado y pie de página.\n\n"
        "El cliente solo puede descargar sus propias facturas."
    ),
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Documento PDF de la factura.",
        },
        **RESPUESTA_404,
    },
    response_class=Response,
)
async def descargar_factura_pdf(
    factura_id: IdPath,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    factura = await _factura_autorizada(db, factura_id, usuario)
    pdf = generar_factura_pdf(factura)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="factura-{factura.numero}.pdf"'},
    )


@router.post(
    "",
    response_model=FacturaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Emitir una factura a partir de una venta",
    description=(
        "Crea la factura de una venta existente con un consecutivo "
        "`OL-NNNNNN`.\n\n"
        "La factura **congela** los datos del cliente y los importes en el "
        "momento de emitirse: si después cambia el perfil del cliente o el "
        "catálogo, el documento no se altera.\n\n"
        "Una venta solo puede facturarse una vez (409) y una venta anulada no "
        "puede facturarse (422)."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_409, **RESPUESTA_422},
)
async def emitir_factura(
    data: FacturaCreate,
    db: AsyncSession = Depends(get_db),
    _u: Usuario = Depends(admin_o_empleado),
):
    try:
        return await factura_crud.emitir_factura(db, data.venta_id, data.observaciones)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch(
    "/{factura_id}/estado",
    response_model=FacturaOut,
    summary="Cambiar el estado de una factura",
    description=(
        "Transiciones permitidas:\n\n"
        "```\n"
        "emitida → pagada | anulada\n"
        "pagada  → anulada\n"
        "anulada → (final)\n"
        "```"
    ),
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def cambiar_estado_factura(
    factura_id: IdPath,
    data: FacturaCambioEstado,
    db: AsyncSession = Depends(get_db),
    _u: Usuario = Depends(admin_o_empleado),
):
    try:
        return await factura_crud.cambiar_estado(db, factura_id, data.nuevo_estado)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
