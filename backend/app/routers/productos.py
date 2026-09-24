from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import obra as obra_crud
from app.database import get_db
from app.dependencies.auth import require_roles
from app.dependencies.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.obra import ObraCreate, ObraOut, ObraUpdate

router = APIRouter(prefix="/productos", tags=["obras / productos"])


@router.get("", response_model=Page[ObraOut])
async def listar_obras(
    artista: str | None = None,
    disponible: bool | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
):
    items, total = await obra_crud.list_obras(
        db,
        page=pagination.page,
        page_size=pagination.page_size,
        artista=artista,
        disponible=disponible,
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{obra_id}", response_model=ObraOut)
async def obtener_obra(obra_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await obra_crud.get_by_id(db, obra_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.post("", response_model=ObraOut, status_code=status.HTTP_201_CREATED)
async def crear_obra(
    data: ObraCreate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(require_roles("administrador", "empleado")),
):
    return await obra_crud.create_obra(db, data)


@router.put("/{obra_id}", response_model=ObraOut)
@router.patch("/{obra_id}", response_model=ObraOut)
async def actualizar_obra(
    obra_id: int,
    data: ObraUpdate,
    db: AsyncSession = Depends(get_db),
    _u=Depends(require_roles("administrador", "empleado")),
):
    try:
        return await obra_crud.update_obra(db, obra_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete("/{obra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_obra(
    obra_id: int,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("administrador")),
):
    try:
        await obra_crud.delete_obra(db, obra_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
