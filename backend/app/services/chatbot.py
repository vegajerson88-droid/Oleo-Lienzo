"""Chatbot de atención al cliente con Inteligencia Artificial (Groq).

La clave de API se lee de la variable de entorno GROQ_API_KEY y nunca aparece
en el código ni se devuelve al frontend.

Si Groq no está configurado, agota el tiempo de espera o falla, el servicio
degrada a un modo de respaldo basado en reglas: responde lo esencial con datos
reales del catálogo y lo declara abiertamente (`generado_por_ia: false`) en
lugar de fingir que la IA contestó.
"""

from __future__ import annotations

import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dinero import formato_cop
from app.models.chat import Mensaje, RolMensaje
from app.models.obra import Obra
from app.models.servicio import Servicio

settings = get_settings()
logger = logging.getLogger("oleo_lienzo.chatbot")

MAX_OBRAS_CONTEXTO = 12

INSTRUCCIONES = """Eres el asistente virtual de «Óleo & Lienzo», una galería de arte \
colombiana que vende pinturas originales y ofrece servicios de enmarcado, \
restauración y envío asegurado.

Tu trabajo es:
- Resolver preguntas frecuentes sobre la galería, los envíos y las compras.
- Orientar sobre las obras y los servicios disponibles usando SOLO el catálogo \
que se te entrega más abajo.
- Guiar el proceso de compra: el cliente se registra, inicia sesión, añade obras \
a su pedido desde el panel y paga con tarjeta.
- Recibir peticiones, quejas y reclamos (PQR). Si el usuario quiere radicar una, \
explícale que puede hacerlo desde la sección PQR de su panel o pedirte que se la \
radiques, y pide asunto y descripción.

Reglas que no puedes romper:
- No inventes obras, precios, artistas ni plazos. Si un dato no está en el \
catálogo, di que no lo tienes y ofrece poner en contacto con la galería.
- Responde siempre en español, en tono cercano y profesional.
- Sé breve: máximo tres párrafos cortos.
- Nunca pidas ni menciones contraseñas, números de tarjeta ni datos bancarios."""

DATOS_EMPRESA = f"""Datos de la galería:
- Nombre: {settings.empresa_nombre}
- Dirección: {settings.empresa_direccion}, {settings.empresa_ciudad}
- Teléfono: {settings.empresa_telefono}
- Correo: {settings.empresa_email}
- Horario: martes a sábado, 10:00 a.m. a 6:00 p.m.
- IVA aplicado a las ventas: {settings.iva_porcentaje:g}%"""


async def construir_contexto_catalogo(db: AsyncSession) -> str:
    """Arma el catálogo real que se le pasa al modelo como contexto."""
    obras = list(
        (
            await db.execute(
                select(Obra)
                .where(Obra.disponible.is_(True))
                .order_by(Obra.id)
                .limit(MAX_OBRAS_CONTEXTO)
            )
        )
        .scalars()
        .all()
    )
    servicios = list(
        (await db.execute(select(Servicio).where(Servicio.activo.is_(True)))).scalars().all()
    )

    lineas_obras = [
        f"- «{o.titulo}» de {o.artista} ({o.anio}, {o.tecnica}): {formato_cop(o.precio)}"
        for o in obras
    ] or ["- (sin obras disponibles en este momento)"]
    lineas_servicios = [
        f"- {s.nombre}: {formato_cop(s.precio)} — {s.descripcion}" for s in servicios
    ] or ["- (sin servicios activos en este momento)"]

    return (
        f"{DATOS_EMPRESA}\n\nObras disponibles:\n"
        + "\n".join(lineas_obras)
        + "\n\nServicios disponibles:\n"
        + "\n".join(lineas_servicios)
    )


def _a_mensajes_api(historial: list[Mensaje]) -> list[dict]:
    equivalencias = {
        RolMensaje.usuario: "user",
        RolMensaje.asistente: "assistant",
        RolMensaje.sistema: "system",
    }
    return [{"role": equivalencias.get(m.rol, "user"), "content": m.contenido} for m in historial]


# ── Respaldo sin IA ──────────────────────────────────────────────────────
REGLAS_RESPALDO: list[tuple[tuple[str, ...], str]] = [
    (
        ("horario", "abren", "abierto", "cierran", "visita"),
        "Abrimos de martes a sábado, de 10:00 a.m. a 6:00 p.m., en "
        f"{settings.empresa_direccion}, {settings.empresa_ciudad}.",
    ),
    (
        ("envio", "envío", "domicilio", "entrega", "despacho"),
        "Hacemos envíos asegurados a todo el país. Empacamos cada lienzo con "
        "materiales especializados y el servicio de envío se añade al pedido.",
    ),
    (
        ("pago", "pagar", "tarjeta", "transferencia", "factura"),
        "Puedes pagar con tarjeta desde tu panel de cliente. Al confirmarse el "
        "pago emitimos la factura, que queda disponible para descargar en PDF.",
    ),
    (
        ("pqr", "queja", "reclamo", "peticion", "petición", "sugerencia"),
        "Puedes radicar tu PQR desde la sección «PQR» de tu panel de cliente. "
        "Te entregamos un número de radicado para hacer seguimiento y te "
        "respondemos al correo registrado.",
    ),
    (
        ("compr", "pedido", "adquirir", "carrito"),
        "Para comprar: crea tu cuenta, inicia sesión y desde tu panel añade las "
        "obras o servicios a un pedido. Al confirmarlo generamos la venta y "
        "podrás pagarla con tarjeta.",
    ),
    (
        ("autentic", "certificado", "original", "garantia", "garantía"),
        "Todas nuestras piezas son originales, vienen firmadas por su artista e "
        "incluyen certificado de autenticidad.",
    ),
    (
        ("enmarc", "restaur"),
        "Ofrecemos enmarcado personalizado a medida y restauración básica. "
        "Puedes añadirlos a tu pedido como servicios.",
    ),
    (
        ("contacto", "telefono", "teléfono", "correo", "email", "whatsapp"),
        f"Puedes escribirnos a {settings.empresa_email} o llamarnos al "
        f"{settings.empresa_telefono}. También tienes el botón de WhatsApp en la "
        "esquina de la pantalla.",
    ),
]


