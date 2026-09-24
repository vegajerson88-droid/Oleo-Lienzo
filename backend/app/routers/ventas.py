"""Módulo de ventas: registro, historial e informes básicos."""

from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import venta as venta_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado, get_current_user
from app.dependencies.common import RESPUESTA_404, RESPUESTA_422, RESPUESTAS_AUTH, IdPath
from app.dependencies.pagination import PaginationParams, pagination_params
from app.models.usuario import Usuario
from app.models.venta import EstadoVenta
from app.schemas.common import Page
from app.schemas.venta import VentaCambioEstado, VentaCreate, VentaFiltros, VentaOut
from app.services import email as email_service

router = APIRouter(prefix="/ventas", tags=["Ventas"], responses=RESPUESTAS_AUTH)


@router.get(
    "",
    response_model=Page[VentaOut],
    summary="Historial de ventas con filtros",
    description=(
        "Consulta del historial comercial con todos los criterios del quinto "
        "avance: **rango de fechas, cliente, producto, servicio, estado y "
        "rango de valor**, combinables entre sí.\n\n"
        "Un **cliente** solo ve sus propias compras, aunque pida otro "
        "`cliente_id`: el backend sobrescribe ese filtro con su identidad."
    ),
)
async def listar_ventas(
    fecha_inicio: date | None = Query(default=None, description="Desde esta fecha, inclusive."),
    fecha_fin: date | None = Query(default=None, description="Hasta esta fecha, inclusive."),
    cliente_id: int | None = Query(default=None, ge=1),
    obra_id: int | None = Query(default=None, ge=1, description="Ventas que incluyan esta obra."),
    servicio_id: int | None = Query(default=None, ge=1, description="Ventas con este servicio."),
    estado: EstadoVenta | None = Query(default=None),
    total_min: float | None = Query(default=None, ge=0, description="Valor mínimo de la venta."),
    total_max: float | None = Query(default=None, ge=0, description="Valor máximo de la venta."),
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        filtros = VentaFiltros(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            cliente_id=cliente_id,
            obra_id=obra_id,
            servicio_id=servicio_id,
            estado=estado,
            total_min=total_min,
            total_max=total_max,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # Un cliente nunca puede consultar las ventas de otro.
    if usuario.rol.nombre == "cliente":
        filtros.cliente_id = usuario.id

    items, total = await venta_crud.list_ventas(
        db, filtros, page=pagination.page, page_size=pagination.page_size
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get(
    "/{venta_id}",
    response_model=VentaOut,
    summary="Consultar una venta",
    responses=RESPUESTA_404,
)
async def obtener_venta(
    venta_id: IdPath,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        venta = await venta_crud.get_by_id(db, venta_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    if usuario.rol.nombre == "cliente" and venta.cliente_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta venta no es tuya.")
    return venta


@router.post(
    "",
    response_model=VentaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una venta",
    description=(
        "Registra una venta presencial desde el panel. Requiere rol "
        "administrador o empleado.\n\n"
        "El backend recalcula el desglose completo con los precios vigentes: "
        "subtotal por línea, descuentos, base gravable e IVA "
        "(`IVA_PORCENTAJE` del `.env`, 19 % por defecto). Descuenta el stock y "
        "asigna un consecutivo `V-AAAA-NNNNNN`.\n\n"
        "Toda la aritmética usa `Decimal`, nunca coma flotante."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def crear_venta(
    data: VentaCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(admin_o_empleado),
):
    try:
        return await venta_crud.crear_venta(db, data, usuario.id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch(
    "/{venta_id}/estado",
    response_model=VentaOut,
    summary="Cambiar el estado de una venta",
    description=(
        "Transición validada contra la máquina de estados:\n\n"
        "```\n"
        "pendiente_pago → pagada | anulada\n"
        "pagada         → reembolsada\n"
        "anulada        → (final)\n"
        "reembolsada    → (final)\n"
        "```\n\n"
        "Una venta pagada **no puede anularse**: se reembolsa, que sí deja "
        "rastro contable. Anular o reembolsar **devuelve las obras al "
        "inventario**. Marcarla como pagada dispara el correo de confirmación "
        "en segundo plano."
    ),
    responses={**RESPUESTA_404, **RESPUESTA_422},
)
async def cambiar_estado_venta(
    venta_id: IdPath,
    data: VentaCambioEstado,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _u: Usuario = Depends(admin_o_empleado),
):
    try:
        venta = await venta_crud.cambiar_estado(db, venta_id, data.nuevo_estado)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    if venta.estado == EstadoVenta.pagada:
        background_tasks.add_task(
            email_service.enviar_confirmacion_compra, venta, venta.factura_numero
        )
    return venta
