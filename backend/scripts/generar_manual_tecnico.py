"""Genera el Manual Técnico del proyecto formativo en PDF.

Cumple la estructura obligatoria que pide la solicitud del instructor: portada,
tabla de contenido con numeración, introducción, objetivos, alcance,
arquitectura, modelo de datos, diseño, instalación, documentación de la API,
manual de usuario con capturas, pruebas, conclusiones y anexos.

El diccionario de datos y la tabla de endpoints **no están escritos a mano**:
se extraen de los modelos SQLAlchemy y del esquema OpenAPI, de modo que el
manual no puede quedar desfasado respecto al código.

Requisitos previos:
    python scripts/capturar_evidencias.py   (genera docs/manual/capturas/)

Uso:
    python scripts/generar_manual_tecnico.py
"""

import sys
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_BACKEND))

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402

import app.models  # noqa: E402,F401  registra todas las tablas
from app.database import Base  # noqa: E402
from app.main import app as api  # noqa: E402

RAIZ = RAIZ_BACKEND.parent
CAPTURAS = RAIZ / "docs" / "manual" / "capturas"
DESTINO = RAIZ / "docs" / "manual" / "ManualTecnico_Ficha3406211_VegaNaranjo_JersonJesus.pdf"

# ── Datos del proyecto ───────────────────────────────────────────────────
PROYECTO = "Óleo & Lienzo — Galería de venta de pinturas"
FICHA = "3406211"
PROGRAMA = "Tecnólogo en Análisis y Desarrollo de Software (código 228118)"
CENTRO = "Centro de Servicios y Gestión Empresarial — Regional Antioquia"
APRENDIZ = "Jerson Jesús Vega Naranjo"
INSTRUCTORES = "César Augusto Moreno Mena · Jhan Hader Muñoz"
REPOSITORIO = "https://github.com/vegajerson88-droid/Oleo-Lienzo"
TOTAL_PRUEBAS = 164

# ── Paleta, sobria y legible en impresión ────────────────────────────────
VERDE = colors.HexColor("#1F3D2B")
DORADO = colors.HexColor("#B08D46")
GRIS = colors.HexColor("#44484C")
GRIS_SUAVE = colors.HexColor("#EDEDEA")
LINEA = colors.HexColor("#C9C9C2")


# ── Estilos: Times New Roman 11 pt, interlineado 1.15 ────────────────────
def construir_estilos():
    base = getSampleStyleSheet()
    interlineado = 11 * 1.15

    e = {
        "cuerpo": ParagraphStyle(
            "cuerpo",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=11,
            leading=interlineado,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
            textColor=colors.HexColor("#15171A"),
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="Times-Bold",
            fontSize=17,
            leading=21,
            textColor=VERDE,
            spaceBefore=4,
            spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Times-Bold",
            fontSize=13,
            leading=16,
            textColor=VERDE,
            spaceBefore=13,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName="Times-Bold",
            fontSize=11.5,
            leading=14,
            textColor=GRIS,
            spaceBefore=9,
            spaceAfter=4,
        ),
        "lista": ParagraphStyle(
            "lista",
            fontName="Times-Roman",
            fontSize=11,
            leading=interlineado,
            leftIndent=16,
            bulletIndent=5,
            spaceAfter=3,
            alignment=TA_JUSTIFY,
        ),
        "codigo": ParagraphStyle(
            "codigo",
            fontName="Courier",
            fontSize=8.5,
            leading=11.5,
            leftIndent=8,
            rightIndent=8,
            spaceBefore=4,
            spaceAfter=8,
            backColor=GRIS_SUAVE,
            borderPadding=6,
            textColor=colors.HexColor("#1B1D20"),
        ),
        "tabla": ParagraphStyle("tabla", fontName="Times-Roman", fontSize=8.5, leading=10.5),
        "tabla_cab": ParagraphStyle(
            "tabla_cab",
            fontName="Times-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=colors.white,
        ),
        "pie_figura": ParagraphStyle(
            "pie_figura",
            fontName="Times-Italic",
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=GRIS,
            spaceBefore=3,
            spaceAfter=12,
        ),
        "portada_titulo": ParagraphStyle(
            "portada_titulo",
            fontName="Times-Bold",
            fontSize=26,
            leading=31,
            alignment=TA_CENTER,
            textColor=VERDE,
        ),
        "portada_sub": ParagraphStyle(
            "portada_sub",
            fontName="Times-Roman",
            fontSize=14,
            leading=19,
            alignment=TA_CENTER,
            textColor=GRIS,
        ),
    }
    return e


E = construir_estilos()


def p(texto, estilo="cuerpo"):
    return Paragraph(texto, E[estilo])


def vinetas(items):
    return [Paragraph(f"• {t}", E["lista"]) for t in items]


def numerada(items):
    return [Paragraph(f"{i}. {t}", E["lista"]) for i, t in enumerate(items, 1)]


