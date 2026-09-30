# Guion de sustentación

Recorrido de 15–20 minutos para la exposición. Cada bloque indica **qué
mostrar**, **qué decir** y **qué criterio de evaluación cubre**, para que
ninguna pregunta del instructor quede sin respuesta demostrada.

> Los comandos sueltos para probar cosas concretas por consola están en
> [`evidencias.md`](evidencias.md). Este documento es el orden de la
> exposición.

---

## URLs para la sustentación

| | |
|---|---|
| **Aplicación** | https://oleo-lienzo.vercel.app |
| **API** | https://oleo-lienzo-api.onrender.com |
| **Swagger** | https://oleo-lienzo-api.onrender.com/docs |
| **Repositorio** | https://github.com/vegajerson88-droid/Oleo-Lienzo |

---

## Antes de empezar: 10 minutos de preparación

| # | Qué hacer | Por qué |
|---|---|---|
| 1 | Arrancar backend y frontend, o abrir la URL pública | Nada se improvisa en vivo |
| 2 | **Si está desplegado en Render:** abrir la URL 5 minutos antes | El plan gratuito duerme el servicio y la primera carga tarda ~40 s |
| 3 | Ejecutar `python seed.py` si la base está vacía | Sin datos, los dashboards salen en cero |
| 4 | Abrir en pestañas: el sitio, `/docs`, Postman y el repositorio | Cambiar de pestaña es más rápido que escribir URLs |
| 5 | Tener a mano las credenciales de los tres roles | Vas a entrar y salir varias veces |
| 6 | Iniciar sesión una vez y cerrar sesión | Deja la caché caliente: todo carga más rápido |

**Credenciales:**

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@oleoylienzo.com` | `Admin1234` |
| Empleado | `empleado@oleoylienzo.com` | `Empleado123` |
| Cliente | `cliente@oleoylienzo.com` | `Cliente123` |

---

## Bloque 1 · Presentación del proyecto (2 min)

**Muestra:** la página de inicio con el carrusel.

**Di:**

> Óleo & Lienzo es una galería de arte que vende pinturas originales y
> servicios asociados. El problema que resuelve es concreto: las galerías
> pequeñas llevan el catálogo en redes, las ventas en una hoja de cálculo y
> las facturas en documentos sueltos. Eso hace imposible saber qué obra sigue
> disponible o cuánto se vendió sin reconstruirlo a mano.
>
> La arquitectura son tres capas: React con Vite en el navegador, FastAPI
> como servidor y PostgreSQL como base de datos. La comunicación entre la
> primera y la segunda es HTTP con JSON; entre la segunda y la tercera, SQL.

**Cubre:** contexto del proyecto · arquitectura tecnológica.

---

## Bloque 2 · La zona pública (1 min)

**Muestra:** el catálogo. Aplica un filtro de precio y otro de técnica.

**Di:**

> El catálogo es público y no necesita cuenta. Admite seis filtros y
> paginación, y todo se resuelve en la base de datos: el frontend no filtra
> en memoria.

**Cubre:** REQ-22 (paginación y filtros) · consumo de la API desde React.

---

## Bloque 3 · Registro, login y JWT (3 min)

**Muestra, en este orden:**

1. El formulario de registro. **Escribe un correo mal formado** y un
   documento con letras: enseña que valida mientras escribes.
2. Regístrate con datos correctos.
3. **Intenta registrar el mismo correo otra vez.** Sale un 409.
4. Inicia sesión como administrador.
5. Señala el navbar: *«Hola, Ana»* y el botón de salir.

**Di:**

> La validación ocurre dos veces: en React mientras se escribe, y otra vez en
> el servidor. Esto último es lo importante: quien llame a la API
> directamente se salta el formulario entero, así que la validación que
> cuenta es la del backend.
>
> La contraseña nunca se guarda tal cual. Se guarda su hash bcrypt, de 60
> caracteres y con una sal distinta por usuario. Del hash no se puede volver
> a la contraseña.
>
> Al iniciar sesión, el servidor firma un JWT que lleva el correo, el rol y
> la fecha de caducidad. React lo envía en cada petición protegida.

**Si te preguntan por el hash**, muéstralo:

```bash
psql "$DATABASE_URL" -c "select email, left(password_hash,7), length(password_hash) from usuarios limit 3;"
```

**Cubre:** Matriz 4.1 · hashing seguro · validación en ambos lados · JWT.

---

## Bloque 4 · Roles y protección de endpoints (2 min)

Este bloque **es el que más peso tiene** y suele ser donde más preguntan.

**Muestra:**

1. Como administrador: el panel con sus diez secciones.
2. **Cierra sesión y entra como empleado.** Señala que ya no está la sección
   de Usuarios.
3. Abre otra pestaña y **prueba a llamar al endpoint directamente**:

```bash
# Sin token
curl -s http://localhost:8000/api/usuarios
# {"error":"Unauthorized","detail":"No autenticado."}

