"""Tareas que se ejecutan en segundo plano, después de responder al cliente.

Estas funciones corren cuando la petición ya terminó y su sesión de base de
datos está cerrada. Por eso **no reciben objetos del ORM**: reciben
identificadores y abren su propia sesión para releer lo que necesitan.

Pasar un objeto ya cargado parece más cómodo, pero ata la tarea a que todas
sus relaciones se hayan cargado con antelación; el día que alguien cambie una
por carga perezosa, la tarea reventaría fuera del ciclo de la petición, donde
además el error no llega al usuario.

Ninguna deja escapar una excepción: un fallo al enviar un correo no puede
tumbar el proceso ni dejar constancia solo en la consola.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.detalle_venta import DetalleVenta
from app.models.pqr import PQR
from app.models.venta import Venta
from app.services import email as email_service

logger = logging.getLogger("oleo_lienzo.tareas")


async def confirmar_compra(venta_id: int) -> None:
    """Envía al cliente el correo de confirmación de una venta pagada."""
    try:
        async with AsyncSessionLocal() as db:
            venta = (
                (
                    await db.execute(
                        select(Venta)
                        .where(Venta.id == venta_id)
                        .options(
                            selectinload(Venta.detalles).selectinload(DetalleVenta.obra),
                            selectinload(Venta.detalles).selectinload(DetalleVenta.servicio),
                            selectinload(Venta.factura),
                        )
                    )
                )
                .unique()
                .scalar_one_or_none()
            )
            if venta is None:
                logger.warning("La venta %s ya no existe; no se envía el correo.", venta_id)
                return

            numero_factura = venta.factura.numero if venta.factura else None
            await email_service.enviar_confirmacion_compra(venta, numero_factura)

    except Exception:
        # La tarea corre fuera de la petición: si no se captura aquí, la
        # excepción se pierde sin que nadie se entere.
        logger.exception("Falló la tarea de confirmación de la venta %s", venta_id)


async def avisar_pqr_radicada(pqr_id: int) -> None:
    """Acusa recibo de una PQR recién radicada."""
    try:
        async with AsyncSessionLocal() as db:
            pqr = await db.get(PQR, pqr_id)
            if pqr is None:
                logger.warning("La PQR %s ya no existe; no se envía el acuse.", pqr_id)
                return
            await email_service.enviar_pqr_radicada(pqr)

    except Exception:
        logger.exception("Falló la tarea de acuse de la PQR %s", pqr_id)


async def avisar_pqr_respondida(pqr_id: int) -> None:
    """Avisa al cliente de que su PQR ya tiene respuesta."""
    try:
        async with AsyncSessionLocal() as db:
            pqr = await db.get(PQR, pqr_id)
            if pqr is None:
                logger.warning("La PQR %s ya no existe; no se envía el aviso.", pqr_id)
                return
            await email_service.enviar_pqr_respondida(pqr)

    except Exception:
        logger.exception("Falló la tarea de aviso de la PQR %s", pqr_id)
