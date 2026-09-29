# Diseño de la API — recurso, verbo, ruta y código

Tabla de diseño de la API REST de Óleo & Lienzo: para cada recurso, qué verbo
HTTP le corresponde a cada operación, en qué ruta vive y con qué código
responde.

## Criterios de diseño aplicados

1. **Las rutas nombran recursos, no acciones.** `/api/productos`, no
   `/api/obtenerProductos`. El verbo HTTP dice qué se hace; la ruta, sobre qué.
2. **Los recursos van en plural.** `/api/ventas/{id}`, no `/api/venta/{id}`.
3. **Cada verbo tiene un significado fijo.** `GET` consulta, `POST` crea,
   `PUT` reemplaza por completo, `PATCH` modifica parcialmente y `DELETE`
   elimina.
4. **Las operaciones de negocio que no son un CRUD se modelan como
   sub-recurso**, no como un `PATCH` genérico: `POST /api/pqr/{id}/responder`
   expresa la intención mucho mejor que mandar un campo suelto.
5. **El cliente no decide los campos del servidor.** Ni el identificador, ni
   los consecutivos (`V-2026-000001`, `OL-000001`, `PQR-000001`), ni las
   fechas, ni el estado: los esquemas de entrada ni siquiera los aceptan.
6. **Los códigos son los del protocolo.** `201` al crear devolviendo el
   recurso, `204` al eliminar sin cuerpo, `409` para un conflicto de negocio
   (nunca `400` ni `500`), `422` para validación.

## Excepción consciente: las rutas de autenticación

`/api/auth/login`, `/api/auth/registro` y las de contraseña llevan un verbo en
la ruta. Es la convención establecida para autenticación —la usan OAuth2 y
prácticamente todas las APIs— y se ha preferido a forzar un sustantivo
artificial como `/api/sesiones`, que sería más purista pero menos reconocible.

## Formato uniforme de error

Todos los errores, los lance quien los lance, salen con el mismo cuerpo:

```json
{ "error": "NotFound", "detail": "Obra 42 no encontrada." }
```

En un `422` de validación, `detail` es la lista de campos que fallaron.

---


## Autenticación

**Quién puede:** Pública (salvo `/me` y cambio de contraseña)

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `POST` | `/api/auth/cambiar-password` | Cambiar la contraseña con la sesión iniciada | `200` · `401` · `403` · `422` |
| `POST` | `/api/auth/login` | Iniciar sesión y obtener el JWT | `200` · `401` · `403` · `422` · `429` |
| `GET` | `/api/auth/me` | Datos del usuario autenticado | `200` · `401` · `403` |
| `POST` | `/api/auth/recuperar-password` | Solicitar el enlace de recuperación de contraseña | `200` · `422` · `429` |
| `POST` | `/api/auth/registro` | Registrar un cliente nuevo | `201` · `409` · `422` |
| `POST` | `/api/auth/restablecer-password` | Fijar una contraseña nueva con el token del correo | `200` · `400` · `422` |
| `POST` | `/api/auth/token` | Inicio de sesión compatible con OAuth2 (botón Authorize de Swagger) | `200` · `401` · `403` · `422` |

## Usuarios

