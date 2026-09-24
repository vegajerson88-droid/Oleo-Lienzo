from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.servicio import Servicio
from app.schemas.servicio import ServicioCreate, ServicioUpdate


async def get_by_id(db: AsyncSession, servicio_id: int) -> Servicio:
    servicio = await db.get(Servicio, servicio_id)
    if not servicio:
        raise NotFoundError(f"Servicio {servicio_id} no encontrado.")
    return servicio


async def list_servicios(
    db: AsyncSession, page: int = 1, page_size: int = 10, activo: bool | None = None
) -> tuple[list[Servicio], int]:
    query = select(Servicio)
    if activo is not None:
        query = query.where(Servicio.activo == activo)
    total = len((await db.execute(query)).scalars().all())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_servicio(db: AsyncSession, data: ServicioCreate) -> Servicio:
    servicio = Servicio(**data.model_dump())
    db.add(servicio)
    await db.commit()
    await db.refresh(servicio)
    return servicio


async def update_servicio(db: AsyncSession, servicio_id: int, data: ServicioUpdate) -> Servicio:
    servicio = await get_by_id(db, servicio_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(servicio, field, value)
    await db.commit()
    await db.refresh(servicio)
    return servicio


async def delete_servicio(db: AsyncSession, servicio_id: int) -> None:
    servicio = await get_by_id(db, servicio_id)
    await db.delete(servicio)
    await db.commit()
