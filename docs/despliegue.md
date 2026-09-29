# Despliegue en la nube

Guía para poner Óleo & Lienzo en producción con tres servicios gratuitos:

| Capa | Plataforma | Por qué |
|---|---|---|
| Base de datos | **Neon** | PostgreSQL 16 gestionado, plan gratuito sin caducidad |
| Backend | **Render** | Despliega desde el `Dockerfile` del repositorio |
| Frontend | **Vercel** | Construye Vite y sirve por CDN |

Tiempo estimado: **30–40 minutos**. El orden importa: la base primero, porque
el backend la necesita; el frontend al final, porque necesita la URL del
backend.

> **Antes de empezar**, sube la rama a GitHub. Render y Vercel despliegan desde
> el repositorio, no desde tu máquina.

---

## 1. Base de datos en Neon

1. Entra en <https://neon.tech> y crea una cuenta (puedes usar GitHub).
2. **Create project**:
   - Nombre: `oleo-lienzo`
   - PostgreSQL: **16**
   - Región: la más cercana (`AWS us-east-2` sirve bien desde Colombia).
3. Al terminar, Neon muestra la cadena de conexión. Cópiala: solo se enseña
   entera una vez.

Vendrá con esta forma:

```
postgresql://usuario:contraseña@ep-algo-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Hay que adaptarla** antes de usarla. El proyecto usa el driver asíncrono
`psycopg`, así que cambia el esquema del principio:

```
postgresql+psycopg://usuario:contraseña@ep-algo-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

> Es el error más común de todo el despliegue. Si dejas `postgresql://` a
> secas, el backend arranca y falla en la primera consulta.

Guarda esa cadena: es el valor de `DATABASE_URL`.

### ¿Hay que ejecutar el script SQL?

No hace falta. La aplicación crea las tablas al arrancar. Si prefieres hacerlo
de forma explícita —y así compruebas el entregable del script SQL—, desde el
**SQL Editor** de Neon pega el contenido de
`backend/sql/schema_postgresql.sql` y ejecútalo.

---

## 2. Backend en Render

1. Entra en <https://render.com> y conecta tu cuenta de GitHub.
2. **New → Blueprint**, elige el repositorio `Oleo-Lienzo` y la rama `main`.
   Render detecta el archivo `render.yaml` de la raíz.
3. Te pedirá las variables marcadas como pendientes. Rellena:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | La cadena de Neon **con `postgresql+psycopg://`** |
| `CORS_ORIGINS` | Déjalo en `http://localhost:5173` de momento. Se corrige en el paso 4 |
| `FRONTEND_URL` | Igual: se corrige después |
| `GROQ_API_KEY` | Tu clave de <https://console.groq.com/keys>. Si la dejas vacía, el chatbot responde en modo local |

`JWT_SECRET_KEY` la genera Render sola y la conserva entre despliegues. No la
escribas tú.

4. **Apply**. La primera construcción tarda entre 5 y 8 minutos: compila la
   imagen Docker e instala las dependencias.

### Poblar la base la primera vez

Cuando el servicio esté activo, abre la pestaña **Shell** de Render y ejecuta:

```bash
python seed.py
```

Esto crea los permisos, los roles, los usuarios de prueba, el catálogo, las
ventas, facturas y PQR de ejemplo, y entrena el modelo de sugerencia de
precios. Es idempotente: ejecutarlo dos veces no duplica nada.

> **Cámbiale la contraseña al administrador** después de sembrar. Las
> credenciales del seed son públicas: están en el README y en el manual.

### Comprobar que vive

```bash
curl https://oleo-lienzo-api.onrender.com/api/sistema/salud
# {"estado":"ok","servicio":"Óleo & Lienzo API","version":"5.0.0"}
```

Y abre `https://oleo-lienzo-api.onrender.com/docs` en el navegador: debe salir
el Swagger con las 60 operaciones.

> **El plan gratuito de Render duerme el servicio** tras 15 minutos sin
> tráfico. La primera petición después de dormir tarda entre 30 y 50 segundos
> en responder. Antes de la sustentación, **abre la URL cinco minutos antes**
> para despertarlo.

---

## 3. Frontend en Vercel

1. Entra en <https://vercel.com> y conecta GitHub.
2. **Add New → Project**, elige el repositorio.
3. **Importante:** en *Root Directory* selecciona **`frontend`**. Si lo dejas
   en la raíz, Vercel no encontrará el `package.json`.
4. El resto lo toma de `frontend/vercel.json` (framework Vite, `npm ci`,
   salida en `dist`).
