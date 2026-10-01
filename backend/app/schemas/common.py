"""Esquemas compartidos por todos los módulos de la API."""

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Cuerpo uniforme de error que devuelve toda la API."""

    error: str = Field(description="Nombre técnico del error.")
    detail: str | list | dict = Field(description="Descripción legible del problema.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"error": "NotFoundError", "detail": "Obra 42 no encontrada."}
        }
    )


class Page(BaseModel, Generic[T]):
    """Respuesta paginada estándar."""

    items: list[T]
    total: int = Field(description="Total de registros que cumplen el filtro.")
    page: int = Field(description="Página actual, empezando en 1.")
    page_size: int = Field(description="Tamaño de página solicitado.")

    @property
    def total_paginas(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class MensajeRespuesta(BaseModel):
    """Respuesta simple para operaciones que no devuelven un recurso."""

    mensaje: str


class RecuperacionRespuesta(BaseModel):
    """Respuesta de la solicitud de recuperación de contraseña.

    `correo_operativo` describe el **sistema**, no la cuenta: dice si el
    servidor tiene SMTP configurado. Nunca revela si ese correo está
    registrado, que es lo que esta pantalla debe seguir ocultando.

    `enlace_desarrollo` solo aparece fuera de producción y cuando no hay SMTP:
    permite probar el flujo completo sin un servidor de correo. En producción
    vale siempre `None`.
    """

    mensaje: str
    correo_operativo: bool
    enlace_desarrollo: str | None = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"mensaje": "Operación completada correctamente."}}
    )
