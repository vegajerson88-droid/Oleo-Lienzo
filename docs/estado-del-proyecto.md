# Estado del proyecto

Documento de traspaso. Resume qué es el proyecto, qué se ha hecho, cómo está
ahora y qué conviene saber antes de tocarlo.

**Última actualización:** 30 de septiembre de 2026

---

## 1. Qué es

**Óleo & Lienzo** — galería de arte que vende pinturas originales y servicios
asociados. Proyecto integrador del SENA, ficha 3406211, ADSO.

Arquitectura: **React + Vite → FastAPI → PostgreSQL**

| Capa | Tecnología | Carpeta |
|---|---|---|
| Frontend | React 18 · Vite 5 · Tailwind 4 | `frontend/` |
| Backend | FastAPI 0.141 · SQLAlchemy 2.1 async · Python 3.12 | `backend/` |
| Base de datos | PostgreSQL (18 en producción, 16+ en local) | `backend/sql/` |

---

## 2. En producción

| | |
|---|---|
| **Aplicación** | https://oleo-lienzo.vercel.app |
| **API** | https://oleo-lienzo-api.onrender.com |
| **Swagger** | https://oleo-lienzo-api.onrender.com/docs |
| **Repositorio** | https://github.com/vegajerson88-droid/Oleo-Lienzo |

- Frontend en **Vercel** (Root Directory: `frontend`)
- Backend en **Render** (Blueprint desde `render.yaml`, Docker, región Ohio)
- Base de datos en **Neon** (proyecto `cold-bar-26064861`, región Ohio)

> El plan gratuito de Render duerme el servicio tras 15 min sin tráfico. La
> primera petición después tarda ~50 s. Despertarlo antes de cualquier demo.

