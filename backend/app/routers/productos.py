"""Catálogo de obras (productos). Lectura pública, escritura restringida."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import obra as obra_crud
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
from app.schemas.obra import ObraCreate, ObraOut, ObraReplace, ObraUpdate

router = APIRouter(prefix="/productos", tags=["Obras / Productos"])


@router.get(
    "",
    response_model=Page[ObraOut],
    summary="Listar obras del catálogo",
    description=(
        "Endpoint **público**: alimenta la galería del sitio sin necesidad de "
        "iniciar sesión.\n\n"
        "Admite filtrar por artista, técnica, disponibilidad y rango de precio, "
        "buscar por texto en el título o la descripción, y paginar."
    ),
)
async def listar_obras(
    artista: str | None = Query(default=None, max_length=80, description="Coincidencia parcial."),
    tecnica: str | None = Query(default=None, max_length=80, description="Coincidencia parcial."),
    disponible: bool | None = Query(default=None, description="Solo obras disponibles."),
    precio_min: float | None = Query(default=None, ge=0, description="Precio mínimo en COP."),
    precio_max: float | None = Query(default=None, ge=0, description="Precio máximo en COP."),
    buscar: BuscarQuery = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
):
    items, total = await obra_crud.list_obras(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        artista=artista,
        tecnica=tecnica,
        disponible=disponible,
        precio_min=precio_min,
        precio_max=precio_max,
        buscar=buscar,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get(
    "/{obra_id}",
    response_model=ObraOut,
    summary="Consultar una obra",
    description="Endpoint público con la ficha técnica completa de una obra.",
    responses=RESPUESTA_404,
)
async def obtener_obra(obra_id: IdPath, db: AsyncSession = Depends(get_db)):
    try:
        return await obra_crud.get_by_id(db, obra_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post(
    "",
    response_model=ObraOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una obra",
    description="Requiere rol administrador o empleado.",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_422},
)
async def crear_obra(
    data: ObraCreate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(admin_o_empleado),
):
    return await obra_crud.create_obra(db, data)


@router.put(
    "/{obra_id}",
    response_model=ObraOut,
    summary="Reemplazar una obra (actualización completa)",
    description=(
        "**PUT**: sustituye el recurso entero. Todos los campos son "
        "obligatorios; lo que se omita se rechaza con un 422.\n\n"
        "Para modificar un solo campo, usa `PATCH`."
    ),
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_422},
)
async def reemplazar_obra(
    obra_id: IdPath,
    data: ObraReplace,
    db: AsyncSession = Depends(get_db),
    _u=Depends(admin_o_empleado),
):
    try:
        return await obra_crud.replace_obra(db, obra_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch(
    "/{obra_id}",
    response_model=ObraOut,
    summary="Actualizar una obra (parcialmente)",
    description="**PATCH**: modifica solo los campos enviados en el cuerpo.",
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_422},
)
async def actualizar_obra(
    obra_id: IdPath,
    data: ObraUpdate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(admin_o_empleado),
):
    try:
        return await obra_crud.update_obra(db, obra_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete(
    "/{obra_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una obra",
    description=(
        "Solo el administrador. Devuelve 409 si la obra ya aparece en algún "
        "pedido o venta: en ese caso hay que marcarla como no disponible."
    ),
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_409},
)
async def eliminar_obra(
    obra_id: IdPath,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(solo_admin),
):
    try:
        await obra_crud.delete_obra(db, obra_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
