# Óleo & Lienzo

Aplicación web *full stack* de una galería de arte que vende pinturas
originales y servicios asociados (enmarcado, restauración, envío y curaduría).

**React + Vite → FastAPI → PostgreSQL**

Proyecto integrador · Ficha 3406211 · Tecnólogo en Análisis y Desarrollo de
Software · SENA.

---

## Contenido

- [Qué hace la aplicación](#qué-hace-la-aplicación)
- [Arquitectura](#arquitectura)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Ejecución](#ejecución)
- [Credenciales de prueba](#credenciales-de-prueba)
- [Variables de entorno](#variables-de-entorno)
- [Base de datos](#base-de-datos)
- [Documentación de la API](#documentación-de-la-api)
- [Pruebas](#pruebas)
- [Integraciones opcionales](#integraciones-opcionales)
- [Despliegue](#despliegue)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Documentos adicionales](#documentos-adicionales)

---

## Qué hace la aplicación

| Módulo | Qué resuelve |
|---|---|
| **Catálogo** | Obras y servicios con filtros, búsqueda y paginación. Lectura pública. |
| **Autenticación** | Registro, inicio de sesión con JWT, recuperación de contraseña por correo. |
| **Roles y permisos** | Administrador, empleado y cliente, con 23 permisos granulares. |
| **Pedidos** | El cliente arma su pedido; el estado sigue una máquina de estados. |
| **Ventas** | Confirmar un pedido genera su venta. También se registran ventas presenciales. |
| **Facturación** | Factura con consecutivo, importes congelados y descarga en PDF. |
| **Reportes** | Reporte diario de ventas en JSON, PDF y Excel. |
| **Dashboards** | Indicadores y gráficos calculados en la base de datos, distintos por rol. |
| **PQR** | Peticiones, quejas y reclamos con número de radicado y respuesta por correo. |
| **Chatbot** | Asistente con IA (Groq) que conoce el catálogo real. |
| **Pagos** | Stripe Checkout con webhook firmado. |
| **Diagnóstico** | Comprobación real de base de datos, IA, pagos y correo. |

### Cómo encajan las piezas

```
Cliente hace un pedido          → estado: pendiente
        ↓  (el administrador lo confirma)
Se genera la venta              → estado: pendiente_pago     · se calcula el IVA
        ↓  (pago con tarjeta o registro manual)
Venta pagada                    → estado: pagada             · correo de confirmación
        ↓
Se emite la factura             → consecutivo OL-NNNNNN      · descargable en PDF
```

El inventario se reserva al crear el pedido y se devuelve si se cancela la
compra o se anula la venta.

---

## Arquitectura

```
┌────────────────────┐      HTTP/JSON      ┌────────────────────┐      SQL      ┌──────────────┐
│  React 18 + Vite   │ ─────────────────▶  │  FastAPI (Python)  │ ───────────▶  │  PostgreSQL  │
│  Tailwind CSS v4   │  Authorization:     │  SQLAlchemy 2 async│   psycopg 3   │      16      │
│  React Router      │  Bearer <JWT>       │  Pydantic v2       │               │              │
└────────────────────┘                     └────────────────────┘               └──────────────┘
                                                     │
                                    ┌────────────────┼────────────────┐
                                    ▼                ▼                ▼
                                  Groq            Stripe            SMTP
                                (chatbot)        (pagos)          (correos)
```

El backend está organizado por capas:

```
routers/      →  HTTP: rutas, códigos de estado y documentación
schemas/      →  Pydantic: validación de entrada y forma de la salida
crud/         →  Acceso a datos y reglas de negocio
models/       →  SQLAlchemy: las tablas
services/     →  Integraciones externas (correo, PDF, Excel, IA, pagos)
dependencies/ →  Autenticación, autorización y paginación
core/         →  Configuración, seguridad, dinero y excepciones
```

---

## Requisitos previos

| Herramienta | Versión mínima | Comprobar con |
|---|---|---|
| Node.js | 18 | `node --version` |
| Python | 3.11 | `python3 --version` |
| PostgreSQL | 14 | `psql --version` |

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/vegajerson88-droid/Oleo-Lienzo.git
cd Oleo-Lienzo
```

### 2. Crear la base de datos

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE oleo WITH LOGIN PASSWORD 'tu_contrasena_segura';
CREATE DATABASE oleo_lienzo WITH OWNER = oleo ENCODING = 'UTF8';
\q
```

### 3. Backend

```bash
cd backend

python3 -m venv venv
source venv/bin/activate          # En Windows:  venv\Scripts\activate

pip install -r requirements.txt
```

El repositorio ya incluye `backend/.env` para desarrollo local. Si se crea una
copia nueva, usa `copy .env.example .env` en PowerShell o `cp .env.example .env`
en Git Bash.

Abre `backend/.env` y ajusta como mínimo estas dos líneas:

```env
DATABASE_URL=postgresql+psycopg://oleo:tu_contrasena_segura@localhost:5432/oleo_lienzo
JWT_SECRET_KEY=<pega aquí una clave larga y aleatoria>
```

El nombre de la base de datos es el último segmento de `DATABASE_URL`:
`oleo_lienzo`. Si tu PostgreSQL local ya tiene otro usuario o contraseña,
actualiza esa URL para que coincida. En una instalación nueva puedes crearla así:

```sql
CREATE ROLE oleo WITH LOGIN PASSWORD 'oleo';
CREATE DATABASE oleo_lienzo OWNER oleo ENCODING 'UTF8';
```

Si el rol ya existe, usa `ALTER ROLE oleo WITH PASSWORD 'oleo';` en lugar de
`CREATE ROLE`.

Para generar la clave:

```bash
openssl rand -hex 32
```

Crea las tablas y los datos de prueba:

```bash
python seed.py
```

> Alternativa: crear el esquema con SQL en lugar del seed.
> ```bash
> psql -U oleo -d oleo_lienzo -f sql/schema_postgresql.sql
> ```
> Ese script deja la base con las 15 tablas, los 23 permisos, los 3 roles,
> los 4 usuarios de prueba y el catálogo. El `seed.py` añade además ventas y
> PQR de ejemplo y entrena el modelo de sugerencia de precios.

### 4. Frontend

Desde la carpeta del frontend:

```bash
cd ../frontend
npm install
cp .env.example .env
```

El archivo `frontend/.env` ya apunta a `http://localhost:8000`, que es donde
arranca el backend.

---

## Ejecución

Hacen falta **dos terminales**.

**Terminal 1 — backend:**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

→ API en http://localhost:8000 · documentación en http://localhost:8000/docs

**Terminal 2 — frontend:**

```bash
cd frontend
npm run dev
```

→ Aplicación en http://localhost:5173

---

## Credenciales de prueba

Las crea `python seed.py`:

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@oleoylienzo.com` | `Admin1234` |
| Empleado | `empleado@oleoylienzo.com` | `Empleado123` |
| Cliente | `cliente@oleoylienzo.com` | `Cliente123` |
| Cliente | `carlos.mejia@ejemplo.com` | `Cliente123` |

Las contraseñas se guardan **solo** como hash bcrypt. Se puede comprobar:

```sql
SELECT email, left(password_hash, 30) FROM usuarios;
```

---

## Variables de entorno

Ningún secreto vive en el código. Todo se lee de `.env`, que está en
`.gitignore` y nunca se sube al repositorio.

### Backend — `backend/.env`

Ver `backend/.env.example` para la lista completa y comentada.

| Variable | Obligatoria | Para qué |
|---|:---:|---|
| `DATABASE_URL` | ✔ | Conexión a PostgreSQL |
| `JWT_SECRET_KEY` | ✔ | Firma de los tokens |
| `CORS_ORIGINS` | ✔ | Orígenes que pueden llamar a la API |
| `FRONTEND_URL` | ✔ | Enlaces de los correos y retorno de Stripe |
| `GROQ_API_KEY` | — | Chatbot con IA |
| `STRIPE_SECRET_KEY` | — | Pasarela de pago |
| `STRIPE_WEBHOOK_SECRET` | — | Verificación de la firma del webhook |
| `EMAIL_HOST`, `EMAIL_USER`, `EMAIL_PASSWORD` | — | Envío de correos |
| `IVA_PORCENTAJE` | — | IVA aplicado (19 por defecto) |

Las que no son obligatorias se pueden dejar vacías: la aplicación arranca
igual y avisa de que esa integración está desactivada.

### Frontend — `frontend/.env`

| Variable | Para qué |
|---|---|
| `VITE_API_URL` | URL del backend, sin `/api` al final |
| `VITE_WHATSAPP_NUMERO` | Número del botón flotante |

> Vite expone al navegador todo lo que empiece por `VITE_`. Por eso aquí
> nunca debe ponerse una clave secreta.

---

## Base de datos

Para desarrollo local, `DATABASE_URL` debe usar `localhost`. Con Docker Compose,
el archivo `backend/.env` se carga automáticamente y Compose sustituye solo el
host por `db`, porque ese es el nombre del servicio dentro de la red Docker.
Puedes levantar esa alternativa con `docker compose up --build` si Docker
Desktop está instalado.

15 tablas relacionadas:

```
roles ──┬── rol_permisos ── permisos
        │
        └── usuarios ──┬── pedidos ── detalles_pedido ──┬── obras
                       │      │                          └── servicios
                       │      └──────── ventas ── detalle_ventas
                       │                  │  │
                       │                  │  ├── facturas
                       │                  │  └── pagos
                       ├── pqr
                       └── conversaciones ── mensajes
```

El script `backend/sql/schema_postgresql.sql` crea todo: tablas, claves
primarias y foráneas, restricciones `CHECK` y `UNIQUE`, columnas `NOT NULL`,
índices y datos iniciales.

Se genera desde los propios modelos SQLAlchemy, de modo que el esquema SQL y
el ORM no pueden desincronizarse:

```bash
cd backend && python scripts/generar_sql.py
```

---

## Documentación de la API

Con el backend en marcha:

| Recurso | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Esquema OpenAPI | http://localhost:8000/openapi.json |

**60 operaciones** agrupadas en 14 secciones, cada una con su descripción,
sus códigos de respuesta y ejemplos de cuerpo.

### Autenticarse desde Swagger

1. Pulsa **Authorize** (arriba a la derecha).
2. `username`: el **correo**. `password`: la contraseña.
3. Las rutas protegidas ya enviarán la cabecera `Authorization`.

### Postman

La colección está en `postman/Oleo-Lienzo.postman_collection.json`.
Impórtala, ejecuta **POST /api/auth/login** y el token queda guardado
automáticamente para el resto de peticiones.

Se regenera desde el esquema OpenAPI con:

```bash
cd backend && python scripts/generar_postman.py
```

### Códigos de respuesta

| Código | Cuándo |
|---|---|
| `200` / `201` / `204` | Operación correcta |
| `401` | Falta el token, es inválido o ha caducado |
| `403` | Autenticado pero sin permisos para esa operación |
| `404` | El recurso no existe |
| `409` | Conflicto: duplicado o restricción única |
| `422` | Validación o regla de negocio incumplida |
| `429` | Demasiadas peticiones |

Todos los errores comparten el mismo formato:

```json
{ "error": "NotFoundError", "detail": "Obra 42 no encontrada." }
```

---

## Pruebas

```bash
cd backend
source venv/bin/activate
pytest -v
```

**141 pruebas** que cubren autenticación, roles, CRUD, reglas de negocio,
transiciones de estado, facturación, reportes, PQR, chatbot, pagos y
seguridad.

Por defecto corren sobre SQLite en memoria, que es rápido y no necesita
instalar nada. Para ejecutarlas contra el **PostgreSQL real**:

```bash
createdb -U postgres oleo_test
TEST_DATABASE_URL="postgresql+psycopg://oleo:tu_contrasena@localhost:5432/oleo_test" pytest
```

---

## Integraciones opcionales

Todas degradan con elegancia: si no están configuradas, la aplicación
funciona y lo indica en el diagnóstico.

### Chatbot con IA (Groq)

1. Crea una clave gratuita en https://console.groq.com/keys
2. Ponla en `backend/.env`:
   ```env
   GROQ_API_KEY=gsk_...
   ```

Sin clave, el chatbot responde con reglas locales sobre el catálogo real y
lo declara en la interfaz (`Respuesta local`), en lugar de fingir que
contestó la IA.

### Pagos (Stripe)

1. Claves de prueba en https://dashboard.stripe.com/test/apikeys
2. En `backend/.env`:
   ```env
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```
3. Para recibir los webhooks en local:
   ```bash
   stripe listen --forward-to localhost:8000/api/pagos/webhook
   ```
   Copia el `whsec_...` que imprime a `STRIPE_WEBHOOK_SECRET`.

Tarjeta de prueba: `4242 4242 4242 4242`, cualquier fecha futura y
cualquier CVC.

> Los datos de la tarjeta se introducen en una página alojada por Stripe.
> Nuestro servidor solo guarda identificadores de la transacción: ningún
> número de tarjeta, CVV ni fecha de expiración toca la base de datos.

### Correo (SMTP)

Con Gmail hace falta una **contraseña de aplicación**, no la del correo:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu.correo@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
```

Se envían correos HTML en el registro, la recuperación de contraseña, la
confirmación de compra, el cambio de estado del pedido y la gestión de PQR.

---

## Despliegue

Ver la guía completa en [`docs/despliegue.md`](docs/despliegue.md).

Resumen para Railway:

1. Crea un proyecto y añade el servicio **PostgreSQL**.
2. Despliega el backend desde `backend/` (el `Dockerfile` ya está listo) y
   copia las variables de `.env.example`.
3. Despliega el frontend como sitio estático con `npm run build`, poniendo
   `VITE_API_URL` con la URL pública del backend.
4. Añade la URL del frontend a `CORS_ORIGINS` del backend.

---

## Estructura del proyecto

```
Oleo-Lienzo/
├── backend/
│   ├── app/
│   │   ├── core/          · configuración, seguridad, dinero, excepciones
│   │   ├── models/        · 15 modelos SQLAlchemy
│   │   ├── schemas/       · esquemas Pydantic de entrada y salida
│   │   ├── crud/          · acceso a datos y reglas de negocio
│   │   ├── routers/       · 14 routers, 60 operaciones
│   │   ├── services/      · correo, PDF, Excel, chatbot, pagos, IA
│   │   ├── dependencies/  · autenticación, autorización, paginación
│   │   ├── database.py
│   │   └── main.py
│   ├── sql/               · script de creación de PostgreSQL
│   ├── scripts/           · generadores del SQL y de la colección Postman
│   ├── tests/             · 141 pruebas con pytest
│   ├── seed.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/        · sistema de diseño reutilizable
│   │   │   └── graficos/  · gráficos e indicadores
│   │   ├── pages/
│   │   │   └── panel/     · módulos de los paneles
│   │   ├── context/       · autenticación y avisos
│   │   ├── hooks/         · carga de datos con estados de carga y error
│   │   ├── services/api.js · cliente HTTP centralizado
│   │   └── utils/validators.js
│   ├── package.json
│   └── .env.example
├── postman/
├── docs/
└── README.md
```

---

## Documentos adicionales

| Documento | Contenido |
|---|---|
| [`docs/comparativa-fastapi-drf.md`](docs/comparativa-fastapi-drf.md) | FastAPI frente a Django REST Framework, aplicado a este proyecto |
| [`docs/evidencias.md`](docs/evidencias.md) | Cómo demostrar cada requisito, paso a paso |
| [`docs/despliegue.md`](docs/despliegue.md) | Puesta en producción |
| [`docs/matriz-cumplimiento.md`](docs/matriz-cumplimiento.md) | Requisito por requisito, con su estado |
