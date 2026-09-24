"""Envío de correos electrónicos en HTML.

Los correos se maquetan con tablas y estilos en línea porque es lo único que
renderizan de forma fiable Gmail, Outlook y el resto de clientes. El logotipo
se dibuja con CSS en lugar de adjuntar una imagen: los clientes de correo
bloquean las imágenes remotas por defecto.

El envío es bloqueante (smtplib), así que se ejecuta en un hilo aparte para no
frenar el bucle de eventos. Nunca propaga excepciones: un fallo de correo no
puede tumbar un registro ni una compra.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import get_settings
from app.core.dinero import formato_cop

settings = get_settings()
logger = logging.getLogger("oleo_lienzo.email")

# ── Paleta, alineada con la identidad visual del frontend ────────────────
VERDE = "#2b3a2f"
VERDE_OSCURO = "#1c2620"
ORO = "#c9a227"
PAPEL = "#f7f4ec"
TINTA = "#1c1b19"
SIENA = "#a64b2a"


def _plantilla(
    titulo: str, saludo: str, cuerpo_html: str, cta: tuple[str, str] | None = None
) -> str:
    """Envuelve el contenido en la maqueta corporativa."""
    boton = ""
    if cta:
        texto, url = cta
        boton = f"""
        <tr><td style="padding:8px 32px 28px 32px;">
          <a href="{url}" style="display:inline-block;background:{VERDE};color:{PAPEL};
             text-decoration:none;padding:14px 28px;border-radius:6px;
             font-family:Arial,Helvetica,sans-serif;font-size:13px;font-weight:bold;
             letter-spacing:.06em;text-transform:uppercase;">{texto}</a>
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title></head>
<body style="margin:0;padding:0;background:#e8e3d5;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#e8e3d5;padding:28px 12px;">
  <tr><td align="center">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="max-width:600px;background:{PAPEL};border-radius:12px;overflow:hidden;
                  box-shadow:0 2px 12px rgba(28,27,25,.12);">

      <!-- Cabecera con el logotipo -->
      <tr><td style="background:{VERDE};border-bottom:3px solid {ORO};padding:26px 32px;">
        <table role="presentation" cellpadding="0" cellspacing="0"><tr>
          <td style="padding-right:12px;">
            <div style="width:40px;height:40px;border:2px solid {ORO};border-radius:50%;
                        color:{ORO};font-family:Georgia,serif;font-style:italic;
                        font-size:22px;line-height:40px;text-align:center;">O</div>
          </td>
          <td style="font-family:Georgia,serif;font-size:21px;color:{PAPEL};">
            Óleo<span style="color:{ORO};font-style:italic;">&amp;</span>Lienzo
          </td>
        </tr></table>
      </td></tr>

      <!-- Contenido -->
      <tr><td style="padding:32px 32px 8px 32px;font-family:Arial,Helvetica,sans-serif;">
        <h1 style="margin:0 0 6px 0;font-family:Georgia,serif;font-size:23px;
                   color:{TINTA};font-weight:normal;">{titulo}</h1>
        <p style="margin:0 0 18px 0;font-size:15px;color:{TINTA};">{saludo}</p>
        <div style="font-size:14px;line-height:1.65;color:#3d3b37;">{cuerpo_html}</div>
      </td></tr>
      {boton}

      <!-- Pie -->
      <tr><td style="background:{VERDE_OSCURO};padding:22px 32px;
                     font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#c9c4b6;">
        <p style="margin:0 0 4px 0;color:{ORO};font-weight:bold;">{settings.empresa_nombre}</p>
        <p style="margin:0 0 2px 0;">NIT {settings.empresa_nit}</p>
        <p style="margin:0 0 2px 0;">{settings.empresa_direccion} · {settings.empresa_ciudad}</p>
        <p style="margin:0 0 10px 0;">{settings.empresa_telefono} · {settings.empresa_email}</p>
        <p style="margin:0;color:#8b877d;font-size:11px;">
          Este mensaje se generó automáticamente; por favor no respondas a este correo.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table></body></html>"""


def _tabla_items(detalles: list, subtotal, descuento, impuestos, total) -> str:
    """Tabla de líneas con el desglose económico, para compras y facturas."""
    filas = "".join(
        f"""<tr>
          <td style="padding:9px 6px;border-bottom:1px solid #e3ded1;font-size:13px;">
            {d.descripcion}</td>
          <td style="padding:9px 6px;border-bottom:1px solid #e3ded1;font-size:13px;
                     text-align:center;">{d.cantidad}</td>
          <td style="padding:9px 6px;border-bottom:1px solid #e3ded1;font-size:13px;
                     text-align:right;">{formato_cop(d.precio_unitario)}</td>
          <td style="padding:9px 6px;border-bottom:1px solid #e3ded1;font-size:13px;
                     text-align:right;font-weight:bold;">{formato_cop(d.subtotal)}</td>
        </tr>"""
        for d in detalles
    )

    def total_fila(etiqueta: str, valor, destacado: bool = False) -> str:
        peso = "bold" if destacado else "normal"
        color = VERDE if destacado else "#3d3b37"
        tam = "15px" if destacado else "13px"
        return f"""<tr>
          <td colspan="3" style="padding:6px;text-align:right;font-size:{tam};
                                 color:{color};font-weight:{peso};">{etiqueta}</td>
          <td style="padding:6px;text-align:right;font-size:{tam};color:{color};
                     font-weight:{peso};">{formato_cop(valor)}</td></tr>"""

    descuento_fila = total_fila("Descuento", -abs(float(descuento))) if float(descuento) else ""

    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="margin:16px 0;border-collapse:collapse;">
      <tr style="background:{VERDE};color:{PAPEL};">
        <th style="padding:9px 6px;text-align:left;font-size:11px;letter-spacing:.06em;
                   text-transform:uppercase;">Descripción</th>
        <th style="padding:9px 6px;text-align:center;font-size:11px;letter-spacing:.06em;
                   text-transform:uppercase;">Cant.</th>
        <th style="padding:9px 6px;text-align:right;font-size:11px;letter-spacing:.06em;
                   text-transform:uppercase;">V. unitario</th>
        <th style="padding:9px 6px;text-align:right;font-size:11px;letter-spacing:.06em;
                   text-transform:uppercase;">Subtotal</th>
      </tr>
      {filas}
      {total_fila("Subtotal", subtotal)}
      {descuento_fila}
      {total_fila(f"IVA ({settings.iva_porcentaje:g}%)", impuestos)}
      {total_fila("Total", total, destacado=True)}
    </table>"""


# ── Envío ────────────────────────────────────────────────────────────────
def _enviar_sincrono(destinatario: str, asunto: str, html: str) -> None:
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((settings.email_from_name, settings.email_from))
    mensaje["To"] = destinatario
    # Alternativa en texto plano para clientes que no renderizan HTML.
    mensaje.set_content(
        "Este mensaje requiere un lector de correo con soporte HTML.\n"
        f"{settings.empresa_nombre} · {settings.empresa_email}"
    )
    mensaje.add_alternative(html, subtype="html")

    with smtplib.SMTP(
        settings.email_host, settings.email_port, timeout=settings.email_timeout_seconds
    ) as servidor:
        if settings.email_use_tls:
            servidor.starttls()
        servidor.login(settings.email_user, settings.email_password)
        servidor.send_message(mensaje)


async def enviar_email(destinatario: str, asunto: str, html: str) -> bool:
    """Envía un correo. Devuelve False si no se pudo (nunca lanza excepción)."""
    if not settings.email_configurado:
        logger.info(
            "Correo no enviado a %s (%r): SMTP sin configurar en .env", destinatario, asunto
        )
        return False
    try:
        await asyncio.to_thread(_enviar_sincrono, destinatario, asunto, html)
        logger.info("Correo enviado a %s: %s", destinatario, asunto)
        return True
    except Exception as exc:
        logger.warning("No se pudo enviar el correo a %s: %s", destinatario, exc)
        return False


# ── Correos concretos del negocio ────────────────────────────────────────
async def enviar_bienvenida(nombre: str, email: str) -> bool:
    html = _plantilla(
        "Te damos la bienvenida",
        f"Hola {nombre},",
        "<p>Tu cuenta en <strong>Óleo &amp; Lienzo</strong> quedó creada correctamente. "
        "Ya puedes explorar la colección, guardar tus piezas favoritas y hacer "
        "seguimiento a tus pedidos desde tu panel.</p>"
        "<p>Cada obra de la galería es original, viene firmada por su artista e "
        "incluye certificado de autenticidad.</p>",
        cta=("Ver la colección", settings.frontend_url),
    )
    return await enviar_email(email, "Bienvenido a Óleo & Lienzo", html)


async def enviar_recuperacion(nombre: str, email: str, token: str) -> bool:
    url = f"{settings.frontend_url}/restablecer?token={token}"
    html = _plantilla(
        "Restablece tu contraseña",
        f"Hola {nombre},",
        "<p>Recibimos una solicitud para restablecer la contraseña de tu cuenta. "
        "Pulsa el botón para crear una nueva.</p>"
        f"<p style='color:{SIENA};'><strong>El enlace caduca en "
        f"{settings.reset_token_expire_minutes} minutos.</strong></p>"
        "<p>Si no fuiste tú, ignora este mensaje: tu contraseña actual seguirá "
        "funcionando con normalidad.</p>",
        cta=("Crear nueva contraseña", url),
    )
    return await enviar_email(email, "Recuperación de contraseña · Óleo & Lienzo", html)


async def enviar_confirmacion_compra(venta, numero_factura: str | None = None) -> bool:
    referencia = f"<p>Factura <strong>{numero_factura}</strong></p>" if numero_factura else ""
    cuerpo = (
        f"<p>Registramos tu compra <strong>{venta.numero}</strong>. "
        "Este es el detalle:</p>"
        + _tabla_items(
            venta.detalles, venta.subtotal, venta.descuento, venta.impuestos, venta.total
        )
        + referencia
        + "<p>Prepararemos tu pedido y te avisaremos en cuanto salga hacia tu dirección.</p>"
    )
    html = _plantilla(
        "Confirmación de compra",
        f"Hola {venta.cliente.nombre},",
        cuerpo,
        cta=("Ver mis pedidos", f"{settings.frontend_url}/panel/cliente"),
    )
    return await enviar_email(
        venta.cliente.email, f"Compra confirmada {venta.numero} · Óleo & Lienzo", html
    )


ETIQUETAS_ESTADO = {
    "pendiente": "está pendiente de confirmación",
    "confirmado": "fue confirmado",
    "entregado": "fue entregado",
    "cancelado": "fue cancelado",
}


async def enviar_cambio_estado_pedido(nombre: str, email: str, pedido_id: int, estado: str) -> bool:
    descripcion = ETIQUETAS_ESTADO.get(estado, f"cambió a «{estado}»")
    html = _plantilla(
        "Actualización de tu pedido",
        f"Hola {nombre},",
        f"<p>Tu pedido <strong>#{pedido_id}</strong> {descripcion}.</p>"
        "<p>Puedes consultar el detalle completo y el histórico desde tu panel.</p>",
        cta=("Ver mis pedidos", f"{settings.frontend_url}/panel/cliente"),
    )
    return await enviar_email(email, f"Pedido #{pedido_id}: {estado} · Óleo & Lienzo", html)


async def enviar_pqr_radicada(pqr) -> bool:
    html = _plantilla(
        "Recibimos tu solicitud",
        f"Hola {pqr.contacto_nombre},",
        f"<p>Radicamos tu {pqr.tipo.value} con el número "
        f"<strong>{pqr.radicado}</strong>.</p>"
        f"<p><strong>Asunto:</strong> {pqr.asunto}</p>"
        "<p>Nuestro equipo la revisará y te responderá a este mismo correo. "
        "Guarda el número de radicado para hacer seguimiento.</p>",
    )
    return await enviar_email(
        pqr.contacto_email, f"PQR {pqr.radicado} radicada · Óleo & Lienzo", html
    )


async def enviar_pqr_respondida(pqr) -> bool:
    html = _plantilla(
        "Respondimos tu solicitud",
        f"Hola {pqr.contacto_nombre},",
        f"<p>Tu {pqr.tipo.value} <strong>{pqr.radicado}</strong> ya tiene respuesta:</p>"
        f"<blockquote style='margin:14px 0;padding:12px 16px;background:#efeade;"
        f"border-left:3px solid {ORO};font-size:14px;'>{pqr.respuesta}</blockquote>"
        "<p>Si necesitas ampliar la información, puedes responder radicando una "
        "nueva solicitud.</p>",
    )
    return await enviar_email(
        pqr.contacto_email, f"Respuesta a tu PQR {pqr.radicado} · Óleo & Lienzo", html
    )