### Credenciales de prueba (las crea `seed.py`)

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@oleoylienzo.com` | `Admin1234` |
| Empleado | `empleado@oleoylienzo.com` | `Empleado123` |
| Cliente | `cliente@oleoylienzo.com` | `Cliente123` |
| Cliente | `carlos.mejia@ejemplo.com` | `Cliente123` |

### Secretos

Ninguno está en el repositorio. Viven en:

- **Local:** `backend/.env` y `frontend/.env` (ambos en `.gitignore`)
- **Producción:** variables de entorno de Render y de Vercel

**Pendiente de rotar:** la clave de Groq y la contraseña de Neon quedaron
expuestas en una conversación. Rotarlas en `console.groq.com/keys` y en el
diálogo *Connect → Reset password* de Neon.

---

## 3. Cómo levantarlo en local

```bash
# Backend  (terminal 1)
cd backend && ./venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && npm run dev
```

Comprobar si ya corre antes de arrancar: `curl -s localhost:8000/api/sistema/salud`

Si el puerto está ocupado:
`kill $(ss -ltnp | grep ':8000' | grep -oP 'pid=\K[0-9]+' | head -1)`

> Si el dev server de Vite lleva muchas horas encendido, su conexión HMR se
> cae y recarga la página a destiempo: parece que el backend no responde
> cuando sí lo hace. Se arregla reiniciándolo.

### Pruebas

```bash
cd backend && ./venv/bin/python -m pytest -q     # 164 pruebas
```

**Nunca** apuntar `TEST_DATABASE_URL` a la base de desarrollo: la suite borra
y recrea las tablas en cada prueba.

---

## 4. Qué se hizo en la última sesión

Nueve commits, de `24820df` a `06f06cd`.

### 4.1 Los 8 criterios de la lista de valoración final

| # | Criterio | Qué se hizo |
|---|---|---|
| 3 | Tabla de diseño recurso–verbo–ruta–código | `docs/diseno-api.md`, generado desde OpenAPI |
| 10 | Versiones fijadas | `requirements.txt` con `==` en todo |
| 31 | Formato uniforme de error | Handler de `HTTPException`; antes un 404 daba `{"detail"}` y un 422 `{"error","detail"}` |
| 35 | Dependencia que resuelve el recurso | `app/dependencies/recursos.py` |
| 37 | `dependencies=[...]` a nivel de router | En `usuarios`, `reportes` e `ia` |
| 39 | Clave secreta sin valor por defecto | Efímera en desarrollo; en producción no arranca sin ella |
| 45 | Middleware de logging | `app/core/middlewares.py`, con `X-Request-ID` |
| 57 | `run_in_threadpool` | La inferencia ya no bloquea el bucle de eventos |
| 65 | Dobles de prueba | `tests/test_dobles_externos.py`, 17 pruebas |

Además: 61 (tareas con sesión propia), 63 (overrides limpiados), y el CORS
rechaza el comodín de forma explícita.

### 4.2 Requisito 13 del quinto avance

El dashboard solo filtraba por fechas. Se añadieron **obra, servicio, estado y
cliente**, en backend (`crud/estadisticas.py` con `FiltrosDashboard`) y en la
interfaz (`DashboardPanel.jsx`).

> El filtro por obra usa **subconsulta, no JOIN**: unir el detalle duplicaría
> los importes de una venta con varias líneas. Hay una prueba que lo blinda.

También se cerró un agujero: un cliente podía pedir `?cliente_id=otro`. Ahora
el backend fuerza el suyo.

### 4.3 Entregables nuevos

- **Manual Técnico** en PDF, 45 páginas, 12 secciones obligatorias
  → `docs/manual/ManualTecnico_Ficha3406211_VegaNaranjo_JersonJesus.pdf`
- **Guion de sustentación** → `docs/sustentacion.md`
- **Consultas SQL para demostrar la base** → `docs/consultas-sustentacion.sql`
- **CI en GitHub Actions** → `.github/workflows/ci.yml`
- **Configuración de despliegue** → `render.yaml`, `frontend/vercel.json`
- **Guía de despliegue** reescrita para Neon + Render + Vercel

### 4.4 Fallos encontrados y corregidos

| Fallo | Detalle |
|---|---|
| `generar_sql.py` no corría | Dos rutas absolutas de otra máquina |
| El modelo de Groq no existía | `llama-3.3-70b` retirado → `openai/gpt-oss-120b` |
| La IA devolvía texto vacío como éxito | Es un modelo de razonamiento y agotaba los tokens pensando |
| 4 pruebas dependían del `.env` local | Pasaban sin clave de Groq, fallaban con ella |
| El Dockerfile usaba Python 3.11 | `requirements.txt` se fijó contra 3.12; numpy 2.5.3 no existe para 3.11 |
| `JWT_SECRET_KEY` era el marcador de la plantilla | Se generó una aleatoria real |
| El seed no creaba facturas ni pedidos | Los paneles salían vacíos |

---

## 5. Estado actual

| | |
|---|---|
| Pruebas | **164**, verdes en SQLite y PostgreSQL |
| CI | verde en `main` (estilo, pruebas en ambos motores, build, sin secretos) |
| Lint | `ruff check` y `ruff format --check` limpios |
| Cumplimiento | **185 de 186** requisitos |

El único punto abierto es el **criterio 1** de la valoración final («las rutas
no contienen verbos»): `/api/auth/login` y `/api/auth/registro` sí los llevan.
Es una excepción consciente, argumentada en `docs/diseno-api.md`.

Detalle completo en `docs/matriz-cumplimiento.md`.

---

## 6. Cómo está organizado el backend

```
backend/app/
  main.py ............. solo configuración, middlewares e include_router
  core/ ............... ajustes, seguridad, excepciones, middlewares
  models/ ............. 15 tablas SQLAlchemy
  schemas/ ............ validación Pydantic (entrada y salida separadas)
  crud/ ............... acceso a datos y reglas de negocio
  routers/ ............ 14 routers, 60 operaciones
  dependencies/ ....... auth, paginación, resolución de recursos
  services/ ........... PDF, Excel, correo, chatbot, IA, tareas de fondo
