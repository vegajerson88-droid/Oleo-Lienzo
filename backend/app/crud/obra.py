from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.obra import Obra
from app.schemas.obra import ObraCreate, ObraUpdate


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
    disponible: bool | None = None,
) -> tuple[list[Obra], int]:
    query = select(Obra)
    if artista:
        query = query.where(Obra.artista.ilike(f"%{artista}%"))
    if disponible is not None:
        query = query.where(Obra.disponible == disponible)

    total = len((await db.execute(query)).scalars().all())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_obra(db: AsyncSession, data: ObraCreate) -> Obra:
    obra = Obra(**data.model_dump())
    db.add(obra)
    await db.commit()
    await db.refresh(obra)
    return obra


async def update_obra(db: AsyncSession, obra_id: int, data: ObraUpdate) -> Obra:
    obra = await get_by_id(db, obra_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obra, field, value)
    await db.commit()
    await db.refresh(obra)
    return obra


async def delete_obra(db: AsyncSession, obra_id: int) -> None:
    obra = await get_by_id(db, obra_id)
    await db.delete(obra)
    await db.commit()
