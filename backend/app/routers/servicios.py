"""Servicios de la galería: enmarcado, restauración y envío."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import servicio as servicio_crud
from app.database import get_db
from app.dependencies.auth import admin_o_empleado, solo_admin
from app.dependencies.common import (
    RESPUESTA_404,
    RESPUESTA_409,
    RESPUESTA_422,
    RESPUESTAS_AUTH,
    BuscarQuery,
    IdPath,
)
from app.dependencies.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.servicio import ServicioCreate, ServicioOut, ServicioReplace, ServicioUpdate

router = APIRouter(prefix="/servicios", tags=["Servicios"])


@router.get(
    "",
    response_model=Page[ServicioOut],
    summary="Listar servicios",
    description="Endpoint público. Filtra por estado y busca por nombre.",
)
async def listar_servicios(
    activo: bool | None = Query(default=None, description="Solo servicios activos."),
    buscar: BuscarQuery = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
):
    items, total = await servicio_crud.list_servicios(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        activo=activo,
        buscar=buscar,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get(
    "/{servicio_id}",
    response_model=ServicioOut,
    summary="Consultar un servicio",
    responses=RESPUESTA_404,
)
async def obtener_servicio(servicio_id: IdPath, db: AsyncSession = Depends(get_db)):
    try:
        return await servicio_crud.get_by_id(db, servicio_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post(
    "",
    response_model=ServicioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un servicio",
    description="El nombre del servicio es único: se rechaza con 409 si ya existe.",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_409, **RESPUESTA_422},
)
async def crear_servicio(
    data: ServicioCreate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(admin_o_empleado),
):
    try:
        return await servicio_crud.create_servicio(db, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.put(
    "/{servicio_id}",
    response_model=ServicioOut,
    summary="Reemplazar un servicio (actualización completa)",
    description="**PUT**: exige el recurso completo.",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_409, **RESPUESTA_422},
)
async def reemplazar_servicio(
    servicio_id: IdPath,
    data: ServicioReplace,
    db: AsyncSession = Depends(get_db),
    _u=Depends(admin_o_empleado),
):
    try:
        return await servicio_crud.replace_servicio(db, servicio_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch(
    "/{servicio_id}",
    response_model=ServicioOut,
    summary="Actualizar un servicio (parcialmente)",
    description="**PATCH**: modifica solo los campos enviados.",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_409, **RESPUESTA_422},
)
async def actualizar_servicio(
    servicio_id: IdPath,
    data: ServicioUpdate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(admin_o_empleado),
):
    try:
        return await servicio_crud.update_servicio(db, servicio_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete(
    "/{servicio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un servicio",
    description="Solo el administrador. Devuelve 409 si el servicio ya se vendió.",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_409},
)
async def eliminar_servicio(
    servicio_id: IdPath,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(solo_admin),
):
    try:
        await servicio_crud.delete_servicio(db, servicio_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