5. En **Environment Variables** añade:

| Variable | Valor |
|---|---|
| `VITE_API_URL` | `https://oleo-lienzo-api.onrender.com` — **sin barra final y sin `/api`** |
| `VITE_WHATSAPP_NUMERO` | El número en formato internacional sin el `+` |

6. **Deploy**. Tarda uno o dos minutos.

Vercel te dará una URL del estilo `https://oleo-lienzo.vercel.app`.

---

## 4. Cerrar el círculo: CORS

Ahora que existe la URL del frontend, hay que autorizarla en el backend. Sin
esto, el navegador bloqueará todas las llamadas y la aplicación se verá bien
pero no cargará ningún dato.

En Render, **Environment**, edita:

```
CORS_ORIGINS = https://oleo-lienzo.vercel.app
FRONTEND_URL = https://oleo-lienzo.vercel.app
```

Si quieres permitir también las URL de vista previa de Vercel, sepáralas por
comas. **El comodín `*` no se acepta**: la aplicación lo rechaza al arrancar,
a propósito.

Render reinicia el servicio solo. Espera a que vuelva a estar activo y prueba
la aplicación de punta a punta.

---

## 5. Comprobación final

Recorre esta lista en la URL pública, no en local:

| # | Qué probar | Qué debe pasar |
|---|---|---|
| 1 | Abrir la página de inicio | Carga el carrusel con las diez obras |
| 2 | Entrar al catálogo | Salen las obras con sus precios |
| 3 | Iniciar sesión como administrador | El navbar muestra el nombre |
| 4 | Abrir el dashboard | Salen los indicadores y los gráficos con datos |
| 5 | Descargar el PDF de una factura | Se descarga y se abre |
| 6 | Exportar el reporte a Excel | Se descarga el `.xlsx` |
| 7 | Escribir al chatbot | Responde (con IA si hay clave) |
| 8 | Abrir `/docs` del backend | Swagger con las 60 operaciones |
| 9 | Recargar estando en `/catalogo` | **No debe dar 404** |

El punto 9 comprueba el rewrite de `vercel.json`: sin él, recargar en una ruta
interna daría error, porque el servidor buscaría un archivo que no existe.

---

## 6. Repaso de seguridad antes de publicar

- [ ] Ningún archivo `.env` subido al repositorio (`git ls-files | grep .env`)
- [ ] `JWT_SECRET_KEY` generada por Render, no copiada de la de desarrollo
- [ ] `CORS_ORIGINS` con la lista explícita de orígenes, sin `*`
- [ ] Contraseña del administrador cambiada tras el seed
- [ ] `ENVIRONMENT=production` en Render
- [ ] La clave de Groq solo en las variables de Render, nunca en el código
- [ ] Si usas Stripe, solo claves de prueba (`sk_test_...`)

---

## Problemas frecuentes

| Síntoma | Causa casi segura | Solución |
|---|---|---|
| El backend arranca pero falla al consultar | La `DATABASE_URL` dice `postgresql://` | Cámbiala a `postgresql+psycopg://` |
| `sslmode` no soportado | Falta el parámetro o sobra | Deja `?sslmode=require` tal como lo da Neon |
| El frontend carga pero sin datos | CORS mal configurado | Revisa que `CORS_ORIGINS` tenga la URL exacta de Vercel, con `https://` y sin barra final |
| Error de CORS aunque la URL parece bien | Barra final de más | `https://app.vercel.app/` ≠ `https://app.vercel.app` |
| Recargar en `/catalogo` da 404 | Falta el rewrite | Comprueba que `frontend/vercel.json` se subió al repositorio |
| La primera petición tarda 40 segundos | Render durmió el servicio | Normal en el plan gratuito. Despiértalo antes de la demostración |
| `Application failed to respond` | La aplicación no escucha en `$PORT` | El `Dockerfile` ya lo resuelve; comprueba que no se haya modificado |
| El backend no arranca y el log dice `JWT_SECRET_KEY` | Falta la variable con `ENVIRONMENT=production` | Es deliberado: genera una clave y configúrala |
| El chatbot responde pero dice `generado_por_ia: false` | Falta `GROQ_API_KEY` | Añádela en Render. Sin ella funciona, pero en modo local |

---

## Despliegue local con Docker

Para probar la imagen de producción sin subir nada:

```bash
docker compose up --build
```

Levanta PostgreSQL y el backend juntos. El frontend sigue aparte, con
`cd frontend && npm run dev`, para conservar la recarga en caliente.
