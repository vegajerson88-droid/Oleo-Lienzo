from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import servicio as servicio_crud
from app.database import get_db
from app.dependencies.auth import require_roles
from app.dependencies.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.servicio import ServicioCreate, ServicioOut, ServicioUpdate

router = APIRouter(prefix="/servicios", tags=["servicios"])


@router.get("", response_model=Page[ServicioOut])
async def listar_servicios(
    activo: bool | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
):
    items, total = await servicio_crud.list_servicios(
        db, page=pagination.page, page_size=pagination.page_size, activo=activo
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{servicio_id}", response_model=ServicioOut)
async def obtener_servicio(servicio_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await servicio_crud.get_by_id(db, servicio_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("", response_model=ServicioOut, status_code=status.HTTP_201_CREATED)
async def crear_servicio(
    data: ServicioCreate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(require_roles("administrador", "empleado")),
):
    return await servicio_crud.create_servicio(db, data)


@router.patch("/{servicio_id}", response_model=ServicioOut)
async def actualizar_servicio(
    servicio_id: int,
    data: ServicioUpdate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(require_roles("administrador", "empleado")),
):
    try:
        return await servicio_crud.update_servicio(db, servicio_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete("/{servicio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_servicio(
    servicio_id: int,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("administrador")),
):
    try:
        await servicio_crud.delete_servicio(db, servicio_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
