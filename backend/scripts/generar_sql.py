"""Genera sql/schema_postgresql.sql a partir de los modelos SQLAlchemy.

Generarlo en vez de escribirlo a mano garantiza que el script SQL y los
modelos ORM nunca se desincronicen.
"""
import sys
sys.path.insert(0, "/home/user/Oleo-Lienzo/backend")

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

import app.models  # noqa: F401  registra todas las tablas
from app.core.security import hash_password
from app.database import Base
from seed import OBRAS, PERMISOS, PERMISOS_CLIENTE, PERMISOS_EMPLEADO, ROLES, SERVICIOS, USUARIOS

dialecto = postgresql.dialect()


def esc(valor) -> str:
    if valor is None:
        return "NULL"
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, (int, float)):
        return str(valor)
    return "'" + str(valor).replace("'", "''") + "'"


partes: list[str] = []

partes.append(f"""-- ═══════════════════════════════════════════════════════════════════════
--  ÓLEO & LIENZO — Script de creación de la base de datos (PostgreSQL)
--  Proyecto integrador React + Vite + FastAPI · Ficha 3406211 · SENA
-- ═══════════════════════════════════════════════════════════════════════
--
--  Genera el esquema completo y los datos iniciales.
--
--  USO
--    createdb -U postgres oleo_lienzo
--    psql -U postgres -d oleo_lienzo -f sql/schema_postgresql.sql
--
--  o bien, creando también el rol y la base (descomenta el bloque de abajo):
--    psql -U postgres -f sql/schema_postgresql.sql
--
--  CONTENIDO
--    {len(Base.metadata.sorted_tables)} tablas con claves primarias y foráneas,
--    restricciones CHECK y UNIQUE, columnas NOT NULL, índices y datos semilla.
--
--  NOTA  Este archivo se genera a partir de los modelos SQLAlchemy
--        (scripts/generar_sql.py), por lo que el esquema SQL y el ORM
--        siempre coinciden. No lo edites a mano.
-- ═══════════════════════════════════════════════════════════════════════

-- ── Creación del rol y la base de datos ────────────────────────────────
-- Descomenta estas líneas si aún no existen. Deben ejecutarse conectado a
-- otra base (por ejemplo `postgres`), no a `oleo_lienzo`.
--
-- CREATE ROLE oleo WITH LOGIN PASSWORD 'cambia_esta_contrasena';
-- CREATE DATABASE oleo_lienzo WITH OWNER = oleo ENCODING = 'UTF8';
-- \\connect oleo_lienzo

BEGIN;

-- ── Limpieza previa (permite reejecutar el script) ─────────────────────
""")

nombres = [t.name for t in reversed(Base.metadata.sorted_tables)]
partes.append("DROP TABLE IF EXISTS " + ", ".join(nombres) + " CASCADE;\n")

partes.append("""

-- ═══════════════════════════════════════════════════════════════════════
--  TABLAS
-- ═══════════════════════════════════════════════════════════════════════
""")

COMENTARIOS = {
    "roles": "Roles del sistema: administrador, empleado y cliente.",
    "permisos": "Acciones concretas que un rol puede realizar.",
    "rol_permisos": "Relación muchos a muchos entre roles y permisos.",
    "usuarios": "Usuarios del sistema. La contraseña se guarda solo como hash bcrypt.",
    "obras": "Catálogo de obras de arte (productos).",
    "servicios": "Servicios de la galería: enmarcado, restauración y envío.",
    "pedidos": "Órdenes que el cliente arma desde el sitio web.",
    "detalles_pedido": "Líneas de un pedido: una obra o un servicio por línea.",
    "ventas": "Transacciones comerciales con su desglose económico completo.",
    "detalle_ventas": "Líneas de una venta, con precio y descuento congelados.",
    "facturas": "Documentos fiscales emitidos a partir de una venta.",
    "pagos": "Pagos con Stripe. Solo referencias: ningún dato de tarjeta.",
    "pqr": "Peticiones, quejas, reclamos y sugerencias.",
    "conversaciones": "Conversaciones del chatbot con IA.",
    "mensajes": "Mensajes individuales de cada conversación.",
}

for tabla in Base.metadata.sorted_tables:
    comentario = COMENTARIOS.get(tabla.name, "")
    partes.append(f"\n-- ── {tabla.name} {'─' * max(0, 62 - len(tabla.name))}")
    if comentario:
        partes.append(f"-- {comentario}")
    ddl = str(CreateTable(tabla).compile(dialect=dialecto)).strip()
    partes.append(ddl + ";\n")

partes.append("""
-- ═══════════════════════════════════════════════════════════════════════
--  ÍNDICES
-- ═══════════════════════════════════════════════════════════════════════
""")
for tabla in Base.metadata.sorted_tables:
    for indice in sorted(tabla.indexes, key=lambda i: i.name):
        partes.append(str(CreateIndex(indice).compile(dialect=dialecto)).strip() + ";")

