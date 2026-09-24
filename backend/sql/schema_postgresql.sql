-- ═══════════════════════════════════════════════════════════════════════
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
--    15 tablas con claves primarias y foráneas,
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
-- \connect oleo_lienzo

BEGIN;

-- ── Limpieza previa (permite reejecutar el script) ─────────────────────

DROP TABLE IF EXISTS pagos, facturas, detalle_ventas, ventas, mensajes, detalles_pedido, pqr, pedidos, conversaciones, usuarios, rol_permisos, servicios, roles, permisos, obras CASCADE;



-- ═══════════════════════════════════════════════════════════════════════
--  TABLAS
-- ═══════════════════════════════════════════════════════════════════════


-- ── obras ─────────────────────────────────────────────────────────
-- Catálogo de obras de arte (productos).
CREATE TABLE obras (
	id SERIAL NOT NULL, 
	titulo VARCHAR(120) NOT NULL, 
	artista VARCHAR(80) NOT NULL, 
	anio INTEGER NOT NULL, 
	tecnica VARCHAR(80) NOT NULL, 
	precio NUMERIC(12, 2) NOT NULL, 
	descripcion TEXT NOT NULL, 
	imagen_url VARCHAR(255), 
	disponible BOOLEAN NOT NULL, 
	stock INTEGER NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_obras_precio_positivo CHECK (precio > 0), 
	CONSTRAINT ck_obras_stock_no_negativo CHECK (stock >= 0), 
	CONSTRAINT ck_obras_anio_minimo CHECK (anio >= 1400)
);


-- ── permisos ──────────────────────────────────────────────────────
-- Acciones concretas que un rol puede realizar.
CREATE TABLE permisos (
	id SERIAL NOT NULL, 
	codigo VARCHAR(60) NOT NULL, 
	descripcion VARCHAR(160) NOT NULL, 
	PRIMARY KEY (id)
);


-- ── roles ─────────────────────────────────────────────────────────
-- Roles del sistema: administrador, empleado y cliente.
CREATE TABLE roles (
	id SERIAL NOT NULL, 
	nombre VARCHAR(30) NOT NULL, 
	descripcion VARCHAR(160), 
	PRIMARY KEY (id), 
	UNIQUE (nombre)
);


-- ── servicios ─────────────────────────────────────────────────────
-- Servicios de la galería: enmarcado, restauración y envío.
CREATE TABLE servicios (
	id SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	descripcion TEXT NOT NULL, 
	precio NUMERIC(12, 2) NOT NULL, 
	activo BOOLEAN NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_servicios_precio_positivo CHECK (precio > 0), 
	UNIQUE (nombre)
);


-- ── rol_permisos ──────────────────────────────────────────────────
-- Relación muchos a muchos entre roles y permisos.
CREATE TABLE rol_permisos (
	rol_id INTEGER NOT NULL, 
	permiso_id INTEGER NOT NULL, 
	PRIMARY KEY (rol_id, permiso_id), 
	FOREIGN KEY(rol_id) REFERENCES roles (id) ON DELETE CASCADE, 
	FOREIGN KEY(permiso_id) REFERENCES permisos (id) ON DELETE CASCADE
);


-- ── usuarios ──────────────────────────────────────────────────────
-- Usuarios del sistema. La contraseña se guarda solo como hash bcrypt.
CREATE TABLE usuarios (
	id SERIAL NOT NULL, 
	nombre VARCHAR(40) NOT NULL, 
	apellido VARCHAR(40) NOT NULL, 
	tipo_documento VARCHAR(5) NOT NULL, 
	numero_documento VARCHAR(15) NOT NULL, 
	direccion VARCHAR(100) NOT NULL, 
	telefono VARCHAR(10) NOT NULL, 
	email VARCHAR(80) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	activo BOOLEAN NOT NULL, 
	rol_id INTEGER NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rol_id) REFERENCES roles (id) ON DELETE RESTRICT
);


-- ── conversaciones ────────────────────────────────────────────────
-- Conversaciones del chatbot con IA.
CREATE TABLE conversaciones (
	id SERIAL NOT NULL, 
	session_id VARCHAR(64) NOT NULL, 
	usuario_id INTEGER, 
	titulo VARCHAR(140) NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
);


