"""Generación de documentos PDF: facturas de venta y reporte diario.

Se usa la API de bajo nivel de ReportLab (canvas) para controlar el diseño al
milímetro: cabecera corporativa, datos fiscales, tabla con franjas alternas,
bloque de totales y pie de página numerado.

Los PDF se construyen en memoria (BytesIO) y se devuelven como bytes; no se
escribe nada en disco.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.core.config import get_settings
from app.core.dinero import a_decimal, formato_cop

settings = get_settings()

# Paleta corporativa, la misma del sitio y de los correos.
VERDE = colors.HexColor("#2b3a2f")
VERDE_OSCURO = colors.HexColor("#1c2620")
ORO = colors.HexColor("#c9a227")
PAPEL = colors.HexColor("#f7f4ec")
TINTA = colors.HexColor("#1c1b19")
GRIS = colors.HexColor("#6b675f")
FRANJA = colors.HexColor("#efeade")

ESTADOS_COLOR = {
    "pagada": colors.HexColor("#2f6b3a"),
    "emitida": colors.HexColor("#8a6d1f"),
    "pendiente_pago": colors.HexColor("#8a6d1f"),
    "anulada": colors.HexColor("#a64b2a"),
    "reembolsada": colors.HexColor("#a64b2a"),
}


def _logo(c: canvas.Canvas, x: float, y: float, radio: float = 7 * mm) -> None:
    """Dibuja el monograma de la galería: círculo dorado con una O."""
    c.setStrokeColor(ORO)
    c.setLineWidth(1.4)
    c.circle(x + radio, y + radio, radio, stroke=1, fill=0)
    c.setFillColor(ORO)
    c.setFont("Times-Italic", 13)
    c.drawCentredString(x + radio, y + radio - 4.4, "O")


def _cabecera(c: canvas.Canvas, ancho: float, alto: float, titulo: str) -> float:
    """Banda superior con el logo y los datos fiscales. Devuelve la Y libre."""
    altura_banda = 34 * mm
    tope = alto - altura_banda

    c.setFillColor(VERDE)
    c.rect(0, tope, ancho, altura_banda, stroke=0, fill=1)
    c.setFillColor(ORO)
    c.rect(0, tope - 1.2 * mm, ancho, 1.2 * mm, stroke=0, fill=1)

    _logo(c, 16 * mm, tope + 12 * mm)

    c.setFillColor(PAPEL)
    c.setFont("Times-Roman", 17)
    c.drawString(34 * mm, tope + 20 * mm, "Óleo & Lienzo")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#c9c4b6"))
    c.drawString(34 * mm, tope + 15 * mm, settings.empresa_nombre)
    c.drawString(34 * mm, tope + 11 * mm, f"NIT {settings.empresa_nit}")
    c.drawString(
        34 * mm, tope + 7 * mm,
        f"{settings.empresa_direccion} · {settings.empresa_ciudad}",
    )

    c.setFillColor(PAPEL)
    c.setFont("Helvetica-Bold", 13)
    c.drawRightString(ancho - 16 * mm, tope + 20 * mm, titulo.upper())
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#c9c4b6"))
    c.drawRightString(ancho - 16 * mm, tope + 14 * mm, settings.empresa_telefono)
    c.drawRightString(ancho - 16 * mm, tope + 10 * mm, settings.empresa_email)

    return tope - 10 * mm


def _pie(c: canvas.Canvas, ancho: float, pagina: int, nota: str = "") -> None:
    c.setStrokeColor(colors.HexColor("#d8d2c4"))
    c.setLineWidth(0.5)
    c.line(16 * mm, 16 * mm, ancho - 16 * mm, 16 * mm)
    c.setFont("Helvetica", 7)
    c.setFillColor(GRIS)
    c.drawString(16 * mm, 11 * mm, nota or f"{settings.empresa_nombre} · {settings.empresa_email}")
    c.drawRightString(ancho - 16 * mm, 11 * mm, f"Página {pagina}")


def _etiqueta_estado(c: canvas.Canvas, x: float, y: float, estado: str) -> None:
    """Píldora de color con el estado del documento."""
    texto = estado.replace("_", " ").upper()
    ancho_texto = c.stringWidth(texto, "Helvetica-Bold", 7.5)
    ancho_caja = ancho_texto + 10
    color = ESTADOS_COLOR.get(estado, GRIS)
    c.setFillColor(color)
    c.roundRect(x - ancho_caja, y - 2, ancho_caja, 12, 3, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(x - ancho_caja / 2, y + 1.5, texto)


def _bloque_datos(c: canvas.Canvas, x: float, y: float, titulo: str, lineas: list[str],
                  ancho: float) -> float:
    """Recuadro con un encabezado dorado y una lista de datos."""
    alto = 9 * mm + len(lineas) * 4.6 * mm
    c.setFillColor(FRANJA)
    c.roundRect(x, y - alto, ancho, alto, 2, stroke=0, fill=1)
    c.setFillColor(ORO)
    c.rect(x, y - 1.4 * mm, ancho, 1.4 * mm, stroke=0, fill=1)

    c.setFillColor(GRIS)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 4 * mm, y - 6 * mm, titulo.upper())
    c.setFillColor(TINTA)
    c.setFont("Helvetica", 8.5)
    cursor = y - 11 * mm
    for linea in lineas:
        c.drawString(x + 4 * mm, cursor, linea)
        cursor -= 4.6 * mm
    return y - alto


def generar_factura_pdf(factura) -> bytes:
    """Factura de venta en PDF, lista para imprimir o adjuntar."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    ancho, alto = A4
    c.setTitle(f"Factura {factura.numero}")
    c.setAuthor(settings.empresa_nombre)
    c.setSubject(f"Factura de venta {factura.numero}")

    y = _cabecera(c, ancho, alto, "Factura de venta")

    # Número, fecha y estado
    c.setFillColor(TINTA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(16 * mm, y - 6 * mm, f"N.º {factura.numero}")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(GRIS)
    emision = factura.fecha_emision.strftime("%d/%m/%Y %H:%M")
    c.drawString(16 * mm, y - 11.5 * mm, f"Fecha de emisión: {emision}")
    c.drawString(16 * mm, y - 16 * mm, f"Venta asociada: {factura.venta.numero}")
    _etiqueta_estado(c, ancho - 16 * mm, y - 8 * mm, factura.estado.value)

    # Datos del cliente y de la operación
    y_bloques = y - 24 * mm
    mitad = (ancho - 36 * mm) / 2
    _bloque_datos(
        c, 16 * mm, y_bloques, "Facturar a",
        [
            factura.cliente_nombre,
            factura.cliente_documento,
            factura.cliente_direccion,
            f"Tel. {factura.cliente_telefono}",
            factura.cliente_email,
        ],
        mitad - 2 * mm,
    )
    y_cursor = _bloque_datos(
        c, 16 * mm + mitad + 4 * mm, y_bloques, "Condiciones",
        [
            f"Método de pago: {factura.venta.metodo_pago.value.capitalize()}",
            f"Estado de la venta: {factura.venta.estado.value.replace('_', ' ')}",
            f"IVA aplicado: {float(factura.iva_porcentaje):g}%",
            f"Moneda: Peso colombiano (COP)",
            f"Emitida por: {settings.empresa_nombre}",
        ],
        mitad - 2 * mm,
    )

    # Tabla de líneas
    y_tabla = y_cursor - 12 * mm
    columnas = [16 * mm, 104 * mm, 126 * mm, 158 * mm, ancho - 16 * mm]

    c.setFillColor(VERDE)
    c.rect(16 * mm, y_tabla - 2 * mm, ancho - 32 * mm, 8 * mm, stroke=0, fill=1)
    c.setFillColor(PAPEL)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(columnas[0] + 3 * mm, y_tabla + 0.6 * mm, "DESCRIPCIÓN")
    c.drawCentredString(columnas[1] + 8 * mm, y_tabla + 0.6 * mm, "CANT.")
    c.drawRightString(columnas[3] - 3 * mm, y_tabla + 0.6 * mm, "V. UNITARIO")
    c.drawRightString(columnas[4] - 3 * mm, y_tabla + 0.6 * mm, "SUBTOTAL")

    fila = y_tabla - 9 * mm
    pagina = 1
    for indice, d in enumerate(factura.detalles):
        if fila < 60 * mm:  # salto de página conservando el bloque de totales
            _pie(c, ancho, pagina, f"Factura {factura.numero} · continúa")
            c.showPage()
            pagina += 1
            fila = _cabecera(c, ancho, alto, "Factura de venta") - 10 * mm

        if indice % 2 == 0:
            c.setFillColor(FRANJA)
            c.rect(16 * mm, fila - 2 * mm, ancho - 32 * mm, 7 * mm, stroke=0, fill=1)

        c.setFillColor(TINTA)
        c.setFont("Helvetica", 8.5)
        descripcion = d.descripcion if len(d.descripcion) <= 58 else d.descripcion[:55] + "..."
        c.drawString(columnas[0] + 3 * mm, fila, descripcion)
        c.drawCentredString(columnas[1] + 8 * mm, fila, str(d.cantidad))
        c.drawRightString(columnas[3] - 3 * mm, fila, formato_cop(d.precio_unitario))
        c.setFont("Helvetica-Bold", 8.5)
        c.drawRightString(columnas[4] - 3 * mm, fila, formato_cop(d.subtotal))
        fila -= 7 * mm

    # Totales
    y_totales = fila - 6 * mm
    x_totales = ancho - 86 * mm
    c.setStrokeColor(colors.HexColor("#d8d2c4"))
    c.setLineWidth(0.6)
    c.line(x_totales, y_totales + 5 * mm, ancho - 16 * mm, y_totales + 5 * mm)

    def linea_total(etiqueta: str, valor, y_pos: float, destacar: bool = False) -> None:
        c.setFont("Helvetica-Bold" if destacar else "Helvetica", 10 if destacar else 8.5)
        c.setFillColor(VERDE if destacar else GRIS)
        c.drawString(x_totales, y_pos, etiqueta)
        c.setFillColor(VERDE if destacar else TINTA)
        c.drawRightString(ancho - 16 * mm, y_pos, formato_cop(valor))

    linea_total("Subtotal", factura.subtotal, y_totales)
    y_totales -= 5.5 * mm
    if float(factura.descuento):
        linea_total("Descuento", -abs(float(factura.descuento)), y_totales)
        y_totales -= 5.5 * mm
    linea_total(f"IVA ({float(factura.iva_porcentaje):g}%)", factura.impuestos, y_totales)
    y_totales -= 8 * mm

    c.setFillColor(VERDE)
    c.roundRect(x_totales - 4 * mm, y_totales - 3 * mm, ancho - 12 * mm - x_totales,
                10 * mm, 2, stroke=0, fill=1)
    c.setFillColor(PAPEL)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_totales, y_totales + 0.6 * mm, "TOTAL A PAGAR")
    c.drawRightString(ancho - 16 * mm, y_totales + 0.6 * mm, formato_cop(factura.total))

    if factura.observaciones:
        c.setFillColor(GRIS)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(16 * mm, y_totales - 8 * mm, f"Observaciones: {factura.observaciones}")

    c.setFillColor(GRIS)
    c.setFont("Helvetica", 7)
    c.drawString(
        16 * mm, 22 * mm,
        "Documento generado electrónicamente. Conserva esta factura como soporte de tu compra.",
    )
    _pie(c, ancho, pagina, f"Factura {factura.numero} · {settings.empresa_nombre}")
    c.showPage()
    c.save()
    return buffer.getvalue()


