"""Operaciones de base de datos sobre las obras del catálogo."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.crud.base import borrar_protegido, contar, paginar
from app.models.obra import Obra
from app.schemas.obra import ObraCreate, ObraReplace, ObraUpdate


async def get_by_id(db: AsyncSession, obra_id: int) -> Obra:
    obra = await db.get(Obra, obra_id)
    if not obra:
        raise NotFoundError(f"Obra {obra_id} no encontrada.")
    return obra


async def list_obras(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    artista: str | None = None,
    tecnica: str | None = None,
    disponible: bool | None = None,
    precio_min: float | None = None,
    precio_max: float | None = None,
    buscar: str | None = None,
) -> tuple[list[Obra], int]:
    query = select(Obra)
    if artista:
        query = query.where(Obra.artista.ilike(f"%{artista}%"))
    if tecnica:
        query = query.where(Obra.tecnica.ilike(f"%{tecnica}%"))
    if disponible is not None:
        query = query.where(Obra.disponible == disponible)
    if precio_min is not None:
        query = query.where(Obra.precio >= precio_min)
    if precio_max is not None:
        query = query.where(Obra.precio <= precio_max)
    if buscar:
        patron = f"%{buscar}%"
        query = query.where(Obra.titulo.ilike(patron) | Obra.descripcion.ilike(patron))

    total = await contar(db, query)
    query = paginar(query.order_by(Obra.id.desc()), page, page_size)
    return list((await db.execute(query)).scalars().all()), total


async def create_obra(db: AsyncSession, data: ObraCreate) -> Obra:
    obra = Obra(**data.model_dump())
    db.add(obra)
    await db.commit()
    await db.refresh(obra)
    return obra


async def replace_obra(db: AsyncSession, obra_id: int, data: ObraReplace) -> Obra:
    """PUT: reemplaza el recurso completo."""
    obra = await get_by_id(db, obra_id)
    for field, value in data.model_dump().items():
        setattr(obra, field, value)
    await db.commit()
    await db.refresh(obra)
    return obra


async def update_obra(db: AsyncSession, obra_id: int, data: ObraUpdate) -> Obra:
    """PATCH: modifica solo los campos enviados."""
    obra = await get_by_id(db, obra_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obra, field, value)
    await db.commit()
    await db.refresh(obra)
    return obra


async def delete_obra(db: AsyncSession, obra_id: int) -> None:
    obra = await get_by_id(db, obra_id)
    await borrar_protegido(db, obra, f"la obra «{obra.titulo}»")
