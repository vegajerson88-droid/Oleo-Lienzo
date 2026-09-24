# Guía de evidencias

Cómo demostrar, paso a paso, cada requisito de los entregables. Todo lo que
aparece aquí corresponde a funcionalidad realmente implementada y probada.

**Antes de empezar**, deja corriendo las dos terminales:

```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
npm run dev
```

---

## 1. Base de datos PostgreSQL

**Que las tablas existen y están relacionadas:**

```bash
psql -U oleo -d oleo_lienzo -c "\dt"
```

**Las claves, restricciones e índices:**

```sql
SELECT contype, count(*) FROM pg_constraint c
  JOIN pg_class t ON t.oid = c.conrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
 WHERE n.nspname = 'public'
 GROUP BY contype;
```

Debe devolver 15 claves primarias, 20 foráneas, 21 `CHECK` y 4 `UNIQUE`.

**Una relación concreta:**

```bash
psql -U oleo -d oleo_lienzo -c "\d detalle_ventas"
```

Se ve la restricción que obliga a que cada línea apunte a una obra **o** a un
servicio, nunca a los dos.

**El script SQL funciona desde cero:**

```bash
createdb -U postgres prueba_oleo
psql -U oleo -d prueba_oleo -f backend/sql/schema_postgresql.sql
psql -U oleo -d prueba_oleo -c "\dt"
```

---

## 2. Contraseñas con hash

```sql
SELECT email, rol_id, left(password_hash, 32) AS hash, length(password_hash)
  FROM usuarios;
```

Se ve el prefijo `$2b$12$` de bcrypt y una longitud de 60 caracteres. Ninguna
contraseña aparece en claro.

> Captura recomendada: esta consulta junto a la pantalla de registro, para
> mostrar que lo que el usuario escribió no es lo que se guardó.

---

## 3. Autenticación y JWT

**Desde Swagger** — http://localhost:8000/docs

1. `POST /api/auth/registro` → **201**, con el rol `cliente` asignado.
2. `POST /api/auth/login` → **200**, con `access_token`.
3. Pega el token en https://jwt.io: se ven `sub`, `rol`, `iat` y `exp`.
4. **Authorize** (arriba a la derecha) → `username` es el correo.
5. `GET /api/auth/me` → **200**, con el usuario y sus permisos.

**Desde la aplicación** — http://localhost:5173/login

Inicia sesión y comprueba que el Navbar muestra **«Hola, Ana»** y el botón
**Salir**.

---

## 4. Control de roles (401 y 403)

| Prueba | Resultado esperado |
|---|---|
| `GET /api/usuarios` sin token | **401** |
| `GET /api/usuarios` con token de **cliente** | **403** |
| `GET /api/usuarios` con token de **empleado** | **403** |
| `GET /api/usuarios` con token de **administrador** | **200** |
| `DELETE /api/productos/1` con token de **empleado** | **403** |
| `DELETE /api/productos/1` con token de **administrador** | **204** |

Todo de una vez, desde la terminal:

```bash
B=http://localhost:8000/api
TC=$(curl -s -X POST $B/auth/login -H 'Content-Type: application/json' \
     -d '{"email":"cliente@oleoylienzo.com","password":"Cliente123"}' \
     | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

echo "Sin token:  $(curl -s -o /dev/null -w '%{http_code}' $B/usuarios)"
echo "Cliente:    $(curl -s -o /dev/null -w '%{http_code}' $B/usuarios -H "Authorization: Bearer $TC")"
```

**En la interfaz:** con la sesión de cliente iniciada, escribe a mano
`http://localhost:5173/panel/administrador`. La aplicación te devuelve a tu
panel, y aunque forzaras la vista, la API rechazaría los datos.

---

## 5. Métodos HTTP y CRUD completo

| Método | Endpoint | Qué demuestra |
|---|---|---|
| `GET` | `/api/productos` | Listar con filtros y paginación |
| `GET` | `/api/productos/{id}` | Consultar uno |
| `POST` | `/api/productos` | Crear |
| `PUT` | `/api/productos/{id}` | **Reemplazo completo** |
| `PATCH` | `/api/productos/{id}` | **Actualización parcial** |
| `DELETE` | `/api/productos/{id}` | Eliminar |
| `PATCH` | `/api/usuarios/{id}/estado` | Cambiar estado activo/inactivo |

**La diferencia entre PUT y PATCH** —que es lo que suele faltar— se ve así:

