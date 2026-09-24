# Despliegue

Guía para poner **Óleo & Lienzo** en producción. Los ejemplos usan
[Railway](https://railway.app), que es la plataforma recomendada en el quinto
avance, pero el procedimiento es el mismo en Render, Fly.io o cualquier
servicio que acepte contenedores.

El proyecto son **tres piezas** que se despliegan por separado:

```
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│   Frontend   │ ─────▶ │   Backend    │ ─────▶ │  PostgreSQL  │
│ sitio estático│        │  contenedor  │        │   gestionado │
└──────────────┘        └──────────────┘        └──────────────┘
```

---

## 1. Base de datos

En Railway: **New → Database → PostgreSQL**.

La plataforma genera una variable `DATABASE_URL` con este formato:

```
postgresql://usuario:contraseña@host:puerto/base
```

El backend usa **psycopg 3 en modo asíncrono**, así que hay que cambiar el
prefijo:

```
postgresql+psycopg://usuario:contraseña@host:puerto/base
```

> Es el error más habitual al desplegar este proyecto. Sin `+psycopg`,
> SQLAlchemy intenta cargar un driver síncrono y el arranque falla.

---

## 2. Backend

**New → GitHub Repo →** este repositorio. Railway detecta `railway.json` y
construye con `backend/Dockerfile`.

### Variables de entorno

Obligatorias:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | La de PostgreSQL, con el prefijo `postgresql+psycopg://` |
| `JWT_SECRET_KEY` | Una clave nueva: `openssl rand -hex 32` |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | La URL pública del frontend |
| `FRONTEND_URL` | La misma URL del frontend |

Opcionales, según qué integraciones quieras activas:

| Variable | Para qué |
|---|---|
| `GROQ_API_KEY` | Chatbot con IA |
| `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` | Pagos |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USER`, `EMAIL_PASSWORD` | Correos |
| `IVA_PORCENTAJE` | IVA aplicado (19 por defecto) |

> **Nunca** reutilices la `JWT_SECRET_KEY` de desarrollo. Quien la conozca
> puede firmar tokens válidos y entrar como cualquier usuario.

### Primer arranque

El `startCommand` de `railway.json` ejecuta `python seed.py` antes de
levantar el servidor. Eso crea las tablas, los permisos, los roles y los
usuarios de prueba. Es idempotente: en los siguientes despliegues no duplica
nada.

**Cambia las contraseñas de prueba en cuanto la aplicación esté en línea.**
Son públicas: están en este repositorio.

### Comprobación

```bash
curl https://tu-backend.up.railway.app/api/sistema/salud
```

Debe responder:

```json
{"estado":"ok","servicio":"Óleo & Lienzo API","version":"5.0.0"}
```

La documentación queda en `https://tu-backend.up.railway.app/docs`.

---

## 3. Frontend

El frontend es un sitio estático: se compila y se sirven los archivos.

**Comandos:**

| Ajuste | Valor |
|---|---|
| Build | `npm install && npm run build` |
| Directorio publicado | `dist` |

**Variable de entorno:**

```env
VITE_API_URL=https://tu-backend.up.railway.app
```

> Vite incrusta las variables **durante la compilación**, no al arrancar.
> Si cambias `VITE_API_URL`, hay que volver a compilar.

### Rutas del navegador

React Router maneja rutas como `/catalogo` en el cliente. El servidor debe
devolver `index.html` para cualquier ruta que no sea un archivo, o recargar
la página dará 404.

En Netlify, `public/_redirects`:

```
/*    /index.html   200
```

En Vercel, `vercel.json`:

```json
{ "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
```

---

## 4. Cerrar el círculo del CORS

Con la URL del frontend ya conocida, vuelve al backend y ajusta:

```env
CORS_ORIGINS=https://tu-frontend.up.railway.app
FRONTEND_URL=https://tu-frontend.up.railway.app
```

Sin esto el navegador bloqueará todas las llamadas a la API. `CORS_ORIGINS`
admite varias URL separadas por comas.

---

## 5. Webhook de Stripe

En el panel de Stripe → **Developers → Webhooks → Add endpoint**:

- URL: `https://tu-backend.up.railway.app/api/pagos/webhook`
- Eventos: `checkout.session.completed`, `checkout.session.expired`,
  `charge.refunded`

Copia el `whsec_...` que genera a la variable `STRIPE_WEBHOOK_SECRET`.

> El webhook **no** lleva autenticación JWT: quien llama es Stripe, no un
> usuario. Su autenticidad se comprueba verificando la firma criptográfica de
> la cabecera `Stripe-Signature`. Sin esa clave, el endpoint rechaza todo con
> un 400, que es el comportamiento correcto.

---

## 6. Repaso de seguridad antes de publicar

- [ ] `JWT_SECRET_KEY` nueva y aleatoria, distinta de la de desarrollo.
- [ ] `ENVIRONMENT=production`.
- [ ] Contraseñas de los usuarios de prueba cambiadas.
- [ ] `CORS_ORIGINS` con las URL exactas, nunca `*`.
- [ ] Ningún `.env` subido al repositorio (`git ls-files | grep .env` solo
      debe devolver los `.env.example`).
- [ ] Claves de Stripe en modo **live** solo cuando vayas a cobrar de verdad.
- [ ] La base de datos no expuesta a internet, solo accesible desde el backend.

---

## 7. Con Docker en tu propia máquina

Para levantar PostgreSQL y el backend juntos:

```bash
docker compose up --build
```

- API en http://localhost:8000
- PostgreSQL en el puerto 5432

El frontend sigue aparte, con `npm run dev`, para conservar la recarga en
caliente de Vite.

---

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `Can't load plugin: sqlalchemy.dialects:postgresql.psycopg` | Falta el prefijo del driver | Usa `postgresql+psycopg://` |
| El navegador bloquea las llamadas por CORS | El origen no está permitido | Añade la URL del frontend a `CORS_ORIGINS` |
| `net::ERR_CONNECTION_REFUSED` en el frontend | `VITE_API_URL` apunta a localhost | Recompila con la URL pública |
| Recargar `/catalogo` da 404 | Falta la redirección al `index.html` | Configura el *rewrite* del apartado 3 |
| 401 en todas las peticiones tras desplegar | Cambió la `JWT_SECRET_KEY` | Es lo esperado: los tokens antiguos ya no valen; vuelve a iniciar sesión |
| El webhook de Stripe responde 400 | Falta o no coincide `STRIPE_WEBHOOK_SECRET` | Copia el `whsec_` del endpoint concreto |