# ── Datos iniciales ──────────────────────────────────────────────────────
partes.append("""

-- ═══════════════════════════════════════════════════════════════════════
--  DATOS INICIALES
-- ═══════════════════════════════════════════════════════════════════════

-- ── Roles ──────────────────────────────────────────────────────────────""")
for indice, (nombre, descripcion) in enumerate(ROLES, start=1):
    partes.append(
        f"INSERT INTO roles (id, nombre, descripcion) VALUES "
        f"({indice}, {esc(nombre)}, {esc(descripcion)});"
    )

partes.append("\n-- ── Permisos ───────────────────────────────────────────────────────────")
indices_permiso = {}
for indice, (codigo, descripcion) in enumerate(PERMISOS, start=1):
    indices_permiso[codigo] = indice
    partes.append(
        f"INSERT INTO permisos (id, codigo, descripcion) VALUES "
        f"({indice}, {esc(codigo)}, {esc(descripcion)});"
    )

partes.append("""
-- ── Asignación de permisos a cada rol ──────────────────────────────────
-- El administrador tiene todos los permisos.""")
asignaciones = {
    1: [c for c, _ in PERMISOS],
    2: PERMISOS_EMPLEADO,
    3: PERMISOS_CLIENTE,
}
for rol_id, codigos in asignaciones.items():
    valores = ", ".join(f"({rol_id}, {indices_permiso[c]})" for c in codigos)
    partes.append(f"INSERT INTO rol_permisos (rol_id, permiso_id) VALUES {valores};")

partes.append("""
-- ── Usuarios de prueba ─────────────────────────────────────────────────
-- Las contraseñas se almacenan EXCLUSIVAMENTE como hash bcrypt.
-- Credenciales en claro (solo para pruebas):""")
for *_, email, password, rol in USUARIOS:
    partes.append(f"--   {rol:15} {email:28} {password}")
partes.append("")

rol_ids = {nombre: indice for indice, (nombre, _) in enumerate(ROLES, start=1)}
for indice, (nombre, apellido, tipo, doc, direccion, tel, email, password, rol) in enumerate(
    USUARIOS, start=1
):
    partes.append(
        "INSERT INTO usuarios (id, nombre, apellido, tipo_documento, numero_documento, "
        "direccion, telefono, email, password_hash, activo, rol_id, creado_en, actualizado_en)\n"
        f"VALUES ({indice}, {esc(nombre)}, {esc(apellido)}, {esc(tipo)}, {esc(doc)}, "
        f"{esc(direccion)}, {esc(tel)}, {esc(email)}, {esc(hash_password(password))}, "
        f"TRUE, {rol_ids[rol]}, NOW(), NOW());"
    )

partes.append("\n-- ── Catálogo de obras ──────────────────────────────────────────────────")
for indice, (titulo, artista, anio, tecnica, precio, descripcion) in enumerate(OBRAS, start=1):
    partes.append(
        "INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, "
        "imagen_url, disponible, stock, creado_en, actualizado_en)\n"
        f"VALUES ({indice}, {esc(titulo)}, {esc(artista)}, {anio}, {esc(tecnica)}, "
        f"{precio}, {esc(descripcion)}, NULL, TRUE, 1, NOW(), NOW());"
    )

partes.append("\n-- ── Servicios ──────────────────────────────────────────────────────────")
for indice, (nombre, descripcion, precio) in enumerate(SERVICIOS, start=1):
    partes.append(
        "INSERT INTO servicios (id, nombre, descripcion, precio, activo, creado_en, actualizado_en)\n"
        f"VALUES ({indice}, {esc(nombre)}, {esc(descripcion)}, {precio}, TRUE, NOW(), NOW());"
    )

partes.append("""

-- ═══════════════════════════════════════════════════════════════════════
--  SECUENCIAS
--  Los INSERT anteriores fijan el id a mano, así que hay que adelantar las
--  secuencias para que el siguiente registro no choque con uno existente.
-- ═══════════════════════════════════════════════════════════════════════""")
for tabla in ("roles", "permisos", "usuarios", "obras", "servicios"):
    partes.append(
        f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
        f"COALESCE((SELECT MAX(id) FROM {tabla}), 1));"
    )

partes.append("""
COMMIT;

-- ═══════════════════════════════════════════════════════════════════════
--  COMPROBACIÓN
--  Ejecuta esto tras el script para verificar que todo quedó creado:
--
--    SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1;
--    SELECT contype, count(*) FROM pg_constraint c
--      JOIN pg_class t ON t.oid = c.conrelid
--      JOIN pg_namespace n ON n.oid = t.relnamespace
--     WHERE n.nspname = 'public' GROUP BY contype;
--    SELECT email, rol_id, left(password_hash, 7) FROM usuarios;
-- ═══════════════════════════════════════════════════════════════════════
""")

destino = "/home/user/Oleo-Lienzo/backend/sql/schema_postgresql.sql"
with open(destino, "w") as f:
    f.write("\n".join(partes))
print(f"Generado {destino}")