def generar_reporte_ventas_pdf(ventas: list, dia) -> bytes:
    """Reporte diario de ventas en PDF, en horizontal para que quepan las columnas."""
    buffer = BytesIO()
    pagina_tam = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=pagina_tam)
    ancho, alto = pagina_tam
    fecha_texto = dia.strftime("%d/%m/%Y")
    c.setTitle(f"Reporte de ventas {fecha_texto}")
    c.setAuthor(settings.empresa_nombre)

    y = _cabecera(c, ancho, alto, "Reporte diario de ventas")

    c.setFillColor(TINTA)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(16 * mm, y - 6 * mm, f"Ventas del {fecha_texto}")
    c.setFont("Helvetica", 8)
    c.setFillColor(GRIS)
    generado = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.drawRightString(ancho - 16 * mm, y - 6 * mm, f"Generado el {generado}")

    # Resumen
    total_general = sum(a_decimal(v.total) for v in ventas) if ventas else a_decimal(0)
    total_iva = sum(a_decimal(v.impuestos) for v in ventas) if ventas else a_decimal(0)
    unidades = sum(d.cantidad for v in ventas for d in v.detalles)

    y_res = y - 14 * mm
    tarjetas = [
        ("Ventas registradas", str(len(ventas))),
        ("Unidades vendidas", str(unidades)),
        ("IVA recaudado", formato_cop(total_iva)),
        ("Total facturado", formato_cop(total_general)),
    ]
    ancho_tarjeta = (ancho - 32 * mm - 3 * 4 * mm) / 4
    for indice, (etiqueta, valor) in enumerate(tarjetas):
        x = 16 * mm + indice * (ancho_tarjeta + 4 * mm)
        c.setFillColor(FRANJA)
        c.roundRect(x, y_res - 16 * mm, ancho_tarjeta, 16 * mm, 2, stroke=0, fill=1)
        c.setFillColor(ORO)
        c.rect(x, y_res - 1.4 * mm, ancho_tarjeta, 1.4 * mm, stroke=0, fill=1)
        c.setFillColor(GRIS)
        c.setFont("Helvetica-Bold", 6.8)
        c.drawString(x + 3.5 * mm, y_res - 6 * mm, etiqueta.upper())
        c.setFillColor(VERDE)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x + 3.5 * mm, y_res - 12.5 * mm, valor)

    # Tabla
    y_tabla = y_res - 26 * mm
    cols = {
        "numero": 16 * mm, "fecha": 48 * mm, "cliente": 80 * mm,
        "items": 148 * mm, "cant": 216 * mm, "estado": 232 * mm, "total": ancho - 16 * mm,
    }
    c.setFillColor(VERDE)
    c.rect(16 * mm, y_tabla - 2 * mm, ancho - 32 * mm, 8 * mm, stroke=0, fill=1)
    c.setFillColor(PAPEL)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(cols["numero"] + 2 * mm, y_tabla + 0.6 * mm, "N.º VENTA")
    c.drawString(cols["fecha"], y_tabla + 0.6 * mm, "FECHA Y HORA")
    c.drawString(cols["cliente"], y_tabla + 0.6 * mm, "CLIENTE")
    c.drawString(cols["items"], y_tabla + 0.6 * mm, "PRODUCTOS / SERVICIOS")
    c.drawCentredString(cols["cant"] + 6 * mm, y_tabla + 0.6 * mm, "CANT.")
    c.drawString(cols["estado"], y_tabla + 0.6 * mm, "ESTADO")
    c.drawRightString(cols["total"] - 2 * mm, y_tabla + 0.6 * mm, "TOTAL")

    fila = y_tabla - 9 * mm
    pagina = 1

    if not ventas:
        c.setFillColor(GRIS)
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(ancho / 2, fila - 6 * mm,
                            f"No se registraron ventas el {fecha_texto}.")
    for indice, v in enumerate(ventas):
        if fila < 30 * mm:
            _pie(c, ancho, pagina, f"Reporte de ventas {fecha_texto} · continúa")
            c.showPage()
            pagina += 1
            fila = _cabecera(c, ancho, alto, "Reporte diario de ventas") - 12 * mm

        if indice % 2 == 0:
            c.setFillColor(FRANJA)
            c.rect(16 * mm, fila - 2 * mm, ancho - 32 * mm, 7 * mm, stroke=0, fill=1)

        items = ", ".join(d.descripcion for d in v.detalles)
        if len(items) > 44:
            items = items[:41] + "..."
        cliente = f"{v.cliente.nombre} {v.cliente.apellido}" if v.cliente else "—"
        if len(cliente) > 30:
            cliente = cliente[:27] + "..."

        c.setFillColor(TINTA)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(cols["numero"] + 2 * mm, fila, v.numero)
        c.setFont("Helvetica", 8)
        c.drawString(cols["fecha"], fila, v.creado_en.strftime("%d/%m/%Y %H:%M"))
        c.drawString(cols["cliente"], fila, cliente)
        c.drawString(cols["items"], fila, items)
        c.drawCentredString(cols["cant"] + 6 * mm, fila, str(sum(d.cantidad for d in v.detalles)))
        c.setFillColor(ESTADOS_COLOR.get(v.estado.value, GRIS))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(cols["estado"], fila, v.estado.value.replace("_", " ").upper())
        c.setFillColor(TINTA)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawRightString(cols["total"] - 2 * mm, fila, formato_cop(v.total))
        fila -= 7 * mm

    if ventas:
        c.setStrokeColor(VERDE)
        c.setLineWidth(0.8)
        c.line(16 * mm, fila + 3 * mm, ancho - 16 * mm, fila + 3 * mm)
        c.setFillColor(VERDE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(cols["items"], fila - 3 * mm, "TOTAL DEL DÍA")
        c.drawRightString(cols["total"] - 2 * mm, fila - 3 * mm, formato_cop(total_general))

    _pie(c, ancho, pagina, f"Reporte diario de ventas · {fecha_texto} · {settings.empresa_nombre}")
    c.showPage()
    c.save()
    return buffer.getvalue()