```bash
# PUT con un solo campo -> 422, porque PUT exige el recurso entero
curl -s -o /dev/null -w "PUT parcial: %{http_code}\n" -X PUT $B/productos/1 \
  -H "Authorization: Bearer $TA" -H 'Content-Type: application/json' \
  -d '{"titulo":"Solo el titulo"}'

# PATCH con un solo campo -> 200, y el resto no se toca
curl -s -o /dev/null -w "PATCH parcial: %{http_code}\n" -X PATCH $B/productos/1 \
  -H "Authorization: Bearer $TA" -H 'Content-Type: application/json' \
  -d '{"precio":999000}'
```

**En la interfaz:** panel de administrador → **Obras** → crear, editar y
eliminar.

---

## 6. Validaciones en tiempo real

**Frontend** — http://localhost:5173/login → **Crear una cuenta**

Escribe a propósito datos inválidos y observa cómo aparecen los mensajes
mientras escribes:

| Campo | Escribe | Mensaje |
|---|---|---|
| Nombre | `Juan123` | Solo se permiten letras y espacios |
| Teléfono | `12` | Debe tener entre 7 y 10 dígitos |
| Documento | letras | El campo no las acepta |
| Correo | `correo-malo` | El formato del correo no es válido |
| Contraseña | `abc` | Mínimo 8 caracteres, con mayúscula, minúscula y número |
| Confirmar | algo distinto | Las contraseñas no coinciden |

**Backend** — la misma validación, saltándose el formulario:

```bash
curl -s -X POST $B/auth/registro -H 'Content-Type: application/json' \
  -d '{"nombre":"A1","apellido":"B","tipo_documento":"XX","numero_documento":"abc",
       "direccion":"x","telefono":"1","email":"mal","password":"123",
       "confirmar_password":"456"}' | python3 -m json.tool
```

Devuelve **422** con la lista de errores. Esta es la evidencia clave: el
backend valida aunque el frontend no lo haga.

---

## 7. Lógica de negocio: el encadenamiento

**El flujo completo, en la interfaz:**

1. Entra como **cliente** → **Catálogo** → pulsa **Pedir** en una obra.
2. Ve a **Mi cuenta** → el pedido aparece en estado *pendiente*.
3. Sal y entra como **administrador** → **Pedidos** → **Confirmar**.
4. El aviso dice que **se generó la venta automáticamente**.
5. **Ventas** → la nueva venta tiene `pedido_id` y su IVA calculado.
6. **Ver** → **Emitir factura** → aparece el consecutivo `OL-NNNNNN`.
7. **Facturas** → **PDF** → se descarga la factura.

**Las transiciones inválidas se rechazan:**

```bash
# pendiente -> entregado no es una transición válida
curl -s -X PATCH $B/pedidos/1/estado -H "Authorization: Bearer $TA" \
  -H 'Content-Type: application/json' -d '{"nuevo_estado":"entregado"}'
```

Devuelve **422** explicando qué transiciones sí serían válidas.

**El inventario se controla:**

```bash
# Antes del pedido
curl -s $B/productos/1 | python3 -c "import sys,json;print('stock:',json.load(sys.stdin)['stock'])"
# ... haz un pedido desde la interfaz ...
# Después: el stock bajó. Cancela el pedido: el stock vuelve.
```

---

## 8. Cálculo del IVA

En el detalle de cualquier venta se ve el desglose. Para comprobarlo:

```bash
curl -s "$B/ventas?page_size=1" -H "Authorization: Bearer $TA" | python3 -c "
import sys, json
v = json.load(sys.stdin)['items'][0]
base = v['subtotal'] - v['descuento']
print(f'Subtotal:  {v[\"subtotal\"]:>12,.2f}')
print(f'Descuento: {v[\"descuento\"]:>12,.2f}')
print(f'Base:      {base:>12,.2f}')
print(f'IVA 19%:   {v[\"impuestos\"]:>12,.2f}  (esperado {base*0.19:,.2f})')
print(f'Total:     {v[\"total\"]:>12,.2f}')
"
```

El IVA se aplica sobre la base ya descontada, como exige la normativa
colombiana.

---

## 9. Facturación y PDF

1. Panel de administrador → **Ventas** → **Ver** → **Emitir factura**.
2. **Facturas** → **PDF**.

El PDF incluye logotipo, razón social, NIT, datos del cliente, número y
fecha, líneas con cantidades y precios, subtotal, descuento, IVA desglosado,
total, método de pago, estado y pie de página.

**Que una venta no se factura dos veces:**

```bash
curl -s -o /dev/null -w "Segunda factura: %{http_code}\n" -X POST $B/facturas \
  -H "Authorization: Bearer $TA" -H 'Content-Type: application/json' \
  -d '{"venta_id":1}'
```

