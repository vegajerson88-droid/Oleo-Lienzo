"""Middlewares propios de la aplicación.

Viven fuera de `main.py` para que ese archivo contenga solo la configuración
de la app, los middlewares que registra y el `include_router`.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("oleo_lienzo.http")

# Cabeceras defensivas que se añaden a todas las respuestas.
CABECERAS_DE_SEGURIDAD = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# Rutas que no se registran: el sondeo de salud de la plataforma de despliegue
# se consulta cada pocos segundos y ahogaría el log.
RUTAS_SILENCIADAS = frozenset({"/api/sistema/salud"})


class RegistroDePeticiones(BaseHTTPMiddleware):
    """Registra cada petición con su identificador, estado y duración.

    A cada petición se le asigna un `X-Request-ID` que viaja en la respuesta:
    permite localizar en el log exactamente la llamada que falló.
    """

    async def dispatch(self, request: Request, call_next):
        peticion_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.peticion_id = peticion_id
        comienzo = time.perf_counter()

        try:
            respuesta = await call_next(request)
        except Exception:
            # La traza la registra el manejador global; aquí solo se deja
            # constancia de qué petición fue, con su identificador.
            duracion = (time.perf_counter() - comienzo) * 1000
            logger.error(
                "%s %s %s -> error no controlado en %.1f ms",
                peticion_id,
                request.method,
                request.url.path,
                duracion,
            )
            raise

        duracion = (time.perf_counter() - comienzo) * 1000
        respuesta.headers["X-Request-ID"] = peticion_id

        if request.url.path not in RUTAS_SILENCIADAS:
            # Un 5xx es un fallo del servidor y merece nivel de error; un 4xx
            # es culpa de la petición y basta con avisar.
            if respuesta.status_code >= 500:
                registrar = logger.error
            elif respuesta.status_code >= 400:
                registrar = logger.warning
            else:
                registrar = logger.info
            registrar(
                "%s %s %s -> %d en %.1f ms",
                peticion_id,
                request.method,
                request.url.path,
                respuesta.status_code,
                duracion,
            )

        return respuesta


class CabecerasDeSeguridad(BaseHTTPMiddleware):
    """Añade las cabeceras defensivas a todas las respuestas."""

    async def dispatch(self, request: Request, call_next):
        respuesta = await call_next(request)
        respuesta.headers.update(CABECERAS_DE_SEGURIDAD)
        return respuesta