def tabla(filas, anchos, cabecera=True, tam=8.5):
    """Tabla con la cabecera en verde y filas alternas."""
    datos = []
    for i, fila in enumerate(filas):
        estilo = "tabla_cab" if (cabecera and i == 0) else "tabla"
        datos.append([Paragraph(str(c), E[estilo]) for c in fila])

    t = Table(datos, colWidths=anchos, repeatRows=1 if cabecera else 0)
    estilos = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINEA),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if cabecera:
        estilos += [
            ("BACKGROUND", (0, 0), (-1, 0), VERDE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7F4")]),
        ]
    t.setStyle(TableStyle(estilos))
    return t


def figura(archivo: str, pie: str, ancho=15.5 * cm):
    """Inserta una captura escalada, con su pie numerado."""
    ruta = CAPTURAS / archivo
    if not ruta.exists():
        return [p(f"<i>[Falta la captura {archivo}]</i>")]

    from reportlab.lib.utils import ImageReader

    ancho_px, alto_px = ImageReader(str(ruta)).getSize()
    alto = ancho * alto_px / ancho_px

    # Una captura de página completa puede ser larguísima: se limita para que
    # quepa en la página y no se coma el documento entero.
    alto_maximo = 17 * cm
    if alto > alto_maximo:
        ancho = ancho * alto_maximo / alto
        alto = alto_maximo

    img = Image(str(ruta), width=ancho, height=alto)
    img.hAlign = "CENTER"
    figura.contador += 1
    return [img, Paragraph(f"Figura {figura.contador}. {pie}", E["pie_figura"])]


figura.contador = 0


# ── Encabezado institucional y pie con numeración ────────────────────────
def decorar_pagina(canvas, doc):
    canvas.saveState()
    ancho, alto = A4

    # Encabezado
    canvas.setFillColor(VERDE)
    canvas.rect(0, alto - 1.55 * cm, ancho, 1.55 * cm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Times-Bold", 9.5)
    canvas.drawString(2.2 * cm, alto - 1.0 * cm, "SERVICIO NACIONAL DE APRENDIZAJE — SENA")
    canvas.setFont("Times-Roman", 8.5)
    canvas.drawRightString(ancho - 2.2 * cm, alto - 1.0 * cm, f"Manual Técnico · Ficha {FICHA}")

    # Pie
    canvas.setStrokeColor(LINEA)
    canvas.setLineWidth(0.4)
    canvas.line(2.2 * cm, 1.5 * cm, ancho - 2.2 * cm, 1.5 * cm)
    canvas.setFillColor(GRIS)
    canvas.setFont("Times-Roman", 8.5)
    canvas.drawString(2.2 * cm, 1.05 * cm, PROYECTO)
    canvas.drawRightString(ancho - 2.2 * cm, 1.05 * cm, f"Página {doc.page - 1}")
    canvas.restoreState()


def decorar_portada(canvas, doc):
    canvas.saveState()
    ancho, alto = A4
    canvas.setFillColor(VERDE)
    canvas.rect(0, alto - 0.9 * cm, ancho, 0.9 * cm, stroke=0, fill=1)
    canvas.rect(0, 0, ancho, 0.9 * cm, stroke=0, fill=1)
    canvas.restoreState()


# ── Contenido: diccionario de datos desde los modelos ────────────────────
DESCRIPCION_TABLAS = {
    "roles": "Roles del sistema: administrador, empleado y cliente.",
    "permisos": "Acciones concretas que un rol puede realizar.",
    "rol_permisos": "Relación muchos a muchos entre roles y permisos.",
    "usuarios": "Usuarios del sistema. La contraseña solo se guarda como hash bcrypt.",
    "obras": "Catálogo de obras de arte (los productos de la galería).",
    "servicios": "Servicios: enmarcado, restauración, envío asegurado y curaduría.",
    "pedidos": "Órdenes que el cliente arma desde el sitio web.",
    "detalles_pedido": "Líneas de un pedido: una obra o un servicio por línea.",
    "ventas": "Transacciones comerciales con su desglose económico completo.",
    "detalle_ventas": "Líneas de una venta, con precio y descuento congelados.",
    "facturas": "Documentos fiscales emitidos a partir de una venta.",
    "pagos": "Pagos con Stripe. Solo referencias: ningún dato de tarjeta.",
    "pqr": "Peticiones, quejas, reclamos y sugerencias.",
    "conversaciones": "Conversaciones mantenidas con el chatbot.",
    "mensajes": "Mensajes individuales de cada conversación.",
}


def tipo_legible(columna) -> str:
    try:
        texto = str(columna.type)
    except Exception:
        texto = columna.type.__class__.__name__
    return texto.replace("VARCHAR", "VARCHAR").replace("TIMESTAMP", "TIMESTAMP")[:26]


def diccionario_de_datos() -> list:
    elementos = []
    for t in Base.metadata.sorted_tables:
        filas = [["Columna", "Tipo", "Nulo", "Clave", "Descripción"]]
        for c in t.columns:
            claves = []
            if c.primary_key:
                claves.append("PK")
            for fk in c.foreign_keys:
                claves.append(f"FK → {fk.column.table.name}")
            if c.unique:
                claves.append("UNIQUE")

            nota = ""
            if c.name == "password_hash":
                nota = "Hash bcrypt de 60 caracteres. Nunca la contraseña en claro."
            elif c.name in ("numero", "radicado"):
                nota = "Consecutivo que asigna el servidor."
            elif c.name == "creado_en":
                nota = "Instante de creación, en UTC."
            elif c.name == "actualizado_en":
                nota = "Última modificación, en UTC."

            filas.append(
                [
                    f"<b>{c.name}</b>",
                    tipo_legible(c),
                    "Sí" if c.nullable else "No",
                    ", ".join(claves) or "—",
                    nota,
                ]
            )

        bloque = [
            Paragraph(f"Tabla <b>{t.name}</b>", E["h3"]),
            p(DESCRIPCION_TABLAS.get(t.name, "")),
            tabla(filas, [3.4 * cm, 3.1 * cm, 1.2 * cm, 3.1 * cm, 4.7 * cm]),
            Spacer(1, 0.35 * cm),
        ]
        elementos.append(KeepTogether(bloque) if len(t.columns) <= 9 else bloque)

    # Aplana las listas que no se envolvieron en KeepTogether.
    planos = []
    for e in elementos:
        planos.extend(e) if isinstance(e, list) else planos.append(e)
    return planos


def tabla_de_endpoints() -> list:
    esquema = api.openapi()
    por_etiqueta = {}
    for ruta, metodos in esquema["paths"].items():
        for verbo, operacion in metodos.items():
            etiqueta = (operacion.get("tags") or ["Sistema"])[0]
            por_etiqueta.setdefault(etiqueta, []).append(
                (verbo.upper(), ruta, operacion.get("summary", ""))
            )

    elementos = []
    for etiqueta, operaciones in por_etiqueta.items():
        filas = [["Verbo", "Ruta", "Operación"]]
        for verbo, ruta, resumen in sorted(operaciones, key=lambda o: ("{" in o[1], o[1], o[0])):
            filas.append(
                [f"<b>{verbo}</b>", f"<font face='Courier' size='8'>{ruta}</font>", resumen]
            )
        elementos.append(
            KeepTogether(
                [
                    Paragraph(etiqueta, E["h3"]),
                    tabla(filas, [1.8 * cm, 7.2 * cm, 6.5 * cm]),
                    Spacer(1, 0.3 * cm),
                ]
            )
        )
    return elementos, sum(len(v) for v in por_etiqueta.values())


# ── Diagramas dibujados con primitivas, para que no dependan de imágenes ─
def diagrama_arquitectura():
    """Las tres capas y lo que viaja entre ellas."""
    from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String

    d = Drawing(440, 210)
    capas = [
        (
            10,
            "React + Vite",
            "Navegador",
            ["Páginas y componentes", "Cliente HTTP central", "Validación en cliente"],
        ),
        (160, "FastAPI", "Servidor", ["Routers y esquemas", "JWT y roles", "Reglas de negocio"]),
        (
            310,
            "PostgreSQL",
            "Base de datos",
            ["15 tablas", "20 claves foráneas", "Restricciones y CHECK"],
        ),
    ]
    for x, titulo, subtitulo, lineas in capas:
        d.add(
            Rect(
                x,
                40,
                120,
                140,
                fillColor=colors.HexColor("#F3F3EF"),
                strokeColor=VERDE,
                strokeWidth=1.2,
            )
        )
        d.add(Rect(x, 150, 120, 30, fillColor=VERDE, strokeColor=VERDE))
        d.add(
            String(
                x + 60,
                160,
                titulo,
                fontName="Times-Bold",
                fontSize=11,
                fillColor=colors.white,
                textAnchor="middle",
            )
        )
        d.add(
            String(
                x + 60,
                136,
                subtitulo,
                fontName="Times-Italic",
                fontSize=8.5,
                fillColor=GRIS,
                textAnchor="middle",
            )
        )
        for i, linea in enumerate(lineas):
            d.add(
                String(
                    x + 60,
                    116 - i * 15,
                    linea,
                    fontName="Times-Roman",
                    fontSize=8,
                    fillColor=colors.HexColor("#22252A"),
                    textAnchor="middle",
                )
            )

    for x0, etiqueta, bajo in [
        (130, "HTTPS · JSON", "Authorization: Bearer"),
        (280, "SQL", "SQLAlchemy async"),
    ]:
        d.add(Line(x0, 110, x0 + 30, 110, strokeColor=DORADO, strokeWidth=1.6))
        d.add(
            Polygon(
                [x0 + 30, 110, x0 + 23, 106, x0 + 23, 114], fillColor=DORADO, strokeColor=DORADO
            )
        )
        d.add(
            String(
                x0 + 15,
                118,
                etiqueta,
                fontName="Times-Bold",
                fontSize=7.5,
                fillColor=GRIS,
                textAnchor="middle",
            )
        )
        d.add(
            String(
                x0 + 15,
                96,
                bajo,
                fontName="Times-Roman",
                fontSize=7,
                fillColor=GRIS,
                textAnchor="middle",
            )
        )

    d.add(
        Rect(
            10,
            5,
            420,
            24,
            fillColor=colors.HexColor("#FBF7EC"),
            strokeColor=DORADO,
            strokeWidth=0.8,
        )
    )
    d.add(
        String(
            220,
            13,
            "Servicios externos:  Groq (chatbot IA)  ·  Stripe (pagos)  ·  SMTP (correo)",
            fontName="Times-Roman",
            fontSize=8.5,
            fillColor=GRIS,
            textAnchor="middle",
        )
    )
    return d


def diagrama_entidad_relacion():
    """Las entidades principales y cómo se encadenan."""
    from reportlab.graphics.shapes import Drawing, Line, Rect, String

    d = Drawing(440, 300)
    cajas = {
        "roles": (10, 250, "roles", ["id PK", "nombre UQ"]),
        "usuarios": (10, 165, "usuarios", ["id PK", "email UQ", "password_hash", "rol_id FK"]),
        "obras": (175, 250, "obras", ["id PK", "titulo", "precio", "stock"]),
        "servicios": (310, 250, "servicios", ["id PK", "nombre", "precio"]),
        "pedidos": (10, 80, "pedidos", ["id PK", "cliente_id FK", "estado"]),
        "ventas": (165, 145, "ventas", ["id PK", "numero UQ", "cliente_id FK", "total"]),
        "detalle": (
            165,
            45,
            "detalle_ventas",
            ["id PK", "venta_id FK", "obra_id FK", "servicio_id FK"],
        ),
        "facturas": (315, 145, "facturas", ["id PK", "numero UQ", "venta_id FK UQ"]),
        "pqr": (315, 45, "pqr", ["id PK", "radicado UQ", "cliente_id FK"]),
    }
    for _, (x, y, nombre, campos) in cajas.items():
        alto = 18 + len(campos) * 10
        d.add(
            Rect(
                x,
                y - alto + 18,
                115,
                alto,
                fillColor=colors.white,
                strokeColor=VERDE,
                strokeWidth=0.9,
            )
        )
        d.add(Rect(x, y + 4, 115, 14, fillColor=VERDE, strokeColor=VERDE))
        d.add(
            String(
                x + 57,
                y + 8,
                nombre,
                fontName="Times-Bold",
                fontSize=8,
                fillColor=colors.white,
                textAnchor="middle",
            )
        )
        for i, campo in enumerate(campos):
            d.add(
                String(
                    x + 5, y - 6 - i * 10, campo, fontName="Times-Roman", fontSize=7, fillColor=GRIS
                )
            )

    relaciones = [
        (67, 165, 67, 250, "N:1"),
        (125, 150, 165, 150, "1:N"),
        (222, 128, 222, 80, "1:N"),
        (280, 150, 315, 150, "1:1"),
        (67, 120, 67, 95, "1:N"),
        (232, 250, 232, 80, ""),
        (367, 250, 280, 60, ""),
        (125, 120, 315, 60, "1:N"),
    ]
    for x0, y0, x1, y1, etiqueta in relaciones:
        d.add(Line(x0, y0, x1, y1, strokeColor=DORADO, strokeWidth=0.9))
        if etiqueta:
            d.add(
                String(
                    (x0 + x1) / 2 + 5,
                    (y0 + y1) / 2 + 3,
                    etiqueta,
                    fontName="Times-Roman",
                    fontSize=6.5,
                    fillColor=GRIS,
                )
            )
    return d


def diagrama_flujo_comercial():
    """El encadenamiento pedido → venta → factura."""
    from reportlab.graphics.shapes import Drawing, Polygon, Rect, String

    d = Drawing(440, 90)
    pasos = [
        ("1. Pedido", "el cliente lo arma"),
        ("2. Confirmar", "genera la venta"),
        ("3. Venta", "descuenta inventario"),
        ("4. Factura", "congela importes"),
        ("5. PDF", "el cliente descarga"),
    ]
    ancho, hueco = 76, 14
    for i, (titulo, detalle) in enumerate(pasos):
        x = 4 + i * (ancho + hueco)
        d.add(
            Rect(
                x,
                28,
                ancho,
                40,
                fillColor=colors.HexColor("#F3F3EF"),
                strokeColor=VERDE,
                strokeWidth=1,
            )
        )
        d.add(
            String(
                x + ancho / 2,
                54,
                titulo,
                fontName="Times-Bold",
                fontSize=8.5,
                fillColor=VERDE,
                textAnchor="middle",
            )
        )
        d.add(
            String(
                x + ancho / 2,
                39,
                detalle,
                fontName="Times-Roman",
                fontSize=7,
                fillColor=GRIS,
                textAnchor="middle",
            )
        )
        if i < len(pasos) - 1:
            fx = x + ancho + 2
            d.add(Polygon([fx, 48, fx + 9, 44, fx, 40], fillColor=DORADO, strokeColor=DORADO))
    return d


# ═════════════════════════════════════════════════════════════════════════
#  CONTENIDO DEL MANUAL
# ═════════════════════════════════════════════════════════════════════════
def portada():
    return [
        Spacer(1, 2.2 * cm),
        p("SERVICIO NACIONAL DE APRENDIZAJE — SENA", "portada_sub"),
        p(CENTRO, "portada_sub"),
        Spacer(1, 1.8 * cm),
        p("MANUAL TÉCNICO", "portada_sub"),
        Spacer(1, 0.4 * cm),
        p(PROYECTO, "portada_titulo"),
        Spacer(1, 0.5 * cm),
        p("Proyecto integrador React + Vite · FastAPI · PostgreSQL", "portada_sub"),
        Spacer(1, 2.4 * cm),
        tabla(
            [
                ["Programa de formación", PROGRAMA],
                ["Ficha", FICHA],
                ["Trimestre / Ambiente", "03 / 702"],
                ["Aprendiz", APRENDIZ],
                ["Instructores", INSTRUCTORES],
                ["Repositorio", REPOSITORIO],
                ["Fecha de entrega", "29 de septiembre de 2026"],
                ["Versión del documento", "1.0"],
            ],
            [5.2 * cm, 10.3 * cm],
            cabecera=False,
        ),
        Spacer(1, 2.2 * cm),
        p("Medellín, Antioquia · Colombia", "portada_sub"),
    ]


def tabla_de_contenido():
    """Índice que ReportLab rellena solo, en la segunda pasada de `multiBuild`.

    Escribir los números de página a mano sería un error esperando a ocurrir:
    basta añadir un párrafo para que todos dejen de coincidir.
    """
    indice = TableOfContents()
    indice.levelStyles = [
        ParagraphStyle(
            "toc1",
            fontName="Times-Bold",
            fontSize=11,
            leading=18,
            textColor=VERDE,
            spaceBefore=6,
        ),
        ParagraphStyle(
            "toc2",
            fontName="Times-Roman",
            fontSize=10,
            leading=15,
            leftIndent=18,
            textColor=GRIS,
        ),
    ]
    return [p("Tabla de contenido", "h1"), indice]


def seccion_introduccion():
    return [
        p("1. Introducción y descripción general del proyecto", "h1"),
        p("1.1 El problema que resuelve", "h2"),
        p(
            "Las galerías de arte pequeñas y medianas de Colombia gestionan su operación con "
            "herramientas dispersas: el catálogo en redes sociales, las ventas en un cuaderno o "
            "una hoja de cálculo, las facturas en documentos sueltos y la atención al cliente por "
            "mensajería. Esa dispersión provoca tres problemas concretos: no hay una fuente única "
            "sobre qué obra sigue disponible, no se puede saber cuánto se vendió en un periodo sin "
            "reconstruirlo a mano, y el cliente no tiene forma de consultar el estado de su compra "
            "sin escribir y esperar respuesta."
        ),
        p(
            "<b>Óleo &amp; Lienzo</b> es una aplicación web que resuelve esas tres carencias sobre "
            "una única base de datos: publica el catálogo, registra las ventas con su desglose "
            "económico, emite facturas con consecutivo, genera reportes en PDF y Excel, muestra "
            "indicadores por rol y atiende consultas mediante un chatbot con inteligencia artificial."
        ),
        p("1.2 Contexto de la formación", "h2"),
        p(
            f"El proyecto se desarrolló durante el tercer trimestre de la ficha {FICHA} del programa "
            "de Análisis y Desarrollo de Software. Es la evolución acumulada de cinco entregas: la "
            "interfaz en React, los estilos con Tailwind, la integración con un backend y base de "
            "datos, la migración de ese backend a FastAPI y, por último, la capa comercial, la "
            "analítica y la inteligencia artificial."
        ),
        p("1.3 Usuarios y actores del sistema", "h2"),
        tabla(
            [
                ["Actor", "Quién es", "Qué hace en el sistema"],
                [
                    "<b>Visitante</b>",
                    "Cualquiera que entra al sitio sin registrarse.",
                    "Recorre la galería y el catálogo, consulta la ficha de cada obra, escribe por "
                    "el formulario de contacto y conversa con el chatbot.",
                ],
                [
                    "<b>Cliente</b>",
                    "Visitante que creó una cuenta.",
                    "Arma pedidos, consulta sus compras y facturas, descarga el PDF de una factura "
                    "y radica PQR con seguimiento de estado.",
                ],
                [
                    "<b>Empleado</b>",
                    "Personal operativo de la galería.",
                    "Gestiona el catálogo, atiende pedidos, registra ventas, emite facturas, genera "
                    "reportes y responde PQR. No accede a la gestión de usuarios.",
                ],
                [
                    "<b>Administrador</b>",
                    "Responsable de la galería.",
                    "Todo lo del empleado, más la gestión de usuarios y roles, el dashboard "
                    "completo con facturación e ingresos, y el diagnóstico del sistema.",
                ],
            ],
            [2.6 * cm, 4.6 * cm, 8.3 * cm],
        ),
    ]


def seccion_objetivos():
    return [
        p("2. Objetivos", "h1"),
        p("2.1 Objetivo general", "h2"),
        p(
            "Desarrollar y desplegar una aplicación web full stack para la gestión comercial de una "
            "galería de arte, construida sobre la arquitectura React + Vite → FastAPI → PostgreSQL, "
            "que permita administrar el catálogo, registrar ventas, emitir facturas, generar "
            "reportes, analizar la información mediante dashboards diferenciados por rol y atender "
            "a los clientes con un chatbot basado en inteligencia artificial, aplicando prácticas "
            "de seguridad en la autenticación, la autorización y el manejo de credenciales."
        ),
        p("2.2 Objetivos específicos", "h2"),
        *numerada(
            [
                "Diseñar e implementar una API REST con FastAPI que exponga los recursos del "
                "dominio siguiendo los criterios REST de recurso, verbo, ruta y código de respuesta.",
                "Modelar la información en una base de datos relacional PostgreSQL con integridad "
                "referencial, restricciones de unicidad y reglas de validación en el propio motor.",
                "Implementar autenticación con JSON Web Tokens y autorización por roles y permisos, "
                "de modo que la decisión final sobre quién puede hacer qué la tome siempre el backend.",
                "Construir el módulo comercial completo: pedidos, ventas con desglose de IVA, "
                "facturación con consecutivo y generación de reportes en formato PDF y Excel.",
                "Desarrollar dashboards diferenciados por rol que obtengan sus indicadores y "
                "gráficos de consultas agregadas en la base de datos, sin ningún dato escrito a mano.",
                "Integrar inteligencia artificial en dos frentes: un modelo propio de regresión "
                "entrenado con el catálogo y un chatbot conectado a un proveedor externo, con las "
                "credenciales gestionadas por variables de entorno.",
                "Verificar el comportamiento del sistema con una suite de pruebas automatizadas y "
                "preparar el despliegue en un entorno de producción en la nube.",
            ]
        ),
    ]


def seccion_alcance():
    return [
        p("3. Alcance del proyecto", "h1"),
        p("3.1 Funcionalidades incluidas", "h2"),
        tabla(
            [
                ["Módulo", "Qué incluye"],
                [
                    "<b>Catálogo</b>",
                    "CRUD completo de obras y servicios, con búsqueda por texto y filtros por "
                    "artista, técnica, disponibilidad y rango de precio, más paginación.",
                ],
                [
                    "<b>Usuarios y seguridad</b>",
                    "Registro, inicio de sesión con JWT, recuperación de contraseña, hashing con "
                    "bcrypt, tres roles con permisos granulares y cambio de estado activo/inactivo.",
                ],
                [
                    "<b>Comercial</b>",
                    "Pedidos del cliente, confirmación que genera la venta, ventas con desglose de "
                    "IVA al 19 %, control de inventario y máquina de estados validada.",
                ],
                [
                    "<b>Facturación</b>",
                    "Emisión con consecutivo OL-NNNNNN, congelado de los importes y de los datos "
                    "del cliente, consulta por varios criterios y descarga en PDF.",
                ],
                [
                    "<b>Reportes</b>",
                    "Reporte diario de ventas en JSON, PDF y Excel, este último con fórmulas y "
                    "autofiltro para seguir analizando los datos.",
                ],
                [
                    "<b>Analítica</b>",
                    "Dashboards por rol con tarjetas de indicadores, gráfico lineal y de barras, y "
                    "filtros por fecha, obra, servicio, estado y cliente.",
                ],
                [
                    "<b>PQR</b>",
                    "Radicación con número de radicado, cuatro estados de seguimiento y respuesta "
                    "por parte del personal.",
                ],
                [
                    "<b>Inteligencia artificial</b>",
                    "Chatbot con Groq que responde usando el catálogo real, y modelo propio de "
                    "scikit-learn que sugiere precios. Ambos degradan de forma explícita si fallan.",
                ],
            ],
            [3.4 * cm, 12.1 * cm],
        ),
        p("3.2 Funcionalidades excluidas explícitamente", "h2"),
        p(
            "Delimitar lo que el proyecto <i>no</i> hace es tan importante como enumerar lo que sí: "
            "evita que se evalúe contra expectativas que nunca formaron parte del alcance."
        ),
        *vinetas(
            [
                "<b>Cobro real de dinero.</b> La pasarela Stripe está integrada, pero funciona en "
                "modo de prueba con las tarjetas de ensayo del proveedor. No se procesan pagos reales.",
                "<b>Facturación electrónica ante la DIAN.</b> Las facturas son documentos internos "
                "con consecutivo propio; no se validan ni se transmiten a la autoridad tributaria.",
                "<b>Logística de envíos.</b> No hay integración con transportadoras ni seguimiento "
                "de guías: el envío asegurado se modela como un servicio más del catálogo.",
                "<b>Aplicación móvil nativa.</b> La interfaz es web y responsiva, verificada a 375, "
                "768 y 1440 píxeles, pero no existe una aplicación para Android ni iOS.",
                "<b>Gestión contable.</b> No hay libro mayor, conciliación bancaria ni informes "
                "fiscales; el alcance llega hasta el reporte de ventas.",
                "<b>Multi-idioma y multi-moneda.</b> La aplicación está en español y opera en pesos "
                "colombianos.",
            ]
        ),
    ]


def seccion_arquitectura():
    return [
        p("4. Arquitectura de la solución", "h1"),
        p("4.1 Visión general", "h2"),
        p(
            "La solución sigue una arquitectura de tres capas con responsabilidades separadas. El "
            "navegador ejecuta la interfaz en React; el servidor FastAPI concentra las reglas de "
            "negocio, la autenticación y la autorización; y PostgreSQL guarda la información con "
            "integridad referencial. La comunicación entre la primera y la segunda capa es HTTP con "
            "cuerpos JSON; entre la segunda y la tercera, SQL generado por SQLAlchemy."
        ),
        diagrama_arquitectura(),
        Paragraph("Figura 1. Arquitectura en tres capas y servicios externos.", E["pie_figura"]),
        p(
            "Una decisión de diseño atraviesa todo el sistema: <b>la autorización definitiva la "
            "decide siempre el backend</b>. El frontend oculta las opciones que no corresponden al "
            "rol, pero eso es comodidad de interfaz, no seguridad. Quien llame directamente a la "
            "API sin los permisos adecuados recibe un 401 o un 403 igualmente."
        ),
        p("4.2 Stack tecnológico", "h2"),
        tabla(
            [
                ["Capa", "Tecnología", "Versión", "Por qué se eligió"],
                [
                    "Frontend",
                    "React + Vite",
                    "18 · 5.4",
                    "Componentes reutilizables y arranque de desarrollo casi instantáneo.",
                ],
                [
                    "Estilos",
                    "Tailwind CSS",
                    "4",
                    "Sistema de diseño coherente sin mantener hojas de estilo aparte.",
                ],
                [
                    "Enrutado",
                    "React Router DOM",
                    "6",
                    "Navegación sin recargar y rutas protegidas por rol.",
                ],
                [
                    "Backend",
                    "FastAPI",
                    "0.141",
                    "Validación automática con Pydantic y documentación OpenAPI sin esfuerzo extra.",
                ],
                [
                    "ORM",
                    "SQLAlchemy",
                    "2.1",
                    "Estilo declarativo moderno con tipado y soporte asíncrono.",
                ],
                [
                    "Base de datos",
                    "PostgreSQL",
                    "16",
                    "Integridad referencial real, restricciones CHECK y agregaciones eficientes.",
                ],
                [
                    "Autenticación",
                    "python-jose · passlib",
                    "3.5 · 1.7",
                    "JWT firmado y hashing bcrypt con sal por contraseña.",
                ],
                [
                    "Documentos",
                    "ReportLab · openpyxl",
                    "5.0 · 3.1",
                    "Generación de facturas y reportes en PDF y Excel desde el servidor.",
                ],
                [
                    "IA propia",
                    "scikit-learn",
                    "1.9",
                    "Regresión lineal entrenada con el propio catálogo para sugerir precios.",
                ],
                [
                    "IA externa",
                    "Groq",
                    "llama-3.3-70b",
                    "Plan gratuito suficiente para el chatbot, compatible con la API de OpenAI.",
                ],
                [
                    "Pruebas",
                    "pytest · httpx",
                    "9.1 · 0.28",
                    f"{TOTAL_PRUEBAS} pruebas sobre SQLite y PostgreSQL.",
                ],
            ],
            [2.3 * cm, 3.3 * cm, 2.2 * cm, 7.7 * cm],
        ),
        p("4.3 Organización del código", "h2"),
        p(
            "El backend se organiza por responsabilidad, no por tipo de archivo. Cada capa solo "
            "conoce a la de abajo:"
        ),
        Paragraph(
            "backend/app/<br/>"
            "&nbsp;&nbsp;main.py .............. solo configuración, middlewares e include_router<br/>"
            "&nbsp;&nbsp;core/ ................ ajustes, seguridad, excepciones, middlewares<br/>"
            "&nbsp;&nbsp;models/ .............. tablas SQLAlchemy (15)<br/>"
            "&nbsp;&nbsp;schemas/ ............. validación de entrada y salida con Pydantic<br/>"
            "&nbsp;&nbsp;crud/ ................ acceso a datos y reglas de negocio<br/>"
            "&nbsp;&nbsp;routers/ ............. endpoints HTTP, uno por recurso (14)<br/>"
            "&nbsp;&nbsp;dependencies/ ........ autenticación, paginación y resolución de recursos<br/>"
            "&nbsp;&nbsp;services/ ............ PDF, Excel, correo, chatbot, IA y tareas de fondo",
            E["codigo"],
        ),
        p(
            "Esa separación tiene una consecuencia práctica que conviene señalar: <b>la capa "
            "<font face='Courier' size='9'>crud</font> nunca lanza excepciones HTTP</b>. Lanza "
            "errores de dominio propios, y unos manejadores registrados en "
            "<font face='Courier' size='9'>main.py</font> los traducen al código HTTP que "
            "corresponde. Así la lógica de negocio no depende del protocolo y podría reutilizarse "
            "desde una tarea programada o una interfaz de línea de comandos."
        ),
    ]


def seccion_modelo_datos():
    elementos = [
        p("5. Modelo de datos", "h1"),
        p("5.1 Diagrama entidad-relación", "h2"),
        p(
            "El modelo tiene <b>15 tablas</b>, <b>132 columnas</b>, <b>20 claves foráneas</b> y "
            "<b>27 índices</b>. El diagrama muestra las entidades principales y cómo se encadenan; "
            "las tablas de apoyo (permisos, conversaciones y mensajes) se detallan en el "
            "diccionario de datos."
        ),
        diagrama_entidad_relacion(),
        Paragraph(
            "Figura 2. Diagrama entidad-relación de las entidades principales.", E["pie_figura"]
        ),
        p("5.2 Decisiones de modelado que conviene explicar", "h2"),
        *vinetas(
            [
                "<b>La factura congela los datos.</b> Copia el nombre, el documento y la dirección "
                "del cliente, y también los importes. Si mañana el cliente cambia de dirección o "
                "sube el precio de una obra, la factura ya emitida no se altera: un documento "
                "fiscal debe reflejar lo que ocurrió, no lo que es cierto hoy.",
                "<b>Una venta se factura una sola vez.</b> La columna "
                "<font face='Courier' size='9'>venta_id</font> de la tabla facturas es única, así "
                "que la restricción la impone la base de datos, no solo el código.",
                "<b>Cada línea de detalle apunta a una obra o a un servicio, nunca a ambas.</b> Lo "
                "garantiza una restricción CHECK con un XOR, de modo que un error de programación "
                "no puede dejar datos incoherentes.",
                "<b>El dinero se guarda como NUMERIC, no como float.</b> Los cálculos se hacen con "
                "Decimal y redondeo ROUND_HALF_UP: con coma flotante, los céntimos acabarían "
                "descuadrando las facturas.",
                "<b>Los estados se guardan como texto con CHECK, no como ENUM nativo.</b> Así el "
                "mismo esquema funciona igual en PostgreSQL y en SQLite, que es lo que permite "
                "ejecutar la suite de pruebas en los dos motores.",
                "<b>Las fechas llevan zona horaria y se guardan en UTC.</b> La conversión a hora "
                "local se hace al presentar, nunca al almacenar.",
            ]
        ),
        p("5.3 Diccionario de datos", "h2"),
        p(
            "Las tablas siguientes se generan a partir de los modelos SQLAlchemy del proyecto, de "
            "modo que el diccionario y el código no pueden discrepar."
        ),
    ]
    elementos += diccionario_de_datos()
    return elementos


def seccion_diseno():
    return [
        PageBreak(),
        p("6. Diseño de la solución", "h1"),
        p("6.1 Historias de usuario y su implementación", "h2"),
        p(
            "Cada historia se enuncia desde la necesidad de quien la usa, y se indica dónde quedó "
            "implementada para que pueda verificarse."
        ),
        tabla(
            [
                ["#", "Historia de usuario", "Dónde está implementada"],
                [
                    "HU-01",
                    "Como <b>visitante</b> quiero recorrer el catálogo y filtrar por artista, "
                    "técnica y precio, para encontrar una obra que me interese.",
                    "<font face='Courier' size='8'>GET /api/productos</font> con seis filtros y "
                    "paginación · página Catálogo",
                ],
                [
                    "HU-02",
                    "Como <b>visitante</b> quiero crear una cuenta validando mis datos, para poder "
                    "comprar.",
                    "<font face='Courier' size='8'>POST /api/auth/registro</font> · "
                    "RegisterModal.jsx · doble validación",
                ],
                [
                    "HU-03",
                    "Como <b>cliente</b> quiero armar un pedido con varias obras y servicios, para "
                    "comprarlos juntos.",
                    "<font face='Courier' size='8'>POST /api/pedidos</font> · pedidos y "
                    "detalles_pedido",
                ],
                [
                    "HU-04",
                    "Como <b>cliente</b> quiero consultar mis compras y descargar la factura, para "
                    "tener el soporte.",
                    "<font face='Courier' size='8'>GET /api/facturas/{id}/pdf</font> · panel del "
                    "cliente",
                ],
                [
                    "HU-05",
                    "Como <b>cliente</b> quiero radicar una PQR y seguir su estado, para saber si "
                    "me van a responder.",
                    "<font face='Courier' size='8'>POST /api/pqr</font> · radicado y cuatro estados",
                ],
                [
                    "HU-06",
                    "Como <b>empleado</b> quiero registrar una venta presencial, para que quede en "
                    "el sistema aunque no venga del sitio web.",
                    "<font face='Courier' size='8'>POST /api/ventas</font> · panel de ventas",
                ],
                [
                    "HU-07",
                    "Como <b>empleado</b> quiero emitir la factura de una venta, para entregarle el "
                    "documento al cliente.",
                    "<font face='Courier' size='8'>POST /api/facturas</font> · consecutivo "
                    "OL-NNNNNN",
                ],
                [
                    "HU-08",
                    "Como <b>administrador</b> quiero ver cuánto se vendió en un periodo y qué se "
                    "vendió más, para tomar decisiones.",
                    "<font face='Courier' size='8'>GET /api/dashboard</font> · 12 indicadores y 4 "
                    "gráficos",
                ],
                [
                    "HU-09",
                    "Como <b>administrador</b> quiero descargar el reporte diario en Excel, para "
                    "seguir analizándolo por mi cuenta.",
                    "<font face='Courier' size='8'>GET /api/reportes/ventas-diarias/excel</font>",
                ],
                [
                    "HU-10",
                    "Como <b>administrador</b> quiero activar o desactivar un usuario sin borrarlo, "
                    "para conservar su histórico.",
                    "<font face='Courier' size='8'>PATCH /api/usuarios/{id}/estado</font>",
                ],
                [
                    "HU-11",
                    "Como <b>visitante</b> quiero preguntar por las obras a cualquier hora y que me "
                    "respondan con información real.",
                    "<font face='Courier' size='8'>POST /api/chatbot/mensaje</font> · Groq con el "
                    "catálogo como contexto",
                ],
            ],
            [1.5 * cm, 7.3 * cm, 6.7 * cm],
        ),
        p("6.2 El flujo comercial, paso a paso", "h2"),
        p(
            "El encadenamiento pedido → venta → factura es la columna vertebral del sistema y "
            "conviene entenderlo entero, porque cada paso deja rastro en una tabla distinta:"
        ),
        diagrama_flujo_comercial(),
        Paragraph("Figura 3. Encadenamiento del flujo comercial.", E["pie_figura"]),
        p(
            "Confirmar un pedido es la operación más delicada del sistema: <b>crea la venta, copia "
            "sus líneas, calcula el IVA y descuenta el inventario, todo dentro de una única "
            "transacción</b>. Si cualquiera de esos pasos falla, se deshacen todos. Sin esa "
            "garantía podría quedar una venta sin líneas, o inventario descontado sin venta."
        ),
        p("6.3 Máquinas de estado", "h2"),
        p(
            "Los estados no cambian libremente: cada transición se valida contra una tabla de "
            "transiciones permitidas. Una venta pagada, por ejemplo, <b>no puede anularse</b>: debe "
            "reembolsarse, porque eso sí deja rastro contable."
        ),
        tabla(
            [
                ["Entidad", "Estado", "Transiciones permitidas"],
                ["<b>Pedido</b>", "pendiente", "confirmado · cancelado"],
                ["", "confirmado", "entregado · cancelado"],
                ["", "entregado / cancelado", "— (final)"],
                ["<b>Venta</b>", "pendiente_pago", "pagada · anulada"],
                ["", "pagada", "reembolsada"],
                ["", "anulada / reembolsada", "— (final)"],
                ["<b>Factura</b>", "emitida", "pagada · anulada"],
                ["", "pagada", "anulada"],
                ["<b>PQR</b>", "pendiente", "en_proceso · respondida · cerrada"],
                ["", "respondida", "cerrada · en_proceso"],
            ],
            [2.8 * cm, 4.5 * cm, 8.2 * cm],
        ),
    ]


def seccion_instalacion():
    return [
        PageBreak(),
        p("7. Manual de instalación y configuración", "h1"),
        p("7.1 Requisitos previos", "h2"),
        tabla(
            [
                ["Componente", "Versión mínima", "Cómo comprobarlo"],
                [
                    "Python",
                    "3.11 (probado en 3.12)",
                    "<font face='Courier' size='8'>python --version</font>",
                ],
                [
                    "Node.js",
                    "18 (probado en 20)",
                    "<font face='Courier' size='8'>node --version</font>",
                ],
                [
                    "PostgreSQL",
                    "14 (probado en 16)",
                    "<font face='Courier' size='8'>psql --version</font>",
                ],
                [
                    "Git",
                    "cualquiera reciente",
                    "<font face='Courier' size='8'>git --version</font>",
                ],
            ],
            [3.6 * cm, 4.6 * cm, 7.3 * cm],
        ),
        p("7.2 Paso 1 — Obtener el código", "h2"),
        Paragraph(f"git clone {REPOSITORIO}.git<br/>cd Oleo-Lienzo", E["codigo"]),
        p("7.3 Paso 2 — Crear la base de datos", "h2"),
        Paragraph(
            "sudo -u postgres psql<br/>"
            "&nbsp;&nbsp;CREATE ROLE oleo WITH LOGIN PASSWORD 'una_contrasena_segura';<br/>"
            "&nbsp;&nbsp;CREATE DATABASE oleo_lienzo WITH OWNER = oleo ENCODING = 'UTF8';<br/>"
            "&nbsp;&nbsp;\\q",
            E["codigo"],
        ),
        p(
            "El esquema puede crearse de dos maneras, y ambas producen exactamente las mismas "
            "tablas: ejecutando el script SQL incluido, o dejando que la aplicación lo cree al "
            "arrancar. El script existe porque es un entregable exigido y porque permite revisar el "
            "esquema sin ejecutar nada."
        ),
        Paragraph("psql -U oleo -d oleo_lienzo -f backend/sql/schema_postgresql.sql", E["codigo"]),
        p("7.4 Paso 3 — Configurar el backend", "h2"),
        Paragraph(
            "cd backend<br/>"
            "python -m venv venv<br/>"
            "source venv/bin/activate      # en Windows:  venv\\Scripts\\activate<br/>"
            "pip install -r requirements.txt<br/>"
            "cp .env.example .env          # y editarlo (ver la tabla de abajo)",
            E["codigo"],
        ),
        p("7.5 Variables de entorno del backend", "h2"),
        p(
            "El archivo <font face='Courier' size='9'>.env</font> <b>no se versiona</b>: está en el "
            "<font face='Courier' size='9'>.gitignore</font> y solo se sube la plantilla "
            "<font face='Courier' size='9'>.env.example</font>. Ninguna credencial aparece en el "
            "código fuente."
        ),
        tabla(
            [
                ["Variable", "Obligatoria", "Para qué sirve"],
                [
                    "<font face='Courier' size='8'>DATABASE_URL</font>",
                    "Sí",
                    "Conexión a PostgreSQL. Formato: "
                    "<font face='Courier' size='8'>postgresql+psycopg://usuario:clave@host:5432/base</font>",
                ],
                [
                    "<font face='Courier' size='8'>JWT_SECRET_KEY</font>",
                    "Sí en producción",
                    "Clave de firma de los tokens. <b>No tiene valor por defecto en el código.</b> "
                    "En desarrollo se genera una efímera; en producción, si falta, la aplicación se "
                    "niega a arrancar.",
                ],
                [
                    "<font face='Courier' size='8'>CORS_ORIGINS</font>",
                    "Sí",
                    "Lista explícita de orígenes permitidos, separados por comas. No se acepta el "
                    "comodín <font face='Courier' size='8'>*</font>.",
                ],
                [
                    "<font face='Courier' size='8'>GROQ_API_KEY</font>",
                    "No",
                    "Clave del chatbot con IA. Si falta, el chatbot responde en modo local y lo "
                    "declara abiertamente.",
                ],
                [
                    "<font face='Courier' size='8'>STRIPE_SECRET_KEY</font>",
                    "No",
                    "Pasarela de pago en modo de prueba. Si falta, el módulo informa de que no está "
                    "configurado.",
                ],
                [
                    "<font face='Courier' size='8'>EMAIL_HOST</font> y afines",
                    "No",
                    "Servidor SMTP. Si falta, los correos se registran en el log en vez de enviarse.",
                ],
            ],
            [4.2 * cm, 2.6 * cm, 8.7 * cm],
        ),
        p("Para generar una clave de firma segura:"),
        Paragraph('python -c "import secrets; print(secrets.token_urlsafe(48))"', E["codigo"]),
        p("7.6 Paso 4 — Poblar la base y arrancar el backend", "h2"),
        Paragraph(
            "python seed.py            # datos de ejemplo y entrenamiento del modelo de IA<br/>"
            "uvicorn app.main:app --reload --port 8000",
            E["codigo"],
        ),
        p(
            "El script <font face='Courier' size='9'>seed.py</font> es idempotente: puede "
            "ejecutarse varias veces sin duplicar registros. Crea los permisos, los tres roles, "
            "cuatro usuarios de prueba, diez obras, cuatro servicios, ventas, facturas, pedidos y "
            "PQR de ejemplo, y entrena el modelo de sugerencia de precios."
        ),
        p("7.7 Paso 5 — Configurar y arrancar el frontend", "h2"),
        Paragraph(
            "cd frontend<br/>"
            "npm install<br/>"
            "cp .env.example .env      # ajustar VITE_API_URL si el backend no está en :8000<br/>"
            "npm run dev",
            E["codigo"],
        ),
        p("7.8 Comprobación de que todo quedó bien", "h2"),
        tabla(
            [
                ["Qué comprobar", "Dónde", "Qué se debe ver"],
                [
                    "La API responde",
                    "<font face='Courier' size='8'>http://localhost:8000/api/sistema/salud</font>",
                    "<font face='Courier' size='8'>{\"estado\":\"ok\"}</font>",
                ],
                [
                    "La documentación",
                    "<font face='Courier' size='8'>http://localhost:8000/docs</font>",
                    "Swagger con 60 operaciones",
                ],
                [
                    "El sitio web",
                    "<font face='Courier' size='8'>http://localhost:5173</font>",
                    "La galería con el carrusel",
                ],
                [
                    "El inicio de sesión",
                    "<font face='Courier' size='8'>/login</font>",
                    "Entrar con admin@oleoylienzo.com / Admin1234",
                ],
                [
                    "Las pruebas",
                    "<font face='Courier' size='8'>cd backend &amp;&amp; pytest -q</font>",
                    f"{TOTAL_PRUEBAS} passed",
                ],
            ],
            [3.5 * cm, 6.5 * cm, 5.5 * cm],
        ),
        p("7.9 Credenciales de prueba", "h2"),
        p(
            "Las crea <font face='Courier' size='9'>seed.py</font> y solo sirven en entorno de "
            "desarrollo. <b>Deben cambiarse antes de cualquier despliegue real.</b>"
        ),
        tabla(
            [
                ["Rol", "Correo", "Contraseña"],
                ["Administrador", "admin@oleoylienzo.com", "Admin1234"],
                ["Empleado", "empleado@oleoylienzo.com", "Empleado123"],
                ["Cliente", "cliente@oleoylienzo.com", "Cliente123"],
                ["Cliente", "carlos.mejia@ejemplo.com", "Cliente123"],
            ],
            [3.8 * cm, 6.7 * cm, 5 * cm],
        ),
    ]


def seccion_api():
    elementos, total = tabla_de_endpoints()
    return [
        PageBreak(),
        p("8. Documentación técnica de la API", "h1"),
        p(
            f"La API expone <b>{total} operaciones</b> repartidas en 14 recursos, todas bajo el "
            "prefijo <font face='Courier' size='9'>/api</font>. La documentación interactiva se "
            "genera sola y está disponible en "
            "<font face='Courier' size='9'>/docs</font> (Swagger UI) y "
            "<font face='Courier' size='9'>/redoc</font>."
        ),
        p("8.1 Cómo autenticarse", "h2"),
        p(
            "Las rutas protegidas esperan la cabecera "
            "<font face='Courier' size='9'>Authorization: Bearer &lt;token&gt;</font>. El token se "
            "obtiene del inicio de sesión y caduca a los 60 minutos."
        ),
        Paragraph(
            "# 1. Obtener el token<br/>"
            "curl -X POST http://localhost:8000/api/auth/login \\<br/>"
            "&nbsp;&nbsp;-H 'Content-Type: application/json' \\<br/>"
            '&nbsp;&nbsp;-d \'{"email":"admin@oleoylienzo.com","password":"Admin1234"}\'<br/>'
            "<br/>"
            "# Respuesta<br/>"
            '{ "access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer",<br/>'
            '&nbsp;&nbsp;"usuario": { "id": 1, "nombre": "Ana", "rol": "administrador" } }<br/>'
            "<br/>"
            "# 2. Usarlo en una ruta protegida<br/>"
            "curl http://localhost:8000/api/usuarios \\<br/>"
            "&nbsp;&nbsp;-H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIs...'",
            E["codigo"],
        ),
        p("8.2 Ejemplo completo: registrar una venta", "h2"),
        Paragraph(
            "POST /api/ventas<br/>"
            "Authorization: Bearer &lt;token de administrador o empleado&gt;<br/>"
            "<br/>"
            "{<br/>"
            '&nbsp;&nbsp;"cliente_id": 3,<br/>'
            '&nbsp;&nbsp;"detalles": [<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;{ "obra_id": 1, "cantidad": 1, "descuento": 0 },<br/>'
            '&nbsp;&nbsp;&nbsp;&nbsp;{ "servicio_id": 1, "cantidad": 1 }<br/>'
            "&nbsp;&nbsp;],<br/>"
            '&nbsp;&nbsp;"metodo_pago": "tarjeta"<br/>'
            "}<br/>"
            "<br/>"
            "201 Created<br/>"
            "{<br/>"
            '&nbsp;&nbsp;"id": 7, "numero": "V-2026-000007", "estado": "pendiente_pago",<br/>'
            '&nbsp;&nbsp;"subtotal": 1400000.00, "impuestos": 266000.00, "total": 1666000.00,<br/>'
            '&nbsp;&nbsp;"detalles": [ ... ]<br/>'
            "}",
            E["codigo"],
        ),
        p(
            "Obsérvese que el cliente <b>no envía</b> ni el número de venta, ni el estado, ni los "
            "importes: todo eso lo calcula y lo asigna el servidor. Los esquemas de entrada ni "
            "siquiera aceptan esos campos."
        ),
        p("8.3 Formato uniforme de los errores", "h2"),
        p(
            "Todos los errores de la API, sin excepción, comparten el mismo cuerpo. Eso permite al "
            "frontend tratarlos con un único bloque de código:"
        ),
        Paragraph(
            "404 Not Found<br/>"
            '{ "error": "NotFound", "detail": "Obra 999 no encontrada." }<br/>'
            "<br/>"
            "422 Unprocessable Content<br/>"
            '{ "error": "ValidationError",<br/>'
            '&nbsp;&nbsp;"detail": [ { "loc": ["query","page"], "msg": "Input should be &gt;= 1" } ] }<br/>'
            "<br/>"
            "409 Conflict<br/>"
            '{ "error": "Conflict", "detail": "Ya existe un usuario con ese correo." }',
            E["codigo"],
        ),
        p(
            "Además, cada respuesta incluye la cabecera "
            "<font face='Courier' size='9'>X-Request-ID</font>, que aparece también en el registro "
            "del servidor: permite localizar en el log exactamente la petición que falló."
        ),
        p("8.4 Catálogo completo de operaciones", "h2"),
        *elementos,
    ]


def seccion_manual_usuario():
    bloques = [
        PageBreak(),
        p("9. Manual de usuario", "h1"),
        p(
            "Esta sección recorre la aplicación desde la perspectiva de quien la usa. Las capturas "
            "se tomaron de la aplicación en funcionamiento con los datos de ejemplo que genera "
            "<font face='Courier' size='9'>seed.py</font>."
        ),
        p("9.1 Zona pública", "h2"),
        p(
            "Cualquiera puede recorrer la galería sin registrarse. La página de inicio presenta el "
            "carrusel con las diez obras de la colección; cada una muestra su título, su autor y su "
            "ficha técnica."
        ),
        *figura("01-inicio.png", "Página de inicio con el carrusel de obras."),
        p(
            "El catálogo permite filtrar por artista, técnica, disponibilidad y rango de precio, y "
            "buscar por texto. Los resultados se paginan."
        ),
        *figura("02-catalogo.png", "Catálogo con filtros y paginación."),
        *figura("04-contacto.png", "Formulario de contacto con validación en tiempo real."),
        p("9.2 Registro e inicio de sesión", "h2"),
        p(
            "El formulario de inicio de sesión valida mientras se escribe. El registro se abre en "
            "una ventana modal que puede cerrarse sin completar el proceso, con la tecla Escape, "
            "haciendo clic fuera o con el botón Cancelar."
        ),
        *figura("05-login.png", "Inicio de sesión con validación en tiempo real."),
        p(
            "Tras entrar, el nombre de la persona aparece en la barra de navegación junto al botón "
            "de salir, y el menú se adapta al rol."
        ),
        p("9.3 Panel del administrador", "h2"),
        p(
            "El dashboard reúne doce indicadores y cuatro gráficos, todos calculados en la base de "
            "datos. Los filtros de la parte superior —fechas, estado, obra, servicio y cliente— "
            "afectan a la vez a las tarjetas y a los gráficos."
        ),
        *figura(
            "06-panel-admin-dashboard.png",
            "Dashboard del administrador con filtros, indicadores y gráficos.",
        ),
        p(
            "El historial de ventas permite consultar por fecha, cliente, obra, servicio, estado y "
            "rango de valor, y cambiar el estado de cada venta respetando las transiciones válidas."
        ),
        *figura("07-panel-admin-ventas.png", "Historial de ventas con filtros y desglose de IVA."),
        p(
            "Desde facturación se emiten las facturas, se buscan por número, cliente o documento, y "
            "se descarga el PDF de cada una."
        ),
        *figura("08-panel-admin-facturas.png", "Facturación: consulta y descarga del PDF."),
        p(
            "El reporte diario de ventas se consulta en pantalla y se exporta en PDF o en Excel. El "
            "archivo de Excel incluye fórmulas y autofiltro para seguir analizando los datos."
        ),
        *figura("09-panel-admin-reportes.png", "Reporte diario con exportación a PDF y Excel."),
        *figura(
            "10-panel-admin-obras.png", "Gestión del catálogo, con sugerencia de precio por IA."
        ),
        *figura("11-panel-admin-usuarios.png", "Gestión de usuarios, roles y estado."),
        *figura("12-panel-admin-pqr.png", "Gestión de PQR con sus cuatro estados."),
        p("9.4 Panel del empleado", "h2"),
        p(
            "El empleado ve una versión recortada: seis indicadores en vez de doce, y sin acceso a "
            "la gestión de usuarios ni a los ingresos globales. La restricción no es solo visual: "
            "si intentara llamar directamente al endpoint de usuarios, el backend respondería 403."
        ),
        *figura("13-panel-empleado.png", "Panel del empleado, con alcance reducido."),
        p("9.5 Panel del cliente", "h2"),
        p(
            "El cliente ve únicamente su propia actividad: sus pedidos, sus compras, lo que lleva "
            "invertido, sus facturas y sus PQR abiertas."
        ),
        *figura("14-panel-cliente.png", "Panel del cliente con su actividad."),
        *figura("15-panel-cliente-pedidos.png", "Mis pedidos, con el detalle de cada uno."),
        p("9.6 Chatbot de atención", "h2"),
        p(
            "El botón flotante de la esquina inferior derecha abre el chatbot, disponible también "
            "para visitantes sin cuenta. Responde usando el catálogo real como contexto, orienta "
            "sobre el proceso de compra y recibe solicitudes de PQR. Cuando el proveedor de IA no "
            "está disponible, responde en modo local y <b>lo declara abiertamente</b> en vez de "
            "hacer pasar la respuesta de respaldo por una respuesta de la IA."
        ),
        p("9.7 Documentación interactiva de la API", "h2"),
        p(
            "En <font face='Courier' size='9'>/docs</font> puede probarse cada operación desde el "
            "navegador. El botón <b>Authorize</b> permite iniciar sesión y, a partir de ahí, las "
            "rutas protegidas envían el token automáticamente."
        ),
        *figura("16-swagger.png", "Documentación automática generada por FastAPI."),
    ]
    return bloques


def seccion_pruebas():
    return [
        PageBreak(),
        p("10. Pruebas realizadas", "h1"),
        p("10.1 Estrategia", "h2"),
        p(
            f"El proyecto cuenta con <b>{TOTAL_PRUEBAS} pruebas automatizadas</b> escritas con "
            "pytest, que se ejecutan contra la API completa mediante un cliente HTTP asíncrono. No "
            "prueban funciones sueltas: recorren el mismo camino que recorrería el navegador, desde "
            "la petición hasta la base de datos."
        ),
        p(
            "Dos decisiones hacen que la suite sea fiable. La primera: <b>cada prueba recibe una "
            "base de datos recién creada</b>, de modo que ninguna puede contaminar a la siguiente. "
            "La segunda: <b>las mismas pruebas se ejecutan sobre SQLite y sobre PostgreSQL</b>; "
            "SQLite por velocidad en el día a día, PostgreSQL porque es el motor real y hay "
            "diferencias de dialecto que solo aparecen allí."
        ),
        p("10.2 Qué cubre cada archivo", "h2"),
        tabla(
            [
                ["Archivo", "Qué verifica"],
                [
                    "<font face='Courier' size='8'>test_auth.py</font>",
                    "Registro con validaciones, correo y documento duplicados (409), inicio de "
                    "sesión, token caducado, firma manipulada y recuperación de contraseña.",
                ],
                [
                    "<font face='Courier' size='8'>test_usuarios.py</font>",
                    "CRUD completo, cambio de estado, que el administrador no pueda desactivarse a "
                    "sí mismo y que un cliente no acceda a la gestión de usuarios.",
                ],
                [
                    "<font face='Courier' size='8'>test_catalogo.py</font>",
                    "CRUD de obras y servicios, diferencia real entre PUT y PATCH, filtros, "
                    "paginación y 404 con mensaje claro.",
                ],
                [
                    "<font face='Courier' size='8'>test_comercial.py</font>",
                    "Pedidos, confirmación que genera la venta, cálculo del IVA, control de "
                    "inventario, máquinas de estado y emisión de facturas.",
                ],
                [
                    "<font face='Courier' size='8'>test_sistema_reportes.py</font>",
                    "Reporte diario en JSON, PDF y Excel; dashboards por rol; los seis filtros; y "
                    "que filtrar por obra no duplique los importes.",
                ],
                [
                    "<font face='Courier' size='8'>test_pqr_chatbot.py</font>",
                    "Radicación con radicado, transiciones de estado, respuesta del personal y "
                    "persistencia de las conversaciones del chatbot.",
                ],
                [
                    "<font face='Courier' size='8'>test_seguridad.py</font>",
                    "Cabeceras defensivas, limitación de intentos de inicio de sesión y formato "
                    "uniforme de los errores.",
                ],
                [
                    "<font face='Courier' size='8'>test_dobles_externos.py</font>",
                    "Groq y el modelo de IA sustituidos por dobles: respuesta correcta, tiempo de "
                    "espera agotado, HTTP 500, respuesta malformada, degradación declarada y que la "
                    "clave nunca viaje al cliente.",
                ],
            ],
            [4.6 * cm, 10.9 * cm],
        ),
        p("10.3 Casos de prueba destacados", "h2"),
        p(
            "Tres pruebas merecen mención porque protegen errores que serían difíciles de detectar "
            "a ojo:"
        ),
        *vinetas(
            [
                "<b>El filtro por obra no duplica los importes.</b> Si el filtro se resolviera con "
                "un JOIN al detalle, una venta de dos líneas aparecería dos veces y tanto el "
                "conteo como los totales se duplicarían. La prueba crea justamente esa venta y "
                "comprueba que el importe coincide exactamente.",
                "<b>Un cliente no puede espiar el dashboard de otro.</b> El endpoint acepta un "
                "parámetro <font face='Courier' size='9'>cliente_id</font>, pero para el rol "
                "cliente se ignora y se fuerza el propio. La prueba intenta el acceso cruzado y "
                "verifica que los datos devueltos son los suyos.",
                "<b>El chatbot no finge.</b> Cuando el proveedor de IA falla, el servicio responde "
                "con el modo local, y la prueba comprueba que "
                "<font face='Courier' size='9'>generado_por_ia</font> vale "
                "<font face='Courier' size='9'>false</font>: la aplicación no hace pasar una "
                "respuesta de respaldo por una respuesta de la inteligencia artificial.",
            ]
        ),
        p("10.4 Cómo ejecutarlas y qué resultado dan", "h2"),
        Paragraph(
            "cd backend<br/>"
            "source venv/bin/activate<br/>"
            "<br/>"
            "pytest -q                                    # sobre SQLite<br/>"
            f"# {TOTAL_PRUEBAS} passed<br/>"
            "<br/>"
            "TEST_DATABASE_URL=postgresql+psycopg://oleo:oleo@localhost:5432/oleo_test \\<br/>"
            "&nbsp;&nbsp;pytest -q                                  # sobre PostgreSQL<br/>"
            f"# {TOTAL_PRUEBAS} passed",
            E["codigo"],
        ),
        p(
            "<b>Advertencia importante:</b> la variable "
            "<font face='Courier' size='9'>TEST_DATABASE_URL</font> debe apuntar a una base de "
            "datos <i>distinta</i> de la de desarrollo. La suite borra y recrea las tablas en cada "
            "prueba, de modo que apuntarla a la base de trabajo destruiría sus datos."
        ),
        p("10.5 Pruebas manuales complementarias", "h2"),
        tabla(
            [
                ["Tipo", "Herramienta", "Alcance"],
                [
                    "Pruebas de la API",
                    "Postman",
                    "Colección de 60 peticiones, una por operación, con los cinco verbos.",
                ],
                [
                    "Recorrido de interfaz",
                    "Playwright + Chrome",
                    "Inicio de sesión con los tres roles y recorrido de todas las secciones.",
                ],
                [
                    "Inspección de la base",
                    "psql",
                    "Comprobación de tablas, restricciones y de que las contraseñas son hashes bcrypt.",
                ],
                [
                    "Estilo del código",
                    "ruff",
                    "Comprobación de estilo y formato en 86 archivos de Python.",
                ],
            ],
            [3.6 * cm, 4 * cm, 7.9 * cm],
        ),
    ]


def seccion_conclusiones():
    return [
        PageBreak(),
        p("11. Conclusiones y recomendaciones", "h1"),
        p("11.1 Aprendizajes del proceso", "h2"),
        *vinetas(
            [
                "<b>La validación no se delega al frontend.</b> Es cómodo pensar que si el "
                "formulario ya validó, el backend puede confiar. No es así: quien llame a la API "
                "directamente se salta el formulario entero. Cada dato se valida dos veces, y la "
                "que cuenta es la del servidor.",
                "<b>El dinero no se calcula con números de coma flotante.</b> Empezar con "
                "<font face='Courier' size='9'>float</font> y ver cómo las facturas se descuadraban "
                "por céntimos fue la lección más concreta del proyecto. Todo el cálculo monetario "
                "pasó a <font face='Courier' size='9'>Decimal</font> con redondeo explícito.",
                "<b>Separar las capas se paga solo cuando algo cambia.</b> Mantener la lógica de "
                "negocio fuera de las funciones de ruta parecía burocracia hasta que hubo que "
                "reutilizarla desde el seed y desde las tareas en segundo plano.",
                "<b>Una integración externa debe poder fallar.</b> El chatbot no se diseñó "
                "suponiendo que el proveedor responde siempre: se diseñó decidiendo qué hacer "
                "cuando no responde. Degradar y decirlo es mejor que quedarse en blanco, y mucho "
                "mejor que fingir.",
                "<b>Las pruebas no son un trámite final.</b> Las que más valor dieron fueron las "
                "que se escribieron al detectar un comportamiento dudoso, no las añadidas al final "
                "para subir la cobertura.",
            ]
        ),
        p("11.2 Limitaciones conocidas", "h2"),
        p(
            "Reconocerlas es parte del trabajo técnico; ocultarlas solo retrasa el momento en que "
            "aparecen."
        ),
        *vinetas(
            [
                "El chatbot depende de un proveedor externo con plan gratuito, sujeto a límites de "
                "uso. Cuando se agotan, responde el modo local.",
                "La generación de PDF y Excel es síncrona. Con reportes de miles de ventas "
                "convendría moverla a una tarea en segundo plano con descarga diferida.",
                "No hay migraciones de esquema (Alembic). Un cambio en los modelos exige recrear "
                "las tablas, lo cual es aceptable en formación pero no en producción.",
                "El modelo de sugerencia de precios es una regresión lineal con dos variables "
                "entrenada con diez obras. Ilustra la integración de un modelo propio; su precisión "
                "no es el objetivo.",
            ]
        ),
        p("11.3 Recomendaciones para una versión futura", "h2"),
        tabla(
            [
                ["Prioridad", "Recomendación", "Por qué"],
                [
                    "<b>Alta</b>",
                    "Incorporar Alembic para versionar el esquema.",
                    "Permite evolucionar la base en producción sin perder datos.",
                ],
                [
                    "<b>Alta</b>",
                    "Rotar las credenciales de prueba antes de cualquier uso real.",
                    "Las que crea el seed son públicas: están en este documento.",
                ],
                [
                    "<b>Media</b>",
                    "Mover la generación de reportes a una cola de tareas.",
                    "Evita bloquear la petición cuando el volumen crezca.",
                ],
                [
                    "<b>Media</b>",
                    "Añadir paginación por cursor en el historial de ventas.",
                    "El desplazamiento por OFFSET se degrada con muchas filas.",
                ],
                [
                    "<b>Media</b>",
                    "Registrar métricas y trazas del tiempo de respuesta.",
                    "Ya existe el X-Request-ID; falta explotarlo.",
                ],
                [
                    "<b>Baja</b>",
                    "Cachear el catálogo, que cambia poco y se consulta mucho.",
                    "Reduciría la carga de la base en la zona pública.",
                ],
            ],
            [2.2 * cm, 6.6 * cm, 6.7 * cm],
        ),
        p("11.4 Conclusión", "h2"),
        p(
            "El proyecto cumple el objetivo planteado: una aplicación web full stack, funcional y "
            "verificada, que cubre el ciclo comercial completo de una galería de arte —del catálogo "
            "a la factura— con seguridad basada en roles, analítica alimentada por la base de datos "
            "e inteligencia artificial integrada en dos frentes."
        ),
        p(
            f"Más allá de las funcionalidades, el resultado que mejor resume el trabajo es que "
            f"<b>{TOTAL_PRUEBAS} pruebas automatizadas pasan sobre dos motores de base de datos "
            "distintos</b>, y que cada afirmación de este manual puede comprobarse ejecutando el "
            "código. La documentación no describe lo que el proyecto pretendía ser: describe lo que "
            "hace, y deja a mano la forma de verificarlo."
        ),
    ]


def seccion_anexos():
    return [
        PageBreak(),
        p("12. Anexos", "h1"),
        p("12.1 Repositorio y estructura de entrega", "h2"),
        tabla(
            [
                ["Recurso", "Ubicación"],
                ["Repositorio", f"<font face='Courier' size='8'>{REPOSITORIO}</font>"],
                ["Backend", "<font face='Courier' size='8'>backend/</font>"],
                ["Frontend", "<font face='Courier' size='8'>frontend/</font>"],
                [
                    "Script SQL",
                    "<font face='Courier' size='8'>backend/sql/schema_postgresql.sql</font>",
                ],
                [
                    "Colección de Postman",
                    "<font face='Courier' size='8'>postman/Oleo-Lienzo.postman_collection.json</font>",
                ],
                ["Pruebas", "<font face='Courier' size='8'>backend/tests/</font>"],
                [
                    "Capturas de este manual",
                    "<font face='Courier' size='8'>docs/manual/capturas/</font>",
                ],
            ],
            [4.6 * cm, 10.9 * cm],
        ),
        p("12.2 Documentación complementaria en el repositorio", "h2"),
        tabla(
            [
                ["Documento", "Contenido"],
                [
                    "<font face='Courier' size='8'>README.md</font>",
                    "Instalación, ejecución, variables de entorno y estructura.",
                ],
                [
                    "<font face='Courier' size='8'>docs/diseno-api.md</font>",
                    "Tabla de diseño recurso–verbo–ruta–código de las 60 operaciones.",
                ],
                [
                    "<font face='Courier' size='8'>docs/matriz-cumplimiento.md</font>",
                    "Verificación requisito por requisito de los cinco entregables.",
                ],
                [
                    "<font face='Courier' size='8'>docs/comparativa-fastapi-drf.md</font>",
                    "Análisis comparativo entre FastAPI y Django REST Framework.",
                ],
                [
                    "<font face='Courier' size='8'>docs/despliegue.md</font>",
                    "Guía de despliegue en la nube paso a paso.",
                ],
                [
                    "<font face='Courier' size='8'>docs/evidencias.md</font>",
                    "Guion de sustentación y evidencias de funcionamiento.",
                ],
            ],
            [5.6 * cm, 9.9 * cm],
        ),
        p("12.3 Scripts de apoyo", "h2"),
        p(
            "Varios artefactos del proyecto se generan en vez de escribirse a mano, precisamente "
            "para que no puedan quedar desfasados respecto al código:"
        ),
        tabla(
            [
                ["Script", "Qué genera"],
                [
                    "<font face='Courier' size='8'>seed.py</font>",
                    "Datos de ejemplo y entrenamiento del modelo de IA.",
                ],
                [
                    "<font face='Courier' size='8'>scripts/generar_sql.py</font>",
                    "El script SQL, a partir de los modelos SQLAlchemy.",
                ],
                [
                    "<font face='Courier' size='8'>scripts/generar_postman.py</font>",
                    "La colección de Postman, desde el esquema OpenAPI.",
                ],
                [
                    "<font face='Courier' size='8'>scripts/generar_diseno_api.py</font>",
                    "La tabla de diseño de la API.",
                ],
                [
                    "<font face='Courier' size='8'>scripts/capturar_evidencias.py</font>",
                    "Las capturas de pantalla de este manual.",
                ],
                [
                    "<font face='Courier' size='8'>scripts/generar_manual_tecnico.py</font>",
                    "Este mismo documento.",
                ],
            ],
            [6.4 * cm, 9.1 * cm],
        ),
        p("12.4 Glosario", "h2"),
        tabla(
            [
                ["Término", "Significado en este proyecto"],
                [
                    "<b>JWT</b>",
                    "Token firmado que identifica al usuario en cada petición. Lleva su correo, su rol y su fecha de caducidad.",
                ],
                [
                    "<b>bcrypt</b>",
                    "Algoritmo de hashing de contraseñas con sal propia. Del hash almacenado no puede recuperarse la contraseña.",
                ],
                [
                    "<b>ORM</b>",
                    "Capa que traduce entre las tablas de la base y los objetos de Python. Aquí, SQLAlchemy.",
                ],
                [
                    "<b>Pydantic</b>",
                    "Biblioteca que valida los datos que entran y salen de la API a partir de anotaciones de tipo.",
                ],
                [
                    "<b>CORS</b>",
                    "Mecanismo del navegador que decide qué orígenes pueden llamar a la API. Aquí es una lista explícita.",
                ],
                [
                    "<b>PQR</b>",
                    "Peticiones, quejas y reclamos: el canal formal de atención al cliente.",
                ],
                [
                    "<b>Idempotente</b>",
                    "Que puede ejecutarse varias veces con el mismo resultado. El seed lo es.",
                ],
                [
                    "<b>Degradar</b>",
                    "Seguir funcionando con capacidad reducida cuando un servicio externo falla, en vez de romperse.",
                ],
            ],
            [3.2 * cm, 12.3 * cm],
        ),
        Spacer(1, 1.2 * cm),
        tabla(
            [
                ["_______________________________", "_______________________________"],
                [
                    f"<b>{APRENDIZ}</b><br/>Aprendiz · Ficha {FICHA}",
                    "<b>César Augusto Moreno Mena</b><br/>Instructor técnico",
                ],
            ],
            [7.7 * cm, 7.8 * cm],
            cabecera=False,
        ),
    ]


class ManualDocTemplate(BaseDocTemplate):
    """Documento que alimenta el índice a medida que coloca los títulos.

    `afterFlowable` se ejecuta cada vez que se asienta un elemento: cuando el
    elemento es un título, se le notifica al índice en qué página acabó. Por eso
    el documento se construye con `multiBuild`, que hace dos pasadas.
    """

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        estilo = flowable.style.name
        if estilo not in ("h1", "h2"):
            return
        texto = flowable.getPlainText()
        # La propia tabla de contenido no se indexa a sí misma.
        if texto.startswith("Tabla de contenido"):
            return
        nivel = 0 if estilo == "h1" else 1
        # Se resta 1 porque la portada no lleva número, igual que en el pie.
        self.notify("TOCEntry", (nivel, texto, self.page - 1))


# ═════════════════════════════════════════════════════════════════════════
#  ENSAMBLADO
# ═════════════════════════════════════════════════════════════════════════
def main() -> int:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)

    doc = ManualDocTemplate(
        str(DESTINO),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.0 * cm,
        title=f"Manual Técnico — {PROYECTO}",
        author=APRENDIZ,
        subject=f"Proyecto formativo · Ficha {FICHA}",
    )

    marco = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="portada", frames=[marco], onPage=decorar_portada),
            PageTemplate(id="contenido", frames=[marco], onPage=decorar_pagina),
        ]
    )

    historia = []
    historia += portada()
    historia.append(NextPageTemplate("contenido"))
    historia.append(PageBreak())
    historia += tabla_de_contenido()
    historia.append(PageBreak())
    historia += seccion_introduccion()
    historia.append(PageBreak())
    historia += seccion_objetivos()
    historia.append(PageBreak())
    historia += seccion_alcance()
    historia.append(PageBreak())
    historia += seccion_arquitectura()
    historia.append(PageBreak())
    historia += seccion_modelo_datos()
    historia += seccion_diseno()
    historia += seccion_instalacion()
    historia += seccion_api()
    historia += seccion_manual_usuario()
    historia += seccion_pruebas()
    historia += seccion_conclusiones()
    historia += seccion_anexos()

    # Dos pasadas: la primera averigua en qué página cae cada título, la
    # segunda escribe el índice ya con los números correctos.
    doc.multiBuild(historia)

    tam = DESTINO.stat().st_size / 1024
    print(f"\nGenerado {DESTINO}")
    print(f"  {tam:.0f} KB · {figura.contador} figuras\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