Devuelve **409**.

---

## 10. Reportes en PDF y Excel

Panel → **Reportes** → elige la fecha → **PDF** o **Excel**.

- **PDF**: horizontal, con cuatro tarjetas de resumen, la tabla del día con el
  estado en color y el total general.
- **Excel**: una columna por dato, importes como números reales, fila de
  totales con fórmulas `SUM`, autofiltro, paneles congelados y una segunda
  hoja de resumen por estado.

Ábrelo en Excel o LibreOffice y comprueba que las fórmulas están vivas: al
filtrar, los totales responden.

---

## 11. Dashboards por rol

Entra con cada cuenta y compara:

| Rol | Indicadores | Gráficos |
|---|---|---|
| Administrador | 12, con usuarios, ingresos y facturación | 4: ventas por día, por estado, más vendidos y PQR |
| Empleado | 6, solo operativos | 2 |
| Cliente | 5, solo su propia actividad | 1 |

**Que los datos no están escritos en el frontend:** registra una venta nueva y
vuelve al dashboard. El contador sube. También puedes abrir la pestaña **Red**
del navegador y ver la llamada a `/api/dashboard`.

En el gráfico lineal, pasa el ratón: aparece la línea guía con la fecha y el
valor exactos. Debajo hay un desplegable **«Ver los datos como tabla»**.

---

## 12. Módulo de PQR

1. **Sin iniciar sesión**, ve a **Contacto** y radica una solicitud: pide
   nombre y correo, y devuelve un número `PQR-NNNNNN`.
2. **Con sesión de cliente**, radica otra: toma tus datos automáticamente.
3. Como **administrador** → **PQR** → **Responder**.
4. Vuelve como cliente → **Mis PQR** → la respuesta aparece.

**Las reglas se cumplen:**

```bash
# Marcar como respondida algo que aún no tiene respuesta -> 422
curl -s -o /dev/null -w "%{http_code}\n" -X PATCH $B/pqr/1/estado \
  -H "Authorization: Bearer $TA" -H 'Content-Type: application/json' \
  -d '{"nuevo_estado":"respondida"}'
```

---

## 13. Chatbot con IA

Pulsa el botón del asistente, abajo a la derecha.

**Sin `GROQ_API_KEY`:** responde con reglas sobre el catálogo real y lo marca
como **«Respuesta local»**. Es intencionado: no finge que contestó la IA.

**Con `GROQ_API_KEY`:** la etiqueta cambia a **«Generado con IA»** e indica el
modelo. Pregúntale por una obra concreta: responde con el precio real de la
base de datos.

**Que la clave no llega al navegador:** abre la pestaña **Red**, mira la
petición a `/api/chatbot/mensaje` y comprueba que ni la petición ni la
respuesta contienen la clave.

**Auditoría:** las conversaciones quedan guardadas.

```bash
curl -s "$B/chatbot/conversaciones" -H "Authorization: Bearer $TA" | python3 -m json.tool
```

---

## 14. Pasarela de pago

Con `STRIPE_SECRET_KEY` configurada:

1. Entra como cliente → **Mi cuenta** → una venta en *pendiente de pago*.
2. **Pagar** → te lleva al checkout alojado por Stripe.
3. Tarjeta `4242 4242 4242 4242`, fecha futura, cualquier CVC.
4. Vuelves a la aplicación con el aviso de pago confirmado.

**Que no guardamos datos de tarjeta:**

```sql
SELECT * FROM pagos;
```

Solo hay `referencia_externa`, `payment_intent`, estado y monto. Ninguna
columna para el número de tarjeta, el CVV o la fecha de expiración.

**Que el webhook verifica la firma:**

```bash
curl -s -o /dev/null -w "Firma falsa: %{http_code}\n" -X POST $B/pagos/webhook \
  -H 'Stripe-Signature: firma-inventada' -H 'Content-Type: application/json' \
  -d '{"type":"checkout.session.completed"}'
```

Devuelve **400**.

---

## 15. Correos

Con el SMTP configurado, cada uno de estos eventos envía un correo HTML:

| Evento | Asunto |
|---|---|
| Registro | Bienvenido a Óleo & Lienzo |
| ¿Olvidaste tu contraseña? | Recuperación de contraseña |
| Venta pagada | Compra confirmada V-AAAA-NNNNNN |
| Cambio de estado del pedido | Pedido #N: confirmado |
| PQR radicada | PQR-NNNNNN radicada |
| PQR respondida | Respuesta a tu PQR |

