"""Radicación y gestión de PQR."""
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.crud.base import contar, paginar
from app.models.pqr import PQR, TRANSICIONES_PQR, EstadoPQR, TipoPQR
from app.models.usuario import Usuario
from app.schemas.pqr import PQRCreate


def _radicado(pqr_id: int) -> str:
    return f"PQR-{pqr_id:06d}"


async def get_by_id(db: AsyncSession, pqr_id: int) -> PQR:
    pqr = (
        await db.execute(select(PQR).where(PQR.id == pqr_id))
    ).unique().scalar_one_or_none()
    if not pqr:
        raise NotFoundError(f"PQR {pqr_id} no encontrada.")
    return pqr


async def crear_pqr(
    db: AsyncSession, data: PQRCreate, cliente: Usuario | None = None
) -> PQR:
    """Radica una PQR. Si hay sesión iniciada, toma los datos del usuario."""
    if cliente is not None:
        nombre = f"{cliente.nombre} {cliente.apellido}"
        email = cliente.email
    else:
        if not data.contacto_nombre or not data.contacto_email:
            raise BusinessRuleError(
                "Sin sesión iniciada debes indicar contacto_nombre y contacto_email."
            )
        nombre = data.contacto_nombre
        email = data.contacto_email

    pqr = PQR(
        radicado="",  # se asigna tras el flush
        cliente_id=cliente.id if cliente else None,
        contacto_nombre=nombre,
        contacto_email=email,
        tipo=data.tipo,
        asunto=data.asunto,
        mensaje=data.mensaje,
        estado=EstadoPQR.pendiente,
    )
    db.add(pqr)
    await db.flush()
    pqr.radicado = _radicado(pqr.id)
    await db.commit()
    return await get_by_id(db, pqr.id)


async def list_pqr(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    cliente_id: int | None = None,
    estado: EstadoPQR | None = None,
    tipo: TipoPQR | None = None,
    buscar: str | None = None,
) -> tuple[list[PQR], int]:
    query = select(PQR)
    if cliente_id is not None:
        query = query.where(PQR.cliente_id == cliente_id)
    if estado:
        query = query.where(PQR.estado == estado)
    if tipo:
        query = query.where(PQR.tipo == tipo)
    if buscar:
        patron = f"%{buscar}%"
        query = query.where(
            or_(PQR.radicado.ilike(patron), PQR.asunto.ilike(patron),
                PQR.contacto_email.ilike(patron))
        )
    total = await contar(db, query)
    query = paginar(query.order_by(PQR.creado_en.desc(), PQR.id.desc()), page, page_size)
    return list((await db.execute(query)).unique().scalars().all()), total


async def responder(db: AsyncSession, pqr_id: int, respuesta: str, usuario_id: int) -> PQR:
    """Responde una PQR y la deja en estado `respondida`."""
    pqr = await get_by_id(db, pqr_id)
    if pqr.estado == EstadoPQR.cerrada:
        raise BusinessRuleError("No se puede responder una PQR cerrada.")
    pqr.respuesta = respuesta
    pqr.respondido_por_id = usuario_id
    pqr.respondido_en = datetime.now(timezone.utc)
    pqr.estado = EstadoPQR.respondida
    await db.commit()
    return await get_by_id(db, pqr_id)


async def cambiar_estado(db: AsyncSession, pqr_id: int, nuevo_estado: EstadoPQR) -> PQR:
    pqr = await get_by_id(db, pqr_id)
    permitidos = TRANSICIONES_PQR.get(pqr.estado, set())
    if nuevo_estado not in permitidos:
        raise BusinessRuleError(
            f"No se puede pasar de '{pqr.estado.value}' a '{nuevo_estado.value}'. "
            f"Transiciones válidas desde '{pqr.estado.value}': "
            f"{sorted(e.value for e in permitidos) or 'ninguna'}."
        )
    if nuevo_estado == EstadoPQR.respondida and not pqr.respuesta:
        raise BusinessRuleError(
            "No se puede marcar como respondida una PQR que aún no tiene respuesta."
        )
    pqr.estado = nuevo_estado
    await db.commit()
    return await get_by_id(db, pqr_id)
