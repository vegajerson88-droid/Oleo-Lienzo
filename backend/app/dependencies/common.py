"""Tipos y utilidades compartidos por los routers."""

from typing import Annotated

from fastapi import Path, Query

# Identificador de recurso en la ruta, validado: nunca llega un 0 o un negativo
# a la capa de datos (criterio «parámetros de ruta con validación»).
IdPath = Annotated[
    int, Path(ge=1, description="Identificador numérico del recurso, mayor que cero.")
]

BuscarQuery = Annotated[
    str | None,
    Query(
        min_length=2,
        max_length=80,
        description="Texto libre de búsqueda. Mínimo 2 caracteres.",
    ),
]

# Respuestas de error reutilizables en la documentación de OpenAPI.
RESPUESTAS_AUTH = {
    401: {"description": "No autenticado: falta el token o no es válido."},
    403: {"description": "Autenticado pero sin permisos suficientes para esta operación."},
}

RESPUESTA_404 = {404: {"description": "El recurso solicitado no existe."}}
RESPUESTA_409 = {
    409: {"description": "Conflicto: el recurso ya existe o viola una restricción única."}
}
RESPUESTA_422 = {422: {"description": "Los datos enviados no superan la validación."}}
