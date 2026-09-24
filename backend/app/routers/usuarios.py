from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DomainError
from app.crud import usuario as usuario_crud
from app.database import get_db
from app.dependencies.auth import require_roles
from app.dependencies.pagination import PaginationParams, pagination_params
from app.schemas.common import Page
from app.schemas.usuario import UsuarioOut, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=Page[UsuarioOut])
async def listar_usuarios(
    rol: str | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("administrador")),
):
    items, total = await usuario_crud.list_usuarios(
        db, page=pagination.page, page_size=pagination.page_size, rol_nombre=rol
    )
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


@router.get("/{usuario_id}", response_model=UsuarioOut)
async def obtener_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("administrador")),
):
    try:
        return await usuario_crud.get_by_id(db, usuario_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.patch("/{usuario_id}", response_model=UsuarioOut)
async def actualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("administrador")),
):
    try:
        return await usuario_crud.update_usuario(db, usuario_id, data)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.delete("/{usuario_id}", status_code=204)
async def eliminar_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("administrador")),
):
    try:
        await usuario_crud.delete_usuario(db, usuario_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