def responder_sin_ia(mensaje: str, catalogo: str) -> str:
    """Respuesta por reglas cuando la IA no está disponible."""
    texto = mensaje.lower()

    for claves, respuesta in REGLAS_RESPALDO:
        if any(clave in texto for clave in claves):
            return respuesta

    if any(c in texto for c in ("obra", "pintura", "cuadro", "catalogo", "catálogo", "precio")):
        muestra = "\n".join(catalogo.split("Obras disponibles:")[-1].strip().splitlines()[:5])
        return f"Estas son algunas de las obras disponibles:\n{muestra}"

    if any(c in texto for c in ("hola", "buenas", "buenos dias", "buenos días", "saludos")):
        return (
            "¡Hola! Soy el asistente de Óleo & Lienzo. Puedo contarte sobre "
            "nuestras obras, los servicios de enmarcado y envío, el proceso de "
            "compra o ayudarte a radicar una PQR. ¿Qué necesitas?"
        )

    return (
        "Puedo ayudarte con información sobre nuestras obras, los servicios de "
        "enmarcado y envío, el proceso de compra o la radicación de PQR. "
        f"Si prefieres atención personalizada, escríbenos a {settings.empresa_email}."
    )


# ── Llamada a Groq ───────────────────────────────────────────────────────
async def generar_respuesta(mensaje_usuario: str, historial: list[Mensaje], catalogo: str) -> dict:
    """Genera la respuesta del asistente.

    Devuelve siempre un dict con `respuesta`, `generado_por_ia`, `modelo` y
    `detalle`; nunca lanza excepción hacia el router.
    """
    if not settings.groq_configurado:
        return {
            "respuesta": responder_sin_ia(mensaje_usuario, catalogo),
            "generado_por_ia": False,
            "modelo": None,
            "detalle": "GROQ_API_KEY no está configurada; respondió el modo local.",
        }

    mensajes = [
        {"role": "system", "content": f"{INSTRUCCIONES}\n\n--- CATÁLOGO ACTUAL ---\n{catalogo}"},
        *_a_mensajes_api(historial),
        {"role": "user", "content": mensaje_usuario},
    ]

    try:
        async with httpx.AsyncClient(timeout=settings.groq_timeout_seconds) as cliente:
            respuesta = await cliente.post(
                f"{settings.groq_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": mensajes,
                    "max_tokens": settings.groq_max_tokens,
                    "temperature": 0.6,
                },
            )
            respuesta.raise_for_status()
            contenido = respuesta.json()["choices"][0]["message"]["content"].strip()
            return {
                "respuesta": contenido,
                "generado_por_ia": True,
                "modelo": settings.groq_model,
                "detalle": None,
            }

    except httpx.TimeoutException:
        motivo = f"Groq no respondió en {settings.groq_timeout_seconds:g} segundos."
    except httpx.HTTPStatusError as exc:
        motivo = f"Groq devolvió HTTP {exc.response.status_code}."
    except (httpx.RequestError, KeyError, ValueError) as exc:
        motivo = f"No se pudo contactar con Groq: {type(exc).__name__}."

    logger.warning("Chatbot degradado al modo local: %s", motivo)
    return {
        "respuesta": responder_sin_ia(mensaje_usuario, catalogo),
        "generado_por_ia": False,
        "modelo": None,
        "detalle": f"{motivo} Se respondió con el modo local.",
    }


async def comprobar_disponibilidad() -> dict:
    """Comprueba de verdad si Groq responde. Lo usa el endpoint de diagnóstico."""
    if not settings.groq_configurado:
        return {"disponible": False, "detalle": "GROQ_API_KEY no configurada en .env."}
    try:
        async with httpx.AsyncClient(timeout=settings.groq_timeout_seconds) as cliente:
            respuesta = await cliente.post(
                f"{settings.groq_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                },
            )
            respuesta.raise_for_status()
        return {"disponible": True, "detalle": f"Modelo {settings.groq_model} operativo."}
    except Exception as exc:
        return {"disponible": False, "detalle": f"{type(exc).__name__}: {exc}"}