-- ── pedidos ───────────────────────────────────────────────────────
-- Órdenes que el cliente arma desde el sitio web.
CREATE TABLE pedidos (
	id SERIAL NOT NULL, 
	cliente_id INTEGER NOT NULL, 
	estado VARCHAR(20) NOT NULL, 
	total NUMERIC(12, 2) NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_pedidos_total_no_negativo CHECK (total >= 0), 
	FOREIGN KEY(cliente_id) REFERENCES usuarios (id) ON DELETE RESTRICT
);


-- ── pqr ───────────────────────────────────────────────────────────
-- Peticiones, quejas, reclamos y sugerencias.
CREATE TABLE pqr (
	id SERIAL NOT NULL, 
	radicado VARCHAR(24) NOT NULL, 
	cliente_id INTEGER, 
	contacto_nombre VARCHAR(90) NOT NULL, 
	contacto_email VARCHAR(80) NOT NULL, 
	tipo VARCHAR(20) NOT NULL, 
	asunto VARCHAR(140) NOT NULL, 
	mensaje TEXT NOT NULL, 
	estado VARCHAR(20) NOT NULL, 
	respuesta TEXT, 
	respondido_por_id INTEGER, 
	respondido_en TIMESTAMP WITH TIME ZONE, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(cliente_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
	FOREIGN KEY(respondido_por_id) REFERENCES usuarios (id) ON DELETE SET NULL
);


-- ── detalles_pedido ───────────────────────────────────────────────
-- Líneas de un pedido: una obra o un servicio por línea.
CREATE TABLE detalles_pedido (
	id SERIAL NOT NULL, 
	pedido_id INTEGER NOT NULL, 
	obra_id INTEGER, 
	servicio_id INTEGER, 
	descripcion VARCHAR(160) NOT NULL, 
	cantidad INTEGER NOT NULL, 
	precio_unitario NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_detalles_pedido_cantidad_positiva CHECK (cantidad > 0), 
	CONSTRAINT ck_detalles_pedido_precio_no_negativo CHECK (precio_unitario >= 0), 
	CONSTRAINT ck_detalles_pedido_obra_xor_servicio CHECK ((obra_id IS NOT NULL AND servicio_id IS NULL) OR (obra_id IS NULL AND servicio_id IS NOT NULL)), 
	FOREIGN KEY(pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE, 
	FOREIGN KEY(obra_id) REFERENCES obras (id) ON DELETE RESTRICT, 
	FOREIGN KEY(servicio_id) REFERENCES servicios (id) ON DELETE RESTRICT
);


-- ── mensajes ──────────────────────────────────────────────────────
-- Mensajes individuales de cada conversación.
CREATE TABLE mensajes (
	id SERIAL NOT NULL, 
	conversacion_id INTEGER NOT NULL, 
	rol VARCHAR(20) NOT NULL, 
	contenido TEXT NOT NULL, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversacion_id) REFERENCES conversaciones (id) ON DELETE CASCADE
);


-- ── ventas ────────────────────────────────────────────────────────
-- Transacciones comerciales con su desglose económico completo.
CREATE TABLE ventas (
	id SERIAL NOT NULL, 
	numero VARCHAR(24) NOT NULL, 
	cliente_id INTEGER NOT NULL, 
	usuario_id INTEGER, 
	pedido_id INTEGER, 
	estado VARCHAR(20) NOT NULL, 
	metodo_pago VARCHAR(20) NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	descuento NUMERIC(12, 2) NOT NULL, 
	impuestos NUMERIC(12, 2) NOT NULL, 
	total NUMERIC(12, 2) NOT NULL, 
	observaciones TEXT, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_ventas_subtotal_no_negativo CHECK (subtotal >= 0), 
	CONSTRAINT ck_ventas_descuento_no_negativo CHECK (descuento >= 0), 
	CONSTRAINT ck_ventas_impuestos_no_negativo CHECK (impuestos >= 0), 
	CONSTRAINT ck_ventas_total_no_negativo CHECK (total >= 0), 
	CONSTRAINT ck_ventas_descuento_max CHECK (descuento <= subtotal), 
	FOREIGN KEY(cliente_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
	UNIQUE (pedido_id), 
	FOREIGN KEY(pedido_id) REFERENCES pedidos (id) ON DELETE SET NULL
);


-- ── detalle_ventas ────────────────────────────────────────────────
-- Líneas de una venta, con precio y descuento congelados.
CREATE TABLE detalle_ventas (
	id SERIAL NOT NULL, 
	venta_id INTEGER NOT NULL, 
	obra_id INTEGER, 
	servicio_id INTEGER, 
	descripcion VARCHAR(160) NOT NULL, 
	cantidad INTEGER NOT NULL, 
	precio_unitario NUMERIC(12, 2) NOT NULL, 
	descuento NUMERIC(12, 2) NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_detalle_ventas_cantidad_positiva CHECK (cantidad > 0), 
	CONSTRAINT ck_detalle_ventas_precio_no_negativo CHECK (precio_unitario >= 0), 
	CONSTRAINT ck_detalle_ventas_descuento_no_negativo CHECK (descuento >= 0), 
	CONSTRAINT ck_detalle_ventas_subtotal_no_negativo CHECK (subtotal >= 0), 
	CONSTRAINT ck_detalle_ventas_obra_xor_servicio CHECK ((obra_id IS NOT NULL AND servicio_id IS NULL) OR (obra_id IS NULL AND servicio_id IS NOT NULL)), 
	FOREIGN KEY(venta_id) REFERENCES ventas (id) ON DELETE CASCADE, 
	FOREIGN KEY(obra_id) REFERENCES obras (id) ON DELETE RESTRICT, 
	FOREIGN KEY(servicio_id) REFERENCES servicios (id) ON DELETE RESTRICT
);


-- ── facturas ──────────────────────────────────────────────────────
-- Documentos fiscales emitidos a partir de una venta.
CREATE TABLE facturas (
	id SERIAL NOT NULL, 
	numero VARCHAR(24) NOT NULL, 
	venta_id INTEGER NOT NULL, 
	cliente_id INTEGER NOT NULL, 
	estado VARCHAR(20) NOT NULL, 
	fecha_emision TIMESTAMP WITH TIME ZONE NOT NULL, 
	cliente_nombre VARCHAR(90) NOT NULL, 
	cliente_documento VARCHAR(25) NOT NULL, 
	cliente_email VARCHAR(80) NOT NULL, 
	cliente_direccion VARCHAR(100) NOT NULL, 
	cliente_telefono VARCHAR(15) NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	descuento NUMERIC(12, 2) NOT NULL, 
	impuestos NUMERIC(12, 2) NOT NULL, 
	iva_porcentaje NUMERIC(5, 2) NOT NULL, 
	total NUMERIC(12, 2) NOT NULL, 
	observaciones TEXT, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_facturas_subtotal_no_negativo CHECK (subtotal >= 0), 
	CONSTRAINT ck_facturas_total_no_negativo CHECK (total >= 0), 
	UNIQUE (venta_id), 
	FOREIGN KEY(venta_id) REFERENCES ventas (id) ON DELETE CASCADE, 
	FOREIGN KEY(cliente_id) REFERENCES usuarios (id) ON DELETE RESTRICT
);


-- ── pagos ─────────────────────────────────────────────────────────
-- Pagos con Stripe. Solo referencias: ningún dato de tarjeta.
CREATE TABLE pagos (
	id SERIAL NOT NULL, 
	venta_id INTEGER NOT NULL, 
	proveedor VARCHAR(30) NOT NULL, 
	referencia_externa VARCHAR(255), 
	payment_intent VARCHAR(255), 
	estado VARCHAR(20) NOT NULL, 
	monto NUMERIC(12, 2) NOT NULL, 
	moneda VARCHAR(6) NOT NULL, 
	detalle TEXT, 
	creado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	actualizado_en TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_pagos_monto_no_negativo CHECK (monto >= 0), 
	FOREIGN KEY(venta_id) REFERENCES ventas (id) ON DELETE CASCADE
);


-- ═══════════════════════════════════════════════════════════════════════
--  ÍNDICES
-- ═══════════════════════════════════════════════════════════════════════

CREATE INDEX ix_obras_artista ON obras (artista);
CREATE INDEX ix_obras_disponible ON obras (disponible);
CREATE UNIQUE INDEX ix_permisos_codigo ON permisos (codigo);
CREATE UNIQUE INDEX ix_usuarios_email ON usuarios (email);
CREATE UNIQUE INDEX ix_usuarios_numero_documento ON usuarios (numero_documento);
CREATE INDEX ix_usuarios_rol_activo ON usuarios (rol_id, activo);
CREATE INDEX ix_conversaciones_session_id ON conversaciones (session_id);
CREATE INDEX ix_conversaciones_usuario_id ON conversaciones (usuario_id);
CREATE INDEX ix_pedidos_cliente_estado ON pedidos (cliente_id, estado);
CREATE INDEX ix_pedidos_cliente_id ON pedidos (cliente_id);
CREATE INDEX ix_pqr_cliente_id ON pqr (cliente_id);
CREATE INDEX ix_pqr_estado_creado ON pqr (estado, creado_en);
CREATE UNIQUE INDEX ix_pqr_radicado ON pqr (radicado);
CREATE INDEX ix_detalles_pedido_pedido_id ON detalles_pedido (pedido_id);
CREATE INDEX ix_mensajes_conversacion_id ON mensajes (conversacion_id);
CREATE INDEX ix_ventas_cliente_creado ON ventas (cliente_id, creado_en);
CREATE INDEX ix_ventas_cliente_id ON ventas (cliente_id);
CREATE INDEX ix_ventas_creado_estado ON ventas (creado_en, estado);
CREATE UNIQUE INDEX ix_ventas_numero ON ventas (numero);
CREATE INDEX ix_detalle_ventas_obra_id ON detalle_ventas (obra_id);
CREATE INDEX ix_detalle_ventas_servicio_id ON detalle_ventas (servicio_id);
CREATE INDEX ix_detalle_ventas_venta_id ON detalle_ventas (venta_id);
CREATE INDEX ix_facturas_cliente_id ON facturas (cliente_id);
CREATE INDEX ix_facturas_fecha_emision ON facturas (fecha_emision);
CREATE UNIQUE INDEX ix_facturas_numero ON facturas (numero);
CREATE INDEX ix_pagos_referencia_externa ON pagos (referencia_externa);
CREATE INDEX ix_pagos_venta_id ON pagos (venta_id);


-- ═══════════════════════════════════════════════════════════════════════
--  DATOS INICIALES
-- ═══════════════════════════════════════════════════════════════════════

-- ── Roles ──────────────────────────────────────────────────────────────
INSERT INTO roles (id, nombre, descripcion) VALUES (1, 'administrador', 'Control total del sistema');
INSERT INTO roles (id, nombre, descripcion) VALUES (2, 'empleado', 'Gestión operativa del catálogo, pedidos, ventas y PQR');
INSERT INTO roles (id, nombre, descripcion) VALUES (3, 'cliente', 'Compra obras y servicios y hace seguimiento a sus pedidos');

-- ── Permisos ───────────────────────────────────────────────────────────
INSERT INTO permisos (id, codigo, descripcion) VALUES (1, 'usuarios.ver', 'Consultar el listado de usuarios');
INSERT INTO permisos (id, codigo, descripcion) VALUES (2, 'usuarios.crear', 'Dar de alta usuarios');
INSERT INTO permisos (id, codigo, descripcion) VALUES (3, 'usuarios.editar', 'Modificar usuarios y su estado');
INSERT INTO permisos (id, codigo, descripcion) VALUES (4, 'usuarios.eliminar', 'Eliminar usuarios');
INSERT INTO permisos (id, codigo, descripcion) VALUES (5, 'catalogo.ver', 'Consultar obras y servicios');
INSERT INTO permisos (id, codigo, descripcion) VALUES (6, 'catalogo.crear', 'Crear obras y servicios');
INSERT INTO permisos (id, codigo, descripcion) VALUES (7, 'catalogo.editar', 'Modificar obras y servicios');
INSERT INTO permisos (id, codigo, descripcion) VALUES (8, 'catalogo.eliminar', 'Eliminar obras y servicios');
INSERT INTO permisos (id, codigo, descripcion) VALUES (9, 'pedidos.ver', 'Consultar pedidos');
INSERT INTO permisos (id, codigo, descripcion) VALUES (10, 'pedidos.crear', 'Crear pedidos');
INSERT INTO permisos (id, codigo, descripcion) VALUES (11, 'pedidos.gestionar', 'Cambiar el estado de los pedidos');
INSERT INTO permisos (id, codigo, descripcion) VALUES (12, 'ventas.ver', 'Consultar el historial de ventas');
INSERT INTO permisos (id, codigo, descripcion) VALUES (13, 'ventas.crear', 'Registrar ventas');
INSERT INTO permisos (id, codigo, descripcion) VALUES (14, 'ventas.gestionar', 'Cambiar el estado de las ventas');
INSERT INTO permisos (id, codigo, descripcion) VALUES (15, 'facturas.ver', 'Consultar y descargar facturas');
INSERT INTO permisos (id, codigo, descripcion) VALUES (16, 'facturas.emitir', 'Emitir facturas de venta');
INSERT INTO permisos (id, codigo, descripcion) VALUES (17, 'reportes.ver', 'Generar reportes en PDF y Excel');
INSERT INTO permisos (id, codigo, descripcion) VALUES (18, 'pqr.crear', 'Radicar PQR');
INSERT INTO permisos (id, codigo, descripcion) VALUES (19, 'pqr.ver', 'Consultar PQR');
INSERT INTO permisos (id, codigo, descripcion) VALUES (20, 'pqr.gestionar', 'Responder y cambiar el estado de las PQR');
INSERT INTO permisos (id, codigo, descripcion) VALUES (21, 'dashboard.ver', 'Acceder al dashboard');
INSERT INTO permisos (id, codigo, descripcion) VALUES (22, 'sistema.diagnostico', 'Ejecutar el diagnóstico del sistema');
INSERT INTO permisos (id, codigo, descripcion) VALUES (23, 'ia.usar', 'Usar las sugerencias de IA del catálogo');

-- ── Asignación de permisos a cada rol ──────────────────────────────────
-- El administrador tiene todos los permisos.
INSERT INTO rol_permisos (rol_id, permiso_id) VALUES (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17), (1, 18), (1, 19), (1, 20), (1, 21), (1, 22), (1, 23);
INSERT INTO rol_permisos (rol_id, permiso_id) VALUES (2, 5), (2, 6), (2, 7), (2, 9), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (2, 16), (2, 17), (2, 19), (2, 20), (2, 21), (2, 23);
INSERT INTO rol_permisos (rol_id, permiso_id) VALUES (3, 5), (3, 9), (3, 10), (3, 12), (3, 15), (3, 18), (3, 19), (3, 21);

-- ── Usuarios de prueba ─────────────────────────────────────────────────
-- Las contraseñas se almacenan EXCLUSIVAMENTE como hash bcrypt.
-- Credenciales en claro (solo para pruebas):
--   administrador   admin@oleoylienzo.com        Admin1234
--   empleado        empleado@oleoylienzo.com     Empleado123
--   cliente         cliente@oleoylienzo.com      Cliente123
--   cliente         carlos.mejia@ejemplo.com     Cliente123

INSERT INTO usuarios (id, nombre, apellido, tipo_documento, numero_documento, direccion, telefono, email, password_hash, activo, rol_id, creado_en, actualizado_en)
VALUES (1, 'Ana', 'Restrepo', 'CC', '1000000001', 'Calle 10 # 20-30', '3001234567', 'admin@oleoylienzo.com', '$2b$12$aR/8kne4wImiTsR5PQDaceCW2In/ecl5YvS6PnL6Dl4uOMP7i6WHu', TRUE, 1, NOW(), NOW());
INSERT INTO usuarios (id, nombre, apellido, tipo_documento, numero_documento, direccion, telefono, email, password_hash, activo, rol_id, creado_en, actualizado_en)
VALUES (2, 'Luis', 'Gómez', 'CC', '1000000002', 'Carrera 45 # 12-05', '3007654321', 'empleado@oleoylienzo.com', '$2b$12$sBDOYlt9hyiBYRrwzACnT.fLA7ilcKmZuEZyq0fbXbdWs4w96j0Au', TRUE, 2, NOW(), NOW());
INSERT INTO usuarios (id, nombre, apellido, tipo_documento, numero_documento, direccion, telefono, email, password_hash, activo, rol_id, creado_en, actualizado_en)
VALUES (3, 'Sara', 'Pérez', 'CC', '1000000003', 'Avenida Siempre Viva 742', '3009876543', 'cliente@oleoylienzo.com', '$2b$12$T8JfxDlLZ.WrbMfQqfsRIuin2yg0RcHx9wULDWZ0rMmBXr4L.ln5.', TRUE, 3, NOW(), NOW());
INSERT INTO usuarios (id, nombre, apellido, tipo_documento, numero_documento, direccion, telefono, email, password_hash, activo, rol_id, creado_en, actualizado_en)
VALUES (4, 'Carlos', 'Mejía', 'CC', '1000000004', 'Calle 80 # 15-22', '3005551122', 'carlos.mejia@ejemplo.com', '$2b$12$vl2A/4Mv7LjbVJSGwkPUbOGmp39EB.h4NJwxA4zsmlKuyNqcglBPi', TRUE, 3, NOW(), NOW());

-- ── Catálogo de obras ──────────────────────────────────────────────────
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (1, 'Amanecer en el Valle', 'Marina Solórzano', 2021, 'Óleo sobre lienzo', 1250000, 'Pinceladas cálidas que capturan la luz del primer sol sobre un valle en calma.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (2, 'Fragmentos Azules', 'Iván Restrepo', 2019, 'Acrílico sobre lienzo', 980000, 'Una composición geométrica que descompone el horizonte en planos de azul profundo.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (3, 'Tormenta Interior', 'Camila Duarte', 2022, 'Óleo sobre lienzo', 1480000, 'Trazos densos y oscuros que expresan la tensión emocional de una tormenta contenida.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (4, 'Jardín Silencioso', 'Marina Solórzano', 2020, 'Acrílico sobre lienzo', 890000, 'Formas orgánicas en tonos verdes que evocan la quietud de un jardín al amanecer.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (5, 'Geometría del Deseo', 'Tomás Aguilar', 2023, 'Óleo sobre lienzo', 1650000, 'Bloques rotundos en rojo y negro que juegan con el equilibrio y la tensión visual.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (6, 'Ecos de Otoño', 'Camila Duarte', 2018, 'Óleo sobre lienzo', 1020000, 'Capas cálidas de ocre y siena que rememoran la caída de las hojas en octubre.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (7, 'Mar Interior', 'Iván Restrepo', 2021, 'Acrílico sobre lienzo', 1150000, 'Curvas en azul turquesa que sugieren el movimiento constante de las mareas.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (8, 'Retrato en Ocre', 'Tomás Aguilar', 2022, 'Óleo sobre lienzo', 1780000, 'Un rostro sugerido entre bloques de tierra y sombra, entre lo figurativo y lo abstracto.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (9, 'Nocturno', 'Marina Solórzano', 2023, 'Óleo sobre lienzo', 1920000, 'Un cielo profundo salpicado de luz dorada, homenaje a las noches sin ciudad.', NULL, TRUE, 1, NOW(), NOW());
INSERT INTO obras (id, titulo, artista, anio, tecnica, precio, descripcion, imagen_url, disponible, stock, creado_en, actualizado_en)
VALUES (10, 'Primavera Fragmentada', 'Camila Duarte', 2020, 'Acrílico sobre lienzo', 970000, 'Pétalos de rosa y verde dispersos en una composición ligera y luminosa.', NULL, TRUE, 1, NOW(), NOW());

-- ── Servicios ──────────────────────────────────────────────────────────
INSERT INTO servicios (id, nombre, descripcion, precio, activo, creado_en, actualizado_en)
VALUES (1, 'Enmarcado personalizado', 'Enmarcado a medida para obras adquiridas en la galería.', 150000, TRUE, NOW(), NOW());
INSERT INTO servicios (id, nombre, descripcion, precio, activo, creado_en, actualizado_en)
VALUES (2, 'Restauración básica', 'Limpieza y restauración leve de obras sobre lienzo.', 300000, TRUE, NOW(), NOW());
INSERT INTO servicios (id, nombre, descripcion, precio, activo, creado_en, actualizado_en)
VALUES (3, 'Envío asegurado', 'Transporte de la obra con embalaje especializado y seguro incluido.', 90000, TRUE, NOW(), NOW());
INSERT INTO servicios (id, nombre, descripcion, precio, activo, creado_en, actualizado_en)
VALUES (4, 'Asesoría de curaduría', 'Acompañamiento para armar una colección coherente.', 250000, TRUE, NOW(), NOW());


-- ═══════════════════════════════════════════════════════════════════════
--  SECUENCIAS
--  Los INSERT anteriores fijan el id a mano, así que hay que adelantar las
--  secuencias para que el siguiente registro no choque con uno existente.
-- ═══════════════════════════════════════════════════════════════════════
SELECT setval(pg_get_serial_sequence('roles', 'id'), COALESCE((SELECT MAX(id) FROM roles), 1));
SELECT setval(pg_get_serial_sequence('permisos', 'id'), COALESCE((SELECT MAX(id) FROM permisos), 1));
SELECT setval(pg_get_serial_sequence('usuarios', 'id'), COALESCE((SELECT MAX(id) FROM usuarios), 1));
SELECT setval(pg_get_serial_sequence('obras', 'id'), COALESCE((SELECT MAX(id) FROM obras), 1));
SELECT setval(pg_get_serial_sequence('servicios', 'id'), COALESCE((SELECT MAX(id) FROM servicios), 1));

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
