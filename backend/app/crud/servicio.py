"""Operaciones de base de datos sobre los servicios de la galería."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.crud.base import borrar_protegido, contar, paginar
from app.models.servicio import Servicio
from app.schemas.servicio import ServicioCreate, ServicioReplace, ServicioUpdate


async def get_by_id(db: AsyncSession, servicio_id: int) -> Servicio:
    servicio = await db.get(Servicio, servicio_id)
    if not servicio:
        raise NotFoundError(f"Servicio {servicio_id} no encontrado.")
    return servicio


async def _nombre_duplicado(db: AsyncSession, nombre: str, excluir_id: int | None = None) -> bool:
    query = select(Servicio).where(Servicio.nombre == nombre)
    if excluir_id is not None:
        query = query.where(Servicio.id != excluir_id)
    return (await db.execute(query)).scalar_one_or_none() is not None


async def list_servicios(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    activo: bool | None = None,
    buscar: str | None = None,
) -> tuple[list[Servicio], int]:
    query = select(Servicio)
    if activo is not None:
        query = query.where(Servicio.activo == activo)
    if buscar:
        query = query.where(Servicio.nombre.ilike(f"%{buscar}%"))
    total = await contar(db, query)
    query = paginar(query.order_by(Servicio.id.desc()), page, page_size)
    return list((await db.execute(query)).scalars().all()), total


async def create_servicio(db: AsyncSession, data: ServicioCreate) -> Servicio:
    if await _nombre_duplicado(db, data.nombre):
        raise ConflictError(f"Ya existe un servicio llamado '{data.nombre}'.")
    servicio = Servicio(**data.model_dump())
    db.add(servicio)
    await db.commit()
    await db.refresh(servicio)
    return servicio


async def replace_servicio(db: AsyncSession, servicio_id: int, data: ServicioReplace) -> Servicio:
    """PUT: reemplaza el recurso completo."""
    servicio = await get_by_id(db, servicio_id)
    if await _nombre_duplicado(db, data.nombre, excluir_id=servicio_id):
        raise ConflictError(f"Ya existe un servicio llamado '{data.nombre}'.")
    for field, value in data.model_dump().items():
        setattr(servicio, field, value)
    await db.commit()
    await db.refresh(servicio)
    return servicio


async def update_servicio(db: AsyncSession, servicio_id: int, data: ServicioUpdate) -> Servicio:
    """PATCH: modifica solo los campos enviados."""
    servicio = await get_by_id(db, servicio_id)
    cambios = data.model_dump(exclude_unset=True)
    if "nombre" in cambios and await _nombre_duplicado(
        db, cambios["nombre"], excluir_id=servicio_id
    ):
        raise ConflictError(f"Ya existe un servicio llamado '{cambios['nombre']}'.")
    for field, value in cambios.items():
        setattr(servicio, field, value)
    await db.commit()
    await db.refresh(servicio)
    return servicio


async def delete_servicio(db: AsyncSession, servicio_id: int) -> None:
    servicio = await get_by_id(db, servicio_id)
    await borrar_protegido(db, servicio, f"el servicio «{servicio.nombre}»")