**Quién puede:** Administrador

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/usuarios` | Listar usuarios | `200` · `401` · `403` · `422` |
| `POST` | `/api/usuarios` | Crear un usuario desde el panel | `201` · `401` · `403` · `409` · `422` |
| `GET` | `/api/usuarios/roles` | Listar roles y sus permisos | `200` · `401` · `403` |
| `DELETE` | `/api/usuarios/{usuario_id}` | Eliminar un usuario | `204` · `401` · `403` · `404` · `409` · `422` |
| `GET` | `/api/usuarios/{usuario_id}` | Consultar un usuario | `200` · `401` · `403` · `404` · `422` |
| `PATCH` | `/api/usuarios/{usuario_id}` | Actualizar un usuario (parcialmente) | `200` · `401` · `403` · `404` · `422` |
| `PUT` | `/api/usuarios/{usuario_id}` | Reemplazar un usuario (actualización completa) | `200` · `401` · `403` · `404` · `422` |
| `PATCH` | `/api/usuarios/{usuario_id}/estado` | Activar o desactivar un usuario | `200` · `401` · `403` · `404` · `422` |

## Obras / Productos

**Quién puede:** Lectura pública · escritura administrador o empleado

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/productos` | Listar obras del catálogo | `200` · `422` |
| `POST` | `/api/productos` | Crear una obra | `201` · `401` · `403` · `422` |
| `DELETE` | `/api/productos/{obra_id}` | Eliminar una obra | `204` · `401` · `403` · `404` · `409` · `422` |
| `GET` | `/api/productos/{obra_id}` | Consultar una obra | `200` · `404` · `422` |
| `PATCH` | `/api/productos/{obra_id}` | Actualizar una obra (parcialmente) | `200` · `401` · `403` · `404` · `422` |
| `PUT` | `/api/productos/{obra_id}` | Reemplazar una obra (actualización completa) | `200` · `401` · `403` · `404` · `422` |

## Servicios

**Quién puede:** Lectura pública · escritura administrador o empleado

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/servicios` | Listar servicios | `200` · `422` |
| `POST` | `/api/servicios` | Crear un servicio | `201` · `401` · `403` · `409` · `422` |
| `DELETE` | `/api/servicios/{servicio_id}` | Eliminar un servicio | `204` · `401` · `403` · `404` · `409` · `422` |
| `GET` | `/api/servicios/{servicio_id}` | Consultar un servicio | `200` · `404` · `422` |
| `PATCH` | `/api/servicios/{servicio_id}` | Actualizar un servicio (parcialmente) | `200` · `401` · `403` · `404` · `409` · `422` |
| `PUT` | `/api/servicios/{servicio_id}` | Reemplazar un servicio (actualización completa) | `200` · `401` · `403` · `404` · `409` · `422` |

## Pedidos

**Quién puede:** Cliente (los suyos) · administrador y empleado (todos)

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/pedidos` | Listar pedidos | `200` · `401` · `403` · `422` |
| `POST` | `/api/pedidos` | Crear un pedido | `201` · `401` · `403` · `404` · `422` |
| `GET` | `/api/pedidos/{pedido_id}` | Consultar un pedido | `200` · `401` · `403` · `404` · `422` |
| `PATCH` | `/api/pedidos/{pedido_id}/estado` | Cambiar el estado de un pedido | `200` · `401` · `403` · `404` · `422` |

## Ventas

**Quién puede:** Administrador y empleado · el cliente ve las suyas

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/ventas` | Historial de ventas con filtros | `200` · `401` · `403` · `422` |
| `POST` | `/api/ventas` | Registrar una venta | `201` · `401` · `403` · `404` · `422` |
| `GET` | `/api/ventas/{venta_id}` | Consultar una venta | `200` · `401` · `403` · `404` · `422` |
| `PATCH` | `/api/ventas/{venta_id}/estado` | Cambiar el estado de una venta | `200` · `401` · `403` · `404` · `422` |

## Facturación

**Quién puede:** Administrador y empleado · el cliente ve las suyas

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/facturas` | Consultar facturas | `200` · `401` · `403` · `422` |
| `POST` | `/api/facturas` | Emitir una factura a partir de una venta | `201` · `401` · `403` · `404` · `409` · `422` |
| `GET` | `/api/facturas/{factura_id}` | Consultar una factura | `200` · `401` · `403` · `404` · `422` |
| `PATCH` | `/api/facturas/{factura_id}/estado` | Cambiar el estado de una factura | `200` · `401` · `403` · `404` · `422` |
| `GET` | `/api/facturas/{factura_id}/pdf` | Descargar la factura en PDF | `200` · `401` · `403` · `404` · `422` |

## Reportes

