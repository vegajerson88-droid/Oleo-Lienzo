"""Pasarela de pago con Stripe: checkout y webhook."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.crud import venta as venta_crud
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.common import RESPUESTA_404, RESPUESTA_422, RESPUESTAS_AUTH
from app.models.pago import EstadoPago, Pago
from app.models.usuario import Usuario
from app.models.venta import EstadoVenta
from app.schemas.common import MensajeRespuesta
from app.schemas.pago import CheckoutRequest, CheckoutResponse
from app.services import email as email_service
from app.services import pagos as pagos_service

settings = get_settings()
logger = logging.getLogger("oleo_lienzo.pagos")
router = APIRouter(prefix="/pagos", tags=["Pagos (Stripe)"])


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Crear la sesión de pago de una venta",
    description=(
        "Crea una sesión de **Stripe Checkout** y devuelve la URL donde el "
        "cliente introduce los datos de su tarjeta.\n\n"
        "**Seguridad.** Los datos de tarjeta se escriben en una página alojada "
        "por Stripe, nunca en nuestro frontend ni en nuestro servidor. De la "
        "transacción solo guardamos identificadores y estado: ningún número de "
        "tarjeta, CVV ni fecha de expiración llega a nuestra base de datos.\n\n"
        "El importe se construye a partir de la venta guardada (líneas, "
        "descuento e IVA), no de lo que envíe el navegador.\n\n"
        "Devuelve 422 si Stripe no está configurado o la venta no se puede cobrar."
    ),
    responses={**RESPUESTAS_AUTH, **RESPUESTA_404, **RESPUESTA_422},
)
async def crear_checkout(
    data: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    try:
        venta = await venta_crud.get_by_id(db, data.venta_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    if usuario.rol.nombre == "cliente" and venta.cliente_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta venta no es tuya.")
    if venta.estado != EstadoVenta.pendiente_pago:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La venta {venta.numero} está en estado '{venta.estado.value}' "
            "y no admite un pago nuevo.",
        )

    try:
        sesion = await pagos_service.crear_sesion_checkout(
            venta,
            exito_url=f"{settings.frontend_url}/panel/cliente?pago=exitoso&venta={venta.numero}",
            cancelado_url=f"{settings.frontend_url}/panel/cliente?pago=cancelado",
        )
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    db.add(
        Pago(
            venta_id=venta.id,
            proveedor="stripe",
            referencia_externa=sesion["session_id"],
            estado=EstadoPago.pendiente,
            monto=venta.total,
            moneda=settings.stripe_currency.upper(),
        )
    )
    await db.commit()
    return CheckoutResponse(**sesion)


@router.post(
    "/webhook",
    response_model=MensajeRespuesta,
    summary="Webhook de Stripe",
    description=(
        "Recibe los eventos de Stripe y actualiza el estado de la venta y del "
        "pago.\n\n"
        "**No lleva autenticación JWT a propósito**: quien llama es Stripe, no "
        "un usuario. La autenticidad se comprueba verificando la **firma "
        "criptográfica** de la cabecera `Stripe-Signature` contra "
        "`STRIPE_WEBHOOK_SECRET`. Sin esa verificación, cualquiera podría "
        "fingir que un pago se completó.\n\n"
        "La operación es **idempotente**: Stripe reintenta los eventos y "
        "volver a procesar el mismo no altera nada.\n\n"
        "Eventos atendidos: `checkout.session.completed`, "
        "`checkout.session.expired` y `charge.refunded`."
    ),
    responses={400: {"description": "Firma inválida o cuerpo no verificable."}},
)
async def webhook_stripe(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    try:
        evento = pagos_service.verificar_evento_webhook(payload, stripe_signature)
    except DomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.detail)

    tipo = evento.get("type")
    venta_id = pagos_service.extraer_venta_id(evento)
    if venta_id is None:
        logger.info("Evento %s sin referencia a una venta; se ignora.", tipo)
        return MensajeRespuesta(mensaje="Evento recibido sin venta asociada.")

    objeto = evento.get("data", {}).get("object", {})
    pago = await _pago_de_la_sesion(db, objeto.get("id"))

    if tipo == "checkout.session.completed":
        if pago:
            pago.estado = EstadoPago.aprobado
            pago.payment_intent = objeto.get("payment_intent")
        try:
            venta = await venta_crud.marcar_pagada_por_referencia(db, venta_id)
        except DomainError:
            venta = None
        await db.commit()
        if venta is not None:
            background_tasks.add_task(
                email_service.enviar_confirmacion_compra, venta, venta.factura_numero
            )
        return MensajeRespuesta(mensaje=f"Pago confirmado para la venta {venta_id}.")

    if tipo == "checkout.session.expired" and pago:
        pago.estado = EstadoPago.fallido
        pago.detalle = "La sesión de pago expiró sin completarse."
        await db.commit()
        return MensajeRespuesta(mensaje="Sesión de pago expirada.")

    if tipo == "charge.refunded" and pago:
        pago.estado = EstadoPago.reembolsado
        await db.commit()
        return MensajeRespuesta(mensaje="Reembolso registrado.")

    return MensajeRespuesta(mensaje=f"Evento '{tipo}' recibido.")


async def _pago_de_la_sesion(db: AsyncSession, session_id: str | None) -> Pago | None:
    if not session_id:
        return None
    from sqlalchemy import select

    consulta = select(Pago).where(Pago.referencia_externa == session_id)
    return (await db.execute(consulta)).scalar_one_or_none()


@router.get(
    "/configuracion",
    summary="Clave pública de Stripe",
    description=(
        "Devuelve la clave **publicable** para que el frontend pueda inicializar "
        "Stripe. Es la única clave pensada para exponerse; la secreta nunca "
        "sale del servidor."
    ),
)
async def configuracion_pagos():
    return {
        "configurado": settings.stripe_configurado,
        "publishable_key": settings.stripe_publishable_key,
        "moneda": settings.stripe_currency.upper(),
    }
