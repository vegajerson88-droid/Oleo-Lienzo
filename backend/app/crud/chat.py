"""Persistencia de las conversaciones del chatbot."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.crud.base import contar, paginar
from app.models.chat import Conversacion, Mensaje, RolMensaje

# Cuántos mensajes previos se envían al modelo como contexto.
LIMITE_CONTEXTO = 10


async def obtener_o_crear_conversacion(
    db: AsyncSession, session_id: str, usuario_id: int | None
) -> Conversacion:
    query = select(Conversacion).where(Conversacion.session_id == session_id)
    conversacion = (await db.execute(query)).unique().scalar_one_or_none()
    if conversacion:
        # Al iniciar sesión a mitad de la conversación, se asocia al usuario.
        if usuario_id and conversacion.usuario_id is None:
            conversacion.usuario_id = usuario_id
            await db.commit()
        return conversacion

    conversacion = Conversacion(session_id=session_id, usuario_id=usuario_id)
    db.add(conversacion)
    await db.commit()
    await db.refresh(conversacion)
    return conversacion


async def agregar_mensaje(
    db: AsyncSession, conversacion: Conversacion, rol: RolMensaje, contenido: str
) -> Mensaje:
    mensaje = Mensaje(conversacion_id=conversacion.id, rol=rol, contenido=contenido)
    db.add(mensaje)
    # El primer mensaje del usuario da título a la conversación.
    if rol == RolMensaje.usuario and conversacion.titulo == "Nueva conversación":
        conversacion.titulo = contenido[:137] + "..." if len(contenido) > 140 else contenido
    await db.commit()
    await db.refresh(mensaje)
    return mensaje


async def historial_reciente(db: AsyncSession, conversacion_id: int) -> list[Mensaje]:
    """Últimos mensajes de la conversación, en orden cronológico."""
    query = (
        select(Mensaje)
        .where(Mensaje.conversacion_id == conversacion_id)
        .order_by(Mensaje.id.desc())
        .limit(LIMITE_CONTEXTO)
    )
    mensajes = list((await db.execute(query)).scalars().all())
    return list(reversed(mensajes))


async def get_conversacion(db: AsyncSession, conversacion_id: int) -> Conversacion:
    conversacion = await db.get(Conversacion, conversacion_id)
    if not conversacion:
        raise NotFoundError(f"Conversación {conversacion_id} no encontrada.")
    return conversacion


async def list_conversaciones(
    db: AsyncSession, page: int = 1, page_size: int = 10
) -> tuple[list[Conversacion], int]:
    query = select(Conversacion)
    total = await contar(db, query)
    query = paginar(query.order_by(Conversacion.actualizado_en.desc()), page, page_size)
    return list((await db.execute(query)).unique().scalars().all()), total