**Quién puede:** Administrador y empleado

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/reportes/ventas-diarias` | Reporte diario de ventas (JSON) | `200` · `401` · `403` · `422` |
| `GET` | `/api/reportes/ventas-diarias/excel` | Reporte diario de ventas en Excel (.xlsx) | `200` · `401` · `403` · `422` |
| `GET` | `/api/reportes/ventas-diarias/pdf` | Reporte diario de ventas en PDF | `200` · `401` · `403` · `422` |

## Dashboard

**Quién puede:** Autenticado, con el contenido recortado según el rol

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/dashboard` | Dashboard del usuario autenticado | `200` · `401` · `403` · `422` |

## PQR

**Quién puede:** Cliente radica · administrador y empleado gestionan

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/pqr` | Listar PQR | `200` · `401` · `403` · `422` |
| `POST` | `/api/pqr` | Radicar una PQR | `201` · `422` |
| `GET` | `/api/pqr/{pqr_id}` | Consultar una PQR | `200` · `401` · `403` · `404` · `422` |
| `PATCH` | `/api/pqr/{pqr_id}/estado` | Cambiar el estado de una PQR | `200` · `401` · `403` · `404` · `422` |
| `POST` | `/api/pqr/{pqr_id}/responder` | Responder una PQR | `200` · `401` · `403` · `404` · `422` |

## Chatbot IA

**Quién puede:** Pública

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/chatbot/conversaciones` | Listar conversaciones (auditoría) | `200` · `401` · `403` · `422` |
| `POST` | `/api/chatbot/mensaje` | Conversar con el asistente | `200` · `422` |
| `GET` | `/api/chatbot/conversaciones/{conversacion_id}` | Consultar una conversación completa | `200` · `401` · `403` · `404` · `422` |

## Inteligencia Artificial

**Quién puede:** Administrador y empleado

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/api/ia/descripcion-sugerida` | Redactar una descripción con IA externa | `200` · `401` · `403` · `422` |
| `GET` | `/api/ia/precio-sugerido` | Sugerir un precio con el modelo propio | `200` · `401` · `403` · `404` · `422` |

## Pagos (Stripe)

**Quién puede:** Cliente · el webhook lo llama Stripe con firma

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `POST` | `/api/pagos/checkout` | Crear la sesión de pago de una venta | `200` · `401` · `403` · `404` · `422` |
| `GET` | `/api/pagos/configuracion` | Clave pública de Stripe | `200` |
| `POST` | `/api/pagos/webhook` | Webhook de Stripe | `200` · `400` · `422` |

## Sistema

**Quién puede:** `/salud` pública · `/diagnostico` administrador

| Verbo | Ruta | Operación | Códigos |
|---|---|---|---|
| `GET` | `/` | Información de la API | `200` |
| `GET` | `/api/sistema/diagnostico` | Diagnóstico completo de dependencias | `200` · `401` · `403` |
| `GET` | `/api/sistema/salud` | Comprobación rápida de vida | `200` |

**Total: 60 operaciones** repartidas en 14 recursos.

---

## Códigos de respuesta y cuándo se usan

| Código | Cuándo |
|---|---|
| `200 OK` | Consulta o modificación correcta |
| `201 Created` | Recurso creado; el cuerpo lleva el recurso con su id |
| `204 No Content` | Eliminación correcta, sin cuerpo |
| `401 Unauthorized` | Falta el token o no es válido. Incluye `WWW-Authenticate: Bearer` |
| `403 Forbidden` | Autenticado, pero su rol no alcanza |
| `404 Not Found` | El recurso no existe |
| `409 Conflict` | Duplicado o restricción única: correo ya registrado, venta ya facturada |
| `422 Unprocessable Content` | Validación fallida o regla de negocio incumplida |
| `429 Too Many Requests` | Se superó el límite de intentos |
| `500 Internal Server Error` | Error inesperado. La traza va al log, nunca al cliente |

---

*Generado desde el esquema OpenAPI con `scripts/generar_diseno_api.py`.
No editar a mano: la tabla y la API implementada se mantienen así en sintonía.*