# Con token de cliente
curl -s http://localhost:8000/api/usuarios -H "Authorization: Bearer $TOKEN_CLIENTE"
# {"error":"Forbidden","detail":"Esta operación requiere uno de estos roles: administrador..."}
```

**Di:**

> Que el frontend oculte la opción es comodidad de interfaz, no seguridad.
> La autorización definitiva la decide siempre el backend. Sin token da 401;
> con token pero sin el rol adecuado, 403. Son dos cosas distintas: 401 es
> «no sé quién eres», 403 es «sé quién eres y no puedes».

**Cubre:** Matriz 4.2 · control de roles · protección de endpoints · REQ-24.

---

## Bloque 5 · El flujo comercial completo (4 min)

Es el corazón del proyecto. **Hazlo de una sola pasada, sin saltos.**

**Muestra:**

1. Entra como **cliente**. Arma un pedido con una obra y un servicio.
2. Entra como **empleado**. Confirma ese pedido.
3. Señala que **se generó la venta automáticamente** y que **el stock de la
   obra bajó**.
4. Emite la **factura** de esa venta.
5. **Descarga el PDF** y ábrelo en pantalla.

**Di:**

> Confirmar un pedido es la operación más delicada del sistema: crea la
> venta, copia sus líneas, calcula el IVA del 19 % y descuenta el inventario,
> todo dentro de una única transacción. Si cualquiera de esos pasos falla, se
> deshacen todos. Sin esa garantía podría quedar una venta sin líneas, o
> inventario descontado sin venta.
>
> La factura congela los datos: copia el nombre y la dirección del cliente y
> los importes del momento. Si mañana el cliente se muda o sube el precio de
> la obra, la factura ya emitida no cambia. Un documento fiscal refleja lo que
> ocurrió, no lo que es cierto hoy.

**Si preguntan por qué no se puede anular una venta pagada:**

> Porque no dejaría rastro contable. Una venta pagada se reembolsa, y el
> reembolso sí queda registrado. Las transiciones se validan contra una
> máquina de estados; intentar una no permitida devuelve 422.

**Cubre:** REQ-01, 02, 03, 07, 08, 09 · Matriz 3.2.

---

## Bloque 6 · Reportes en PDF y Excel (2 min)

**Muestra:**

1. La sección de Reportes. Genera el reporte del día.
2. **Descarga el PDF** y ábrelo.
3. **Descarga el Excel** y ábrelo. Enseña que tiene **fórmulas y autofiltro**,
   no solo texto pegado.

**Di:**

> El Excel no es una tabla plana: lleva fórmulas de total y autofiltro, para
> que quien lo reciba pueda seguir analizando los datos sin volver al
> sistema. Ambos se generan en el servidor, no en el navegador.

**Cubre:** REQ-04, 05, 06.

---

## Bloque 7 · Dashboards y analítica (3 min)

**Muestra:**

1. El dashboard del administrador: **12 indicadores y 4 gráficos**.
2. **Aplica el filtro de estado = Anulada.** Los números y los gráficos
   cambian a la vez.
3. Cambia a **filtro por obra**. Vuelve a cambiar todo.
4. **Cierra sesión y entra como empleado:** 6 indicadores, sin usuarios ni
   ingresos.
5. **Entra como cliente:** 5 indicadores, solo lo suyo.

**Di:**

> Ni un solo número de esta pantalla está escrito en el frontend. Todos salen
> de consultas con GROUP BY contra la base de datos. React solo los dibuja.
>
> Los filtros son seis: fecha inicial, fecha final, obra, servicio, estado y
> cliente, y afectan a la vez a las tarjetas y a los gráficos.

**Si preguntan un detalle técnico, este impresiona:**

> El filtro por obra se resuelve con una subconsulta, no con un JOIN. Si se
> hiciera con JOIN, una venta de dos líneas aparecería dos veces y los
> importes saldrían duplicados. Hay una prueba automatizada que lo comprueba.

**Cubre:** REQ-10, 11, 12, 13, 15.

---

## Bloque 8 · PQR y chatbot con IA (2 min)

**Muestra:**

1. Como cliente: radica una PQR. Señala el **número de radicado**.
2. Como empleado: respóndela. Enseña el cambio de estado.
3. Abre el **chatbot** desde el botón flotante.
4. Pregúntale: *«¿Qué obras tienen disponibles?»* — debe responder con obras
   **reales del catálogo**.

**Di:**

> El chatbot recibe el catálogo real como contexto, así que no inventa obras:
> responde con las que existen y sus precios.
>
> La clave de la API vive en una variable de entorno y nunca sale del
> servidor ni aparece en el código.

**Importante, si la IA no está configurada o falla:**

> El chatbot degrada a un modo local basado en reglas y **lo declara**: la
> respuesta trae `generado_por_ia: false`. Preferimos decir la verdad antes
> que hacer pasar una respuesta de respaldo por una respuesta de la IA.

**Cubre:** REQ-16, 17, 18, 19 · Matriz 7.1, 7.2.

---

## Bloque 9 · Documentación y pruebas (2 min)

**Muestra:**

1. `/docs`: el Swagger con las **60 operaciones** agrupadas en 14 secciones.
2. Pulsa **Authorize**, entra, y **ejecuta una operación desde ahí mismo**.
3. La colección de **Postman**.
4. En una terminal, ejecuta las pruebas:

```bash
cd backend && pytest -q
# 164 passed
```

**Di:**

> La documentación se genera sola a partir del código, con sus etiquetas,
> descripciones y ejemplos. No hay que mantenerla aparte.
>
> Hay 164 pruebas automatizadas, y pasan tanto sobre SQLite como sobre
> PostgreSQL. No prueban funciones sueltas: recorren el mismo camino que el
> navegador, desde la petición hasta la base de datos.

**Cubre:** Matriz 8.1, 9.1 · REQ-25.

---

## Bloque 10 · Cierre: decisiones técnicas (2 min)

Aquí es donde se separa «hice un proyecto» de «entiendo lo que hice».
Menciona **dos o tres**, las que mejor recuerdes:

| Decisión | Por qué |
|---|---|
| **El dinero se calcula con `Decimal`, no con `float`** | Empezamos con `float` y las facturas se descuadraban por céntimos. Con coma flotante, `0.1 + 0.2` no da `0.3` |
| **La capa `crud` no lanza excepciones HTTP** | Lanza errores de dominio, y unos manejadores los traducen. Así la lógica de negocio no depende del protocolo y se reutiliza desde el seed y desde las tareas de fondo |
| **Todos los errores tienen el mismo formato** | `{"error": ..., "detail": ...}`. Permite al frontend tratarlos con un solo bloque de código |
| **La clave secreta no tiene valor por defecto** | En desarrollo se genera efímera; en producción, si falta, la aplicación se niega a arrancar. Un valor por defecto acaba llegando a producción |
| **Los estados se guardan como texto con CHECK, no como ENUM** | Así el mismo esquema funciona en PostgreSQL y en SQLite, que es lo que permite correr las pruebas en los dos motores |

**Cierre sugerido:**

> El resultado que mejor resume el trabajo es que 164 pruebas pasan sobre dos
> motores de base de datos distintos. Cada cosa que he dicho hoy puede
> comprobarse ejecutando el código.

---

## Comparativa FastAPI vs Django REST Framework

La Matriz de Validación (criterio 11.1) pide esta comparativa. Está completa
en [`comparativa-fastapi-drf.md`](comparativa-fastapi-drf.md). Resumen para
responder de viva voz:

| Aspecto | FastAPI | Django REST Framework |
|---|---|---|
| **Validación** | Pydantic, a partir de anotaciones de tipo | Serializers escritos a mano |
| **Documentación** | OpenAPI automática | Requiere `drf-spectacular` |
| **Asincronía** | Nativa desde el diseño | Añadida después, con limitaciones en el ORM |
| **Rendimiento** | Mayor en operaciones de entrada/salida | Menor, por el ciclo síncrono |
| **Lo que trae puesto** | Poco: hay que elegir ORM, migraciones y admin | Mucho: ORM, admin, migraciones y autenticación |
| **Cuándo conviene** | APIs, microservicios, cargas asíncronas | Aplicaciones completas donde el panel de administración ahorra semanas |

> Para este proyecto elegimos FastAPI porque el entregable es una API que
> consume un frontend aparte: el panel de administración de Django no habría
> aportado nada, y la documentación automática y la validación con Pydantic
> sí.

---

## Preguntas que probablemente te hagan

| Pregunta | Respuesta corta |
|---|---|
| ¿Dónde se guarda la contraseña? | Solo el hash bcrypt, con sal por usuario. Nunca en claro |
| ¿Qué pasa si alguien llama a la API sin token? | 401. Con token pero sin permiso, 403 |
| ¿Cómo sabes que el token no fue manipulado? | Va firmado con una clave del servidor; si cambia un byte, la firma no valida. Hay una prueba que lo comprueba |
| ¿El frontend puede saltarse la seguridad? | No. Oculta opciones por comodidad, pero la decisión la toma el backend |
| ¿Por qué PostgreSQL y no MySQL? | Integridad referencial, restricciones CHECK y mejores agregaciones para los dashboards |
| ¿Dónde está la clave de la IA? | En una variable de entorno. No está en el código ni en GitHub |
| ¿Qué pasa si la IA se cae? | El chatbot degrada al modo local y lo declara: `generado_por_ia: false` |
| ¿Cuántos endpoints tiene? | 60 operaciones en 14 recursos |
| ¿Las pruebas prueban de verdad? | 164, contra la API completa, en SQLite y en PostgreSQL |
| ¿Se puede desplegar? | Sí: `render.yaml`, `vercel.json`, `Dockerfile` y la guía en `despliegue.md` |

---

## Si algo falla en vivo

| Problema | Qué hacer |
|---|---|
| La URL pública tarda en cargar | *«Es el plan gratuito, duerme el servicio tras 15 minutos»*. Sigue hablando mientras carga |
| El chatbot responde en modo local | Dilo abiertamente: está diseñado para degradar. Es una decisión, no un fallo |
| Un panel sale vacío | Ejecuta `python seed.py` y recarga |
| Se cae internet | Levanta todo en local: backend en `:8000`, frontend en `:5173`. Funciona igual salvo la IA externa |
| Un PDF no abre | Descárgalo de nuevo; hay cuatro facturas de ejemplo para elegir |

**Ten siempre un plan B en local.** Aunque el despliegue funcione, arranca el
proyecto en tu máquina antes de salir de casa.
