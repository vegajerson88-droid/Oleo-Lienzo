"""Puebla la base de datos con el catálogo de permisos y datos de prueba.

Uso:
    python seed.py

Es idempotente: se puede ejecutar varias veces sin duplicar registros.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import get_settings
from app.core.dinero import calcular_linea, calcular_totales
from app.core.security import hash_password
from app.database import AsyncSessionLocal, init_models
from app.models.detalle_venta import DetalleVenta
from app.models.obra import Obra
from app.models.pqr import PQR, EstadoPQR, TipoPQR
from app.models.rol import Permiso, Rol
from app.models.servicio import Servicio
from app.models.usuario import Usuario
from app.models.venta import EstadoVenta, MetodoPago, Venta
from app.services.ai_local import entrenar_y_guardar

settings = get_settings()

# ── Catálogo de permisos ─────────────────────────────────────────────────
PERMISOS = [
    ("usuarios.ver", "Consultar el listado de usuarios"),
    ("usuarios.crear", "Dar de alta usuarios"),
    ("usuarios.editar", "Modificar usuarios y su estado"),
    ("usuarios.eliminar", "Eliminar usuarios"),
    ("catalogo.ver", "Consultar obras y servicios"),
    ("catalogo.crear", "Crear obras y servicios"),
    ("catalogo.editar", "Modificar obras y servicios"),
    ("catalogo.eliminar", "Eliminar obras y servicios"),
    ("pedidos.ver", "Consultar pedidos"),
    ("pedidos.crear", "Crear pedidos"),
    ("pedidos.gestionar", "Cambiar el estado de los pedidos"),
    ("ventas.ver", "Consultar el historial de ventas"),
    ("ventas.crear", "Registrar ventas"),
    ("ventas.gestionar", "Cambiar el estado de las ventas"),
    ("facturas.ver", "Consultar y descargar facturas"),
    ("facturas.emitir", "Emitir facturas de venta"),
    ("reportes.ver", "Generar reportes en PDF y Excel"),
    ("pqr.crear", "Radicar PQR"),
    ("pqr.ver", "Consultar PQR"),
    ("pqr.gestionar", "Responder y cambiar el estado de las PQR"),
    ("dashboard.ver", "Acceder al dashboard"),
    ("sistema.diagnostico", "Ejecutar el diagnóstico del sistema"),
    ("ia.usar", "Usar las sugerencias de IA del catálogo"),
]

# Qué puede hacer cada rol. El administrador los tiene todos.
PERMISOS_EMPLEADO = [
    "catalogo.ver",
    "catalogo.crear",
    "catalogo.editar",
    "pedidos.ver",
    "pedidos.gestionar",
    "ventas.ver",
    "ventas.crear",
    "ventas.gestionar",
    "facturas.ver",
    "facturas.emitir",
    "reportes.ver",
    "pqr.ver",
    "pqr.gestionar",
    "dashboard.ver",
    "ia.usar",
]
PERMISOS_CLIENTE = [
    "catalogo.ver",
    "pedidos.ver",
    "pedidos.crear",
    "ventas.ver",
    "facturas.ver",
    "pqr.crear",
    "pqr.ver",
    "dashboard.ver",
]

ROLES = [
    ("administrador", "Control total del sistema"),
    ("empleado", "Gestión operativa del catálogo, pedidos, ventas y PQR"),
    ("cliente", "Compra obras y servicios y hace seguimiento a sus pedidos"),
]

# ── Datos de ejemplo ─────────────────────────────────────────────────────
OBRAS = [
    (
        "Amanecer en el Valle",
        "Marina Solórzano",
        2021,
        "Óleo sobre lienzo",
        1250000,
        "Pinceladas cálidas que capturan la luz del primer sol sobre un valle en calma.",
    ),
    (
        "Fragmentos Azules",
        "Iván Restrepo",
        2019,
        "Acrílico sobre lienzo",
        980000,
        "Una composición geométrica que descompone el horizonte en planos de azul profundo.",
    ),
    (
        "Tormenta Interior",
        "Camila Duarte",
        2022,
        "Óleo sobre lienzo",
        1480000,
        "Trazos densos y oscuros que expresan la tensión emocional de una tormenta contenida.",
    ),
    (
        "Jardín Silencioso",
        "Marina Solórzano",
        2020,
        "Acrílico sobre lienzo",
        890000,
        "Formas orgánicas en tonos verdes que evocan la quietud de un jardín al amanecer.",
    ),
    (
        "Geometría del Deseo",
        "Tomás Aguilar",
        2023,
        "Óleo sobre lienzo",
        1650000,
        "Bloques rotundos en rojo y negro que juegan con el equilibrio y la tensión visual.",
    ),
    (
        "Ecos de Otoño",
        "Camila Duarte",
        2018,
        "Óleo sobre lienzo",
        1020000,
        "Capas cálidas de ocre y siena que rememoran la caída de las hojas en octubre.",
    ),
    (
        "Mar Interior",
        "Iván Restrepo",
        2021,
        "Acrílico sobre lienzo",
        1150000,
        "Curvas en azul turquesa que sugieren el movimiento constante de las mareas.",
    ),
    (
        "Retrato en Ocre",
        "Tomás Aguilar",
        2022,
        "Óleo sobre lienzo",
        1780000,
        "Un rostro sugerido entre bloques de tierra y sombra, entre lo figurativo y lo abstracto.",
    ),
    (
        "Nocturno",
        "Marina Solórzano",
        2023,
        "Óleo sobre lienzo",
        1920000,
        "Un cielo profundo salpicado de luz dorada, homenaje a las noches sin ciudad.",
    ),
    (
        "Primavera Fragmentada",
        "Camila Duarte",
        2020,
        "Acrílico sobre lienzo",
        970000,
        "Pétalos de rosa y verde dispersos en una composición ligera y luminosa.",
    ),
]

SERVICIOS = [
    ("Enmarcado personalizado", "Enmarcado a medida para obras adquiridas en la galería.", 150000),
    ("Restauración básica", "Limpieza y restauración leve de obras sobre lienzo.", 300000),
    (
        "Envío asegurado",
        "Transporte de la obra con embalaje especializado y seguro incluido.",
        90000,
    ),
    ("Asesoría de curaduría", "Acompañamiento para armar una colección coherente.", 250000),
]

USUARIOS = [
    (
        "Ana",
        "Restrepo",
        "CC",
        "1000000001",
        "Calle 10 # 20-30",
        "3001234567",
        "admin@oleoylienzo.com",
        "Admin1234",
        "administrador",
    ),
    (
        "Luis",
        "Gómez",
        "CC",
        "1000000002",
        "Carrera 45 # 12-05",
        "3007654321",
        "empleado@oleoylienzo.com",
        "Empleado123",
        "empleado",
    ),
    (
        "Sara",
        "Pérez",
        "CC",
        "1000000003",
        "Avenida Siempre Viva 742",
        "3009876543",
        "cliente@oleoylienzo.com",
        "Cliente123",
        "cliente",
    ),
    (
        "Carlos",
        "Mejía",
        "CC",
        "1000000004",
        "Calle 80 # 15-22",
        "3005551122",
        "carlos.mejia@ejemplo.com",
        "Cliente123",
        "cliente",
    ),
]


async def _sembrar_permisos_y_roles(db) -> dict[str, Rol]:
    permisos: dict[str, Permiso] = {}
    for codigo, descripcion in PERMISOS:
        existente = (
            await db.execute(select(Permiso).where(Permiso.codigo == codigo))
        ).scalar_one_or_none()
        if not existente:
            existente = Permiso(codigo=codigo, descripcion=descripcion)
            db.add(existente)
            await db.flush()
        permisos[codigo] = existente

    roles: dict[str, Rol] = {}
    for nombre, descripcion in ROLES:
        existente = (await db.execute(select(Rol).where(Rol.nombre == nombre))).scalar_one_or_none()
        if not existente:
            existente = Rol(nombre=nombre, descripcion=descripcion)
            # Inicializa la colección explícitamente: en un objeto recién
            # creado, leer `.permisos` dispararía una carga diferida que en
            # modo asíncrono falla con MissingGreenlet.
            existente.permisos = []
            db.add(existente)
            await db.flush()
        roles[nombre] = existente

    asignaciones = {
        "administrador": list(permisos.keys()),
        "empleado": PERMISOS_EMPLEADO,
        "cliente": PERMISOS_CLIENTE,
    }
    for nombre_rol, codigos in asignaciones.items():
        rol = roles[nombre_rol]
        actuales = {p.codigo for p in rol.permisos}
        for codigo in codigos:
            if codigo not in actuales:
                rol.permisos.append(permisos[codigo])

    await db.commit()
    return roles


async def _sembrar_usuarios(db, roles) -> dict[str, Usuario]:
    creados: dict[str, Usuario] = {}
    for nombre, apellido, tipo, doc, direccion, tel, email, password, rol in USUARIOS:
        existente = (
            await db.execute(select(Usuario).where(Usuario.email == email))
        ).scalar_one_or_none()
        if not existente:
            existente = Usuario(
                nombre=nombre,
                apellido=apellido,
                tipo_documento=tipo,
                numero_documento=doc,
                direccion=direccion,
                telefono=tel,
                email=email,
                password_hash=hash_password(password),
                rol_id=roles[rol].id,
            )
            db.add(existente)
            await db.flush()
        creados[email] = existente
    await db.commit()
    return creados


async def _sembrar_catalogo(db) -> tuple[list[Obra], list[Servicio]]:
    if (await db.execute(select(Obra))).scalars().first() is None:
        for titulo, artista, anio, tecnica, precio, descripcion in OBRAS:
            db.add(
                Obra(
                    titulo=titulo,
                    artista=artista,
                    anio=anio,
                    tecnica=tecnica,
                    precio=precio,
                    descripcion=descripcion,
                    stock=1,
                    disponible=True,
                )
            )
        await db.commit()

    if (await db.execute(select(Servicio))).scalars().first() is None:
        for nombre, descripcion, precio in SERVICIOS:
            db.add(Servicio(nombre=nombre, descripcion=descripcion, precio=precio))
        await db.commit()

    obras = list((await db.execute(select(Obra).order_by(Obra.id))).scalars().all())
    servicios = list((await db.execute(select(Servicio).order_by(Servicio.id))).scalars().all())
    return obras, servicios


async def _sembrar_ventas(db, usuarios, obras, servicios) -> None:
    """Crea ventas de ejemplo repartidas en los últimos días.

    Sirven para que los dashboards y el reporte diario tengan datos reales
    que mostrar desde el primer arranque.
    """
    if (await db.execute(select(Venta))).scalars().first() is not None:
        return

    clientes = [usuarios["cliente@oleoylienzo.com"], usuarios["carlos.mejia@ejemplo.com"]]
    empleado = usuarios["empleado@oleoylienzo.com"]
    ahora = datetime.now(timezone.utc)

    plantillas = [
        (
            0,
            clientes[0],
            [(obras[0], 1), (servicios[0], 1)],
            EstadoVenta.pagada,
            MetodoPago.tarjeta,
        ),
        (0, clientes[1], [(obras[1], 1)], EstadoVenta.pendiente_pago, MetodoPago.transferencia),
        (
            1,
            clientes[0],
            [(obras[2], 1), (servicios[2], 1)],
            EstadoVenta.pagada,
            MetodoPago.tarjeta,
        ),
        (2, clientes[1], [(obras[3], 1)], EstadoVenta.pagada, MetodoPago.efectivo),
        (
            3,
            clientes[0],
            [(obras[4], 1), (servicios[1], 1)],
            EstadoVenta.pagada,
            MetodoPago.tarjeta,
        ),
        (5, clientes[1], [(obras[5], 1)], EstadoVenta.anulada, MetodoPago.efectivo),
    ]

    for dias_atras, cliente, items, estado, metodo in plantillas:
        lineas = []
        for producto, cantidad in items:
            es_obra = isinstance(producto, Obra)
            descripcion = f"{producto.titulo} — {producto.artista}" if es_obra else producto.nombre
            lineas.append(
                DetalleVenta(
                    obra_id=producto.id if es_obra else None,
                    servicio_id=None if es_obra else producto.id,
                    descripcion=descripcion,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    descuento=0,
                    subtotal=calcular_linea(producto.precio, cantidad),
                )
            )

        totales = calcular_totales([linea.subtotal for linea in lineas], 0, settings.iva_tasa)
        momento = ahora - timedelta(days=dias_atras, hours=dias_atras * 2)
        venta = Venta(
            numero="",
            cliente_id=cliente.id,
            usuario_id=empleado.id,
            estado=estado,
            metodo_pago=metodo,
            subtotal=totales["subtotal"],
            descuento=totales["descuento"],
            impuestos=totales["impuestos"],
            total=totales["total"],
            creado_en=momento,
            actualizado_en=momento,
            observaciones="Venta de ejemplo generada por seed.py.",
        )
        venta.detalles = lineas
        db.add(venta)
        await db.flush()
        venta.numero = f"V-{momento.year}-{venta.id:06d}"

        # Las obras vendidas y no anuladas salen del inventario.
        if estado != EstadoVenta.anulada:
            for producto, cantidad in items:
                if isinstance(producto, Obra):
                    producto.stock = max(0, producto.stock - cantidad)
                    producto.disponible = producto.stock > 0

    await db.commit()


async def _sembrar_pqr(db, usuarios) -> None:
    if (await db.execute(select(PQR))).scalars().first() is not None:
        return

    cliente = usuarios["cliente@oleoylienzo.com"]
    ejemplos = [
        (
            TipoPQR.peticion,
            "Solicitud de certificado de autenticidad",
            "Quisiera recibir de nuevo el certificado de autenticidad de mi última compra.",
            EstadoPQR.pendiente,
        ),
        (
            TipoPQR.queja,
            "Demora en la entrega",
            "El pedido tardó más de lo indicado en llegar a mi dirección.",
            EstadoPQR.en_proceso,
        ),
    ]
    for tipo, asunto, mensaje, estado in ejemplos:
        pqr = PQR(
            radicado="",
            cliente_id=cliente.id,
            contacto_nombre=f"{cliente.nombre} {cliente.apellido}",
            contacto_email=cliente.email,
            tipo=tipo,
            asunto=asunto,
            mensaje=mensaje,
            estado=estado,
        )
        db.add(pqr)
        await db.flush()
        pqr.radicado = f"PQR-{pqr.id:06d}"
    await db.commit()


async def seed() -> None:
    await init_models()
    async with AsyncSessionLocal() as db:
        roles = await _sembrar_permisos_y_roles(db)
        usuarios = await _sembrar_usuarios(db, roles)
        obras, servicios = await _sembrar_catalogo(db)
        await _sembrar_ventas(db, usuarios, obras, servicios)
        await _sembrar_pqr(db, usuarios)

    # Entrena el modelo de sugerencia de precios con el catálogo real.
    entrenar_y_guardar([{"anio": a, "tecnica": t, "precio": p} for _, _, a, t, p, _ in OBRAS])

    print("\n" + "─" * 62)
    print("  Seed completado")
    print("─" * 62)
    print(f"  {len(PERMISOS)} permisos · {len(ROLES)} roles · {len(USUARIOS)} usuarios")
    print(f"  {len(OBRAS)} obras · {len(SERVICIOS)} servicios · ventas y PQR de ejemplo")
    print("  Modelo de IA local entrenado (modelo_precio.joblib)")
    print("─" * 62)
    print("  Credenciales de prueba:")
    for *_, email, password, rol in USUARIOS:
        print(f"    {rol:15} {email:28} {password}")
    print("─" * 62 + "\n")


if __name__ == "__main__":
    asyncio.run(seed())
