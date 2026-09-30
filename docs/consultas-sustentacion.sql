-- ═══════════════════════════════════════════════════════════════════════
--  Consultas para mostrar la base de datos durante la sustentación
--
--  Pégalas de una en una en el SQL Editor de Neon (o en DBeaver/psql).
--  Cada bloque demuestra un requisito concreto del proyecto.
-- ═══════════════════════════════════════════════════════════════════════


-- ── 1. Las 15 tablas del modelo ────────────────────────────────────────
-- Demuestra: modelo relacional completo (REQ-21 del quinto avance)

SELECT t.table_name AS tabla,
       (SELECT count(*)
          FROM information_schema.columns c
         WHERE c.table_name = t.table_name
           AND c.table_schema = 'public') AS columnas
  FROM information_schema.tables t
 WHERE t.table_schema = 'public'
   AND t.table_type = 'BASE TABLE'
 ORDER BY t.table_name;


-- ── 2. Cuántos registros hay en cada tabla ─────────────────────────────
-- Demuestra: la base tiene datos reales, no está vacía

SELECT 'usuarios' AS tabla, count(*) FROM usuarios
UNION ALL SELECT 'roles',            count(*) FROM roles
UNION ALL SELECT 'permisos',         count(*) FROM permisos
UNION ALL SELECT 'obras',            count(*) FROM obras
UNION ALL SELECT 'servicios',        count(*) FROM servicios
UNION ALL SELECT 'pedidos',          count(*) FROM pedidos
UNION ALL SELECT 'ventas',           count(*) FROM ventas
UNION ALL SELECT 'detalle_ventas',   count(*) FROM detalle_ventas
UNION ALL SELECT 'facturas',         count(*) FROM facturas
UNION ALL SELECT 'pqr',              count(*) FROM pqr
UNION ALL SELECT 'conversaciones',   count(*) FROM conversaciones
UNION ALL SELECT 'mensajes',         count(*) FROM mensajes
 ORDER BY 1;


-- ── 3. Las contraseñas están hasheadas ─────────────────────────────────
-- Demuestra: hashing seguro con bcrypt. Ninguna contraseña en texto plano.
-- El prefijo $2b$12$ identifica bcrypt con coste 12; 60 caracteres es su
-- longitud fija. Del hash NO se puede volver a la contraseña.

SELECT email,
       left(password_hash, 7)  AS algoritmo,
       length(password_hash)   AS longitud,
       right(password_hash, 12) AS ultimos_caracteres
  FROM usuarios
 ORDER BY id;


-- ── 4. Integridad referencial: las 20 claves foráneas ──────────────────
-- Demuestra: las relaciones las impone la base de datos, no solo el código

SELECT tc.table_name      AS tabla,
       kcu.column_name    AS columna,
       ccu.table_name     AS apunta_a,
       rc.delete_rule     AS al_borrar
  FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu
    ON kcu.constraint_name = tc.constraint_name
  JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
  JOIN information_schema.referential_constraints rc
    ON rc.constraint_name = tc.constraint_name
 WHERE tc.constraint_type = 'FOREIGN KEY'
   AND tc.table_schema = 'public'
 ORDER BY tc.table_name, kcu.column_name;


-- ── 5. El encadenamiento completo: venta → detalle → factura ───────────
-- Demuestra: el flujo comercial con su desglose de IVA y la factura emitida

SELECT v.numero                         AS venta,
       u.nombre || ' ' || u.apellido    AS cliente,
       d.descripcion,
       d.cantidad,
       d.subtotal,
       v.impuestos                      AS iva_19,
       v.total,
       v.estado,
       f.numero                         AS factura
  FROM ventas v
  JOIN usuarios u        ON u.id = v.cliente_id
  JOIN detalle_ventas d  ON d.venta_id = v.id
  LEFT JOIN facturas f   ON f.venta_id = v.id
 ORDER BY v.id, d.id;


-- ── 6. Roles y sus permisos ────────────────────────────────────────────
-- Demuestra: control de acceso granular, no solo tres roles fijos

SELECT r.nombre AS rol, count(rp.permiso_id) AS permisos
  FROM roles r
  LEFT JOIN rol_permisos rp ON rp.rol_id = r.id
 GROUP BY r.nombre
 ORDER BY permisos DESC;

-- Y el detalle de uno concreto:
SELECT r.nombre AS rol, p.codigo AS permiso, p.descripcion
  FROM roles r
  JOIN rol_permisos rp ON rp.rol_id = r.id
  JOIN permisos p      ON p.id = rp.permiso_id
 WHERE r.nombre = 'empleado'
 ORDER BY p.codigo;


-- ── 7. La factura congela los datos del cliente ────────────────────────
-- Demuestra: un documento fiscal refleja lo que ocurrió, no lo que es
-- cierto hoy. Si el cliente cambia de dirección, la factura no se altera.

SELECT f.numero,
       f.fecha_emision::date AS fecha,
       f.cliente_nombre      AS nombre_en_la_factura,
       u.nombre || ' ' || u.apellido AS nombre_actual,
       f.cliente_direccion   AS direccion_en_la_factura,
       u.direccion           AS direccion_actual,
       f.total,
       f.estado
  FROM facturas f
  JOIN usuarios u ON u.id = f.cliente_id
 ORDER BY f.id;


-- ── 8. Restricciones CHECK que protegen los datos ──────────────────────
-- Demuestra: reglas de negocio impuestas por el motor. Ni un error de
-- programación puede dejar una cantidad negativa o una línea sin producto.

SELECT rel.relname AS tabla, con.conname AS restriccion,
       pg_get_constraintdef(con.oid) AS regla
  FROM pg_constraint con
  JOIN pg_class rel      ON rel.oid = con.conrelid
  JOIN pg_namespace nsp  ON nsp.oid = rel.relnamespace
 WHERE con.contype = 'c'
   AND nsp.nspname = 'public'
 ORDER BY rel.relname
 LIMIT 15;


-- ── 9. Los dashboards salen de aquí, no del frontend ───────────────────
-- Demuestra: esta es LA MISMA consulta que alimenta el gráfico de ventas
-- por día. El frontend solo la dibuja.

SELECT date(creado_en)              AS dia,
       count(*)                     AS ventas,
       sum(total)                   AS total_vendido
  FROM ventas
 WHERE estado IN ('pagada', 'pendiente_pago')
 GROUP BY date(creado_en)
 ORDER BY dia;


-- ── 10. El dinero se guarda como NUMERIC, no como float ────────────────
-- Demuestra: por qué las facturas cuadran al céntimo

SELECT column_name AS columna, data_type AS tipo,
       numeric_precision AS digitos, numeric_scale AS decimales
  FROM information_schema.columns
 WHERE table_name = 'facturas'
   AND data_type = 'numeric'
 ORDER BY ordinal_position;