Todos llevan logotipo, razón social, NIT, dirección, teléfono y correo de
contacto. Los de compra incluyen la tabla de líneas con subtotal, IVA y total.

**Que no bloquean la respuesta:** se envían con `BackgroundTasks`. El registro
responde de inmediato aunque el servidor de correo tarde.

**Sin SMTP configurado** no falla nada: se registra en el log y la operación
continúa.

---

## 16. Diagnóstico del sistema

Panel de administrador → **Diagnóstico** → **Ejecutar diagnóstico**.

Cada componente se comprueba de verdad:

| Componente | Qué hace |
|---|---|
| Base de datos | Ejecuta `SELECT 1` y reporta el motor y su versión |
| IA local | Comprueba si el modelo está cargado en memoria |
| IA externa | Llama de verdad a la API de Groq |
| Pasarela de pago | Consulta el balance de Stripe |
| Correo | Abre la conexión SMTP y autentica |

Cada uno informa de su estado, su latencia en milisegundos y un detalle. No es
un endpoint que devuelva `"ok"` sin mirar nada.

---

## 17. Documentación automática

http://localhost:8000/docs

- 14 secciones con su descripción.
- 60 operaciones, cada una con `summary`, descripción larga, códigos de
  respuesta y ejemplos de cuerpo.
- Botón **Authorize** funcional.
- Alternativa en http://localhost:8000/redoc

---

## 18. Pruebas automatizadas

```bash
cd backend && pytest -v
```

**141 pruebas.** Para demostrar que no dependen de SQLite:

```bash
createdb -U postgres oleo_test
TEST_DATABASE_URL="postgresql+psycopg://oleo:tu_contrasena@localhost:5432/oleo_test" pytest
```

Las mismas 141 pasan contra PostgreSQL.

---

## 19. Diseño responsivo

Abre las herramientas de desarrollo (F12) → modo dispositivo.

| Ancho | Qué comprobar |
|---|---|
| 375 px | Menú hamburguesa, tarjetas en una columna, tablas convertidas en fichas |
| 768 px | Dos columnas, menú aún plegado |
| 1440 px | Menú completo, tres columnas, tablas normales |

Las tablas de los paneles no se desplazan horizontalmente en móvil: cada fila
se convierte en una tarjeta con las cabeceras delante de cada dato.

---

## 20. Seguridad

| Qué | Cómo se comprueba |
|---|---|
| Contraseñas con hash | `SELECT password_hash FROM usuarios` |
| Sin secretos en el código | `git ls-files \| grep "\.env$"` no devuelve nada |
| `.env` ignorado | `cat .gitignore \| grep env` |
| Token caducado rechazado | Espera a que expire o pon `JWT_EXPIRE_MINUTES=1` |
| Fuerza bruta limitada | Lanza 25 inicios de sesión fallidos seguidos → **429** |
| Cabeceras de seguridad | `curl -I http://localhost:8000/api/productos` |
| El correo no se filtra | Login con un correo inexistente y con uno real pero mala contraseña dan el mismo mensaje |

---

## Resumen para las capturas

| # | Captura | Dónde |
|---|---|---|
| 1 | Tablas en PostgreSQL | `psql -c "\dt"` |
| 2 | Hashes de contraseña | `SELECT email, password_hash FROM usuarios` |
| 3 | Swagger completo | `/docs` |
| 4 | Login y token en jwt.io | Swagger + jwt.io |
| 5 | 401 y 403 por rol | Postman |
| 6 | CRUD desde la interfaz | Panel → Obras |
| 7 | PUT 422 frente a PATCH 200 | Postman |
| 8 | Validaciones en vivo | Modal de registro |
| 9 | Pedido → venta → factura | Los tres paneles |
| 10 | Factura en PDF | Archivo descargado |
| 11 | Reporte en PDF | Archivo descargado |
| 12 | Reporte en Excel | Archivo abierto en Excel |
| 13 | Dashboard de administrador | Panel → Dashboard |
| 14 | Dashboards de empleado y cliente | Sus paneles |
| 15 | PQR radicada y respondida | Contacto + panel |
| 16 | Chatbot respondiendo | Widget flotante |
| 17 | Pago con Stripe | Checkout y retorno |
| 18 | Correo recibido | Bandeja de entrada |
| 19 | Diagnóstico | Panel → Diagnóstico |
| 20 | `pytest` en verde | Terminal |
| 21 | Vista móvil | F12, modo dispositivo |
| 22 | URL pública | Navegador |
