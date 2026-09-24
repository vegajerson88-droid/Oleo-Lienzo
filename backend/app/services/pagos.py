"""Pasarela de pago con Stripe.

Se usa Stripe Checkout: el cliente introduce los datos de su tarjeta en una
página alojada por Stripe, nunca en nuestro frontend ni en nuestro servidor.
De la transacción solo guardamos identificadores (`session_id`,
`payment_intent`) y el estado. Ningún número de tarjeta, CVV ni fecha de
expiración toca nuestra base de datos.

Las claves viven en variables de entorno; la publicable es la única que se
expone al navegador, que es precisamente para lo que existe.
"""
from __future__ import annotations

import asyncio
import logging

import stripe

from app.core.config import get_settings
from app.core.dinero import a_decimal
from app.core.exceptions import BusinessRuleError

settings = get_settings()
logger = logging.getLogger("oleo_lienzo.pagos")

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key

# Monedas que Stripe maneja sin decimales: el importe va en unidades enteras.
MONEDAS_SIN_DECIMALES = {
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga",
    "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf",
}


def a_unidad_minima(monto, moneda: str) -> int:
    """Convierte un importe a la unidad mínima que espera Stripe."""
    valor = a_decimal(monto)
    if moneda.lower() in MONEDAS_SIN_DECIMALES:
        return int(valor)
    return int(valor * 100)


def _crear_sesion_sincrona(venta, exito_url: str, cancelado_url: str) -> stripe.checkout.Session:
    moneda = settings.stripe_currency.lower()
    lineas = [
        {
            "price_data": {
                "currency": moneda,
                "product_data": {"name": d.descripcion[:120]},
                "unit_amount": a_unidad_minima(d.precio_unitario, moneda),
            },
            "quantity": d.cantidad,
        }
        for d in venta.detalles
    ]

    # El IVA y el descuento global se añaden como líneas propias para que el
    # total cobrado coincida exactamente con el de la venta.
    if float(venta.descuento):
        lineas.append(
            {
                "price_data": {
                    "currency": moneda,
                    "product_data": {"name": "Descuento aplicado"},
                    "unit_amount": -a_unidad_minima(venta.descuento, moneda),
                },
                "quantity": 1,
            }
        )
    if float(venta.impuestos):
        lineas.append(
            {
                "price_data": {
                    "currency": moneda,
                    "product_data": {"name": f"IVA ({settings.iva_porcentaje:g}%)"},
                    "unit_amount": a_unidad_minima(venta.impuestos, moneda),
                },
                "quantity": 1,
            }
        )

    return stripe.checkout.Session.create(
        mode="payment",
        line_items=lineas,
        # La referencia permite reconciliar el webhook con nuestra venta.
        client_reference_id=str(venta.id),
        metadata={"venta_id": str(venta.id), "numero_venta": venta.numero},
        customer_email=venta.cliente.email if venta.cliente else None,
        success_url=exito_url,
        cancel_url=cancelado_url,
    )


async def crear_sesion_checkout(venta, exito_url: str, cancelado_url: str) -> dict:
    """Crea la sesión de pago y devuelve la URL alojada por Stripe."""
    if not settings.stripe_configurado:
        raise BusinessRuleError(
            "La pasarela de pago no está configurada. "
            "Define STRIPE_SECRET_KEY en el archivo .env."
        )
    if not venta.detalles:
        raise BusinessRuleError("La venta no tiene líneas que cobrar.")

    try:
        sesion = await asyncio.to_thread(
            _crear_sesion_sincrona, venta, exito_url, cancelado_url
        )
    except stripe.StripeError as exc:
        logger.warning("Stripe rechazó la creación de la sesión: %s", exc)
        raise BusinessRuleError(f"Stripe no pudo crear la sesión de pago: {exc.user_message or exc}")

    return {
        "checkout_url": sesion.url,
        "session_id": sesion.id,
        "publishable_key": settings.stripe_publishable_key,
    }


def verificar_evento_webhook(payload: bytes, firma: str | None) -> stripe.Event:
    """Verifica la firma del webhook y devuelve el evento.

    Sin esta comprobación cualquiera podría enviarnos un POST fingiendo que un
    pago se completó, así que la firma es obligatoria.
    """
    if not settings.stripe_webhook_secret:
        raise BusinessRuleError(
            "STRIPE_WEBHOOK_SECRET no está configurado; no se puede verificar el webhook."
        )
    if not firma:
        raise BusinessRuleError("Falta la cabecera Stripe-Signature.")
    try:
        return stripe.Webhook.construct_event(
            payload, firma, settings.stripe_webhook_secret
        )
    except ValueError:
        raise BusinessRuleError("El cuerpo del webhook no es un JSON válido.")
    except stripe.SignatureVerificationError:
        raise BusinessRuleError("La firma del webhook no es válida.")


def extraer_venta_id(evento: stripe.Event) -> int | None:
    """Saca el id de nuestra venta del evento de Stripe."""
    objeto = evento.get("data", {}).get("object", {})
    referencia = objeto.get("client_reference_id") or objeto.get("metadata", {}).get("venta_id")
    try:
        return int(referencia) if referencia else None
    except (TypeError, ValueError):
        return None


async def comprobar_disponibilidad() -> dict:
    """Comprueba que la clave de Stripe funciona. Lo usa el diagnóstico."""
    if not settings.stripe_configurado:
        return {"disponible": False, "detalle": "STRIPE_SECRET_KEY no configurada en .env."}
    try:
        await asyncio.to_thread(stripe.Balance.retrieve)
        return {"disponible": True, "detalle": "Credenciales de Stripe válidas."}
    except Exception as exc:
        return {"disponible": False, "detalle": f"{type(exc).__name__}: {exc}"}
