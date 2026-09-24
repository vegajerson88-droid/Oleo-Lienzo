"""Punto de entrada de la API de Óleo & Lienzo.

Arquitectura del proyecto:

    React + Vite  →  FastAPI  →  PostgreSQL

Todos los endpoints cuelgan del prefijo `/api`.
"""
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.core.limiter import limiter
from app.database import init_models
from app.routers import (
    auth,
    chatbot,
    dashboard,
    facturas,
    ia,
    pagos,
    pedidos,
    pqr,
    productos,
    reportes,
    servicios,
    sistema,
    usuarios,
    ventas,
)
from app.services import ai_local

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("oleo_lienzo")

DESCRIPCION = f"""
API REST de **Óleo & Lienzo**, una galería de arte que vende pinturas
originales y servicios asociados.

### Arquitectura

```
React + Vite  →  FastAPI  →  PostgreSQL
```

### Cómo autenticarse en esta documentación

1. Pulsa **Authorize** (arriba a la derecha).
2. Introduce el **correo** en el campo `username` y la contraseña.
3. Las rutas protegidas ya enviarán `Authorization: Bearer <token>`.

Usuarios de prueba que crea `python seed.py`:

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@oleoylienzo.com` | `Admin1234` |
| Empleado | `empleado@oleoylienzo.com` | `Empleado123` |
| Cliente | `cliente@oleoylienzo.com` | `Cliente123` |

### Roles

| Rol | Alcance |
|---|---|
| **Administrador** | Todo: usuarios, catálogo, ventas, facturas, PQR y diagnóstico. |
| **Empleado** | Catálogo, pedidos, ventas, facturas y PQR. Sin gestión de usuarios. |
| **Cliente** | Su propio catálogo, pedidos, compras, facturas y PQR. |

La autorización definitiva **siempre** la decide el backend.

### Códigos de respuesta

| Código | Significado |
|---|---|
| `200` / `201` / `204` | Operación correcta |
| `401` | Falta el token o no es válido |
| `403` | Autenticado pero sin permisos |
| `404` | El recurso no existe |
| `409` | Conflicto (duplicado o restricción única) |
| `422` | Validación o regla de negocio incumplida |
| `429` | Demasiadas peticiones |

Todos los errores comparten el mismo formato: `{{"error": "...", "detail": "..."}}`.

### Configuración

Los datos sensibles se leen de variables de entorno (ver `.env.example`).
El IVA aplicado es del **{settings.iva_porcentaje:g}%**.
"""

ETIQUETAS = [
    {"name": "Autenticación", "description": "Registro, inicio de sesión con JWT y gestión de la contraseña."},
    {"name": "Usuarios", "description": "CRUD de usuarios, roles y permisos. Solo administrador."},
    {"name": "Obras / Productos", "description": "Catálogo de obras. Lectura pública, escritura restringida."},
    {"name": "Servicios", "description": "Enmarcado, restauración y envío asegurado."},
    {"name": "Pedidos", "description": "Órdenes del cliente. Confirmar un pedido genera su venta."},
    {"name": "Ventas", "description": "Registro e historial comercial con filtros y desglose de IVA."},
    {"name": "Facturación", "description": "Emisión, consulta y descarga de facturas en PDF."},
    {"name": "Reportes", "description": "Reporte diario de ventas en JSON, PDF y Excel."},
    {"name": "Dashboard", "description": "Indicadores y gráficos calculados en la base de datos, por rol."},
    {"name": "PQR", "description": "Peticiones, quejas, reclamos y sugerencias."},
    {"name": "Chatbot IA", "description": "Asistente de atención al cliente con Groq."},
    {"name": "Pagos (Stripe)", "description": "Checkout alojado y webhook firmado."},
    {"name": "Inteligencia Artificial", "description": "Modelo propio de precios y redacción asistida."},
    {"name": "Sistema", "description": "Salud y diagnóstico real de cada dependencia."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque y apagado de la aplicación."""
    await init_models()
    # El modelo de IA local se carga una sola vez, no en cada petición.
    app.state.ai_local_model = ai_local.cargar_modelo()
    if app.state.ai_local_model is None:
        logger.info("Modelo de IA local no encontrado; el endpoint lo informará.")
    logger.info("%s v%s lista en entorno '%s'.", settings.app_name, settings.app_version, settings.environment)
    yield
    logger.info("Cerrando %s.", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=DESCRIPCION,
    openapi_tags=ETIQUETAS,
    lifespan=lifespan,
    contact={"name": settings.empresa_nombre, "email": settings.empresa_email},
    license_info={"name": "Uso académico — Ficha 3406211, SENA"},
    swagger_ui_parameters={"docExpansion": "none", "filter": True, "persistAuthorization": True},
)

# ── Middlewares ──────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # el navegador necesita leerla para descargar PDF/Excel
)


@app.middleware("http")
async def cabeceras_de_seguridad(request: Request, call_next):
    """Cabeceras defensivas en todas las respuestas."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# ── Manejadores de error: un único formato para toda la API ──────────────
@app.exception_handler(DomainError)
async def manejar_error_de_dominio(request: Request, exc: DomainError):
    """Traduce las excepciones de negocio al código HTTP que les corresponde."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def manejar_error_de_validacion(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "ValidationError", "detail": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(RateLimitExceeded)
async def manejar_limite_de_peticiones(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "RateLimitExceeded",
            "detail": "Has hecho demasiadas peticiones. Espera un momento e inténtalo de nuevo.",
        },
    )


@app.exception_handler(Exception)
async def manejar_error_no_controlado(request: Request, exc: Exception):
    """Último recurso: registra la traza completa y no la expone al cliente."""
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "InternalServerError", "detail": "Ocurrió un error interno."},
    )


# ── Rutas: todo cuelga de /api ───────────────────────────────────────────
PREFIJO = "/api"
for router in (
    auth.router, usuarios.router, productos.router, servicios.router,
    pedidos.router, ventas.router, facturas.router, reportes.router,
    dashboard.router, pqr.router, chatbot.router, pagos.router,
    ia.router, sistema.router,
):
    app.include_router(router, prefix=PREFIJO)


@app.get("/", tags=["Sistema"], summary="Información de la API")
async def raiz():
    return {
        "servicio": settings.app_name,
        "version": settings.app_version,
        "documentacion": "/docs",
        "documentacion_alternativa": "/redoc",
        "prefijo_api": PREFIJO,
    }
