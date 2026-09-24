"""Utilidades compartidas por la capa CRUD."""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def contar(db: AsyncSession, query: Select) -> int:
    """Cuenta los registros que devolvería `query` sin traerlos a memoria.

    La versión anterior hacía `len(result.scalars().all())`, que carga la
    tabla entera solo para contarla. Aquí se envuelve la consulta en un
    SELECT COUNT(*) y el trabajo lo hace PostgreSQL.
    """
    sin_orden = query.order_by(None).limit(None).offset(None)
    return (await db.execute(select(func.count()).select_from(sin_orden.subquery()))).scalar_one()


def paginar(query: Select, page: int, page_size: int) -> Select:
    """Aplica OFFSET/LIMIT a partir de un número de página que empieza en 1."""
    return query.offset((page - 1) * page_size).limit(page_size)


async def borrar_protegido(db: AsyncSession, instancia, etiqueta: str) -> None:
    """Borra un registro traduciendo la violación de clave foránea a un 409.

    PostgreSQL impide borrar filas referenciadas (ON DELETE RESTRICT) y lanza
    IntegrityError, que sin capturar acabaría como un 500. Aquí se convierte
    en un conflicto explicado, que es lo que el cliente necesita saber.
    """
    from sqlalchemy.exc import IntegrityError

    from app.core.exceptions import ConflictError

    try:
        await db.delete(instancia)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError(
            f"No se puede eliminar {etiqueta} porque tiene registros asociados "
            f"(pedidos, ventas o facturas). Desactívalo en lugar de borrarlo "
            f"para conservar el historial."
        )