```

### Convenciones que conviene respetar

1. **La capa `crud` no lanza `HTTPException`.** Lanza errores de dominio
   (`app/core/exceptions.py`) y unos handlers en `main.py` los traducen.
2. **Todo error sale igual:** `{"error": "...", "detail": ...}`.
3. **El dinero es `Decimal`, nunca `float`.** Ver `app/core/dinero.py`.
4. **Los estados se validan contra una máquina de transiciones**, no se
   cambian libremente.
5. **El cliente no envía campos del servidor:** ni id, ni consecutivos, ni
   fechas, ni estado. Los esquemas de entrada no los aceptan.
6. **Comentarios y nombres en castellano**, como el resto del código.

### Artefactos que se generan, no se editan a mano

| Archivo | Script |
|---|---|
| `backend/sql/schema_postgresql.sql` | `scripts/generar_sql.py` |
| `postman/Oleo-Lienzo.postman_collection.json` | `scripts/generar_postman.py` |
| `docs/diseno-api.md` | `scripts/generar_diseno_api.py` |
| `docs/manual/capturas/*.png` | `scripts/capturar_evidencias.py` |
| `docs/manual/ManualTecnico_*.pdf` | `scripts/generar_manual_tecnico.py` |

Si cambias los modelos, **regenera el SQL** o CI fallará.
Si cambias endpoints, **regenera Postman y el diseño de la API**.

---

## 7. Si vas a cambiar la interfaz

El frontend está en `frontend/src/`:

```
components/ui/ ....... 13 componentes reutilizables (Button, Input, Modal...)
components/graficos/ . StatCard, GraficoBarras, GraficoLinea
components/ .......... Header, Footer, Carousel, ChatbotWidget, WhatsAppButton
pages/ ............... Index, Catalogo, Login, QuienesSomos, Contacto
pages/panel/ ......... las secciones de los tres paneles
services/api.js ...... cliente HTTP centralizado (única puerta al backend)
context/ ............. AuthContext, ToastContext
hooks/useRecurso.js .. carga de datos con estados de carga y error
utils/validators.js .. validación de formularios
```

- Los estilos son **Tailwind 4**, sin hojas CSS aparte salvo `index.css`.
- La URL del backend **nunca se escribe a mano**: sale de `VITE_API_URL`.
- Al añadir una llamada a la API, hazlo en `services/api.js`, no suelta en el
  componente.

Después de cualquier cambio:

```bash
cd frontend && npm run build     # tiene que compilar limpio
```

Y si tocas el backend:

```bash
cd backend && ./venv/bin/python -m ruff check . --exclude venv && ./venv/bin/python -m pytest -q
```

---

## 8. Despliegue de un cambio

1. `git push origin main`
2. **Render** reconstruye el backend solo (5-8 min)
3. **Vercel** reconstruye el frontend solo (1-2 min)
4. **CI** ejecuta las pruebas en paralelo

Si cambias una variable de entorno, hazlo en el panel correspondiente
(Render o Vercel) — el `.env` local no viaja.

> Las variables `VITE_*` se incrustan **en tiempo de construcción**. Cambiar
> una en Vercel exige redesplegar para que surta efecto.

---

## 9. Documentación del proyecto

| Archivo | Contenido |
|---|---|
| `README.md` | Instalación, ejecución, variables, estructura |
| `docs/estado-del-proyecto.md` | Este documento |
| `docs/sustentacion.md` | Guion de la exposición, bloque a bloque |
| `docs/matriz-cumplimiento.md` | Los 186 requisitos, uno por uno |
| `docs/diseno-api.md` | Tabla recurso–verbo–ruta–código |
| `docs/despliegue.md` | Guía Neon + Render + Vercel |
| `docs/evidencias.md` | Comandos para demostrar cada requisito |
| `docs/comparativa-fastapi-drf.md` | FastAPI frente a Django REST Framework |
| `docs/consultas-sustentacion.sql` | 10 consultas para mostrar la base |
| `docs/manual/` | Manual Técnico en PDF y sus capturas |
