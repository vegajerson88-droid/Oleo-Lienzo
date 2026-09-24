"""Esquemas de obras (el catálogo de productos)."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

ANIO_MIN = 1400


def _validar_anio(v: int) -> int:
    anio_actual = date.today().year
    if v < ANIO_MIN or v > anio_actual:
        raise ValueError(f"anio debe estar entre {ANIO_MIN} y {anio_actual}.")
    return v


class ObraBase(BaseModel):
    titulo: str = Field(min_length=2, max_length=120)
    artista: str = Field(min_length=2, max_length=80)
    anio: int = Field(description=f"Año de creación, entre {ANIO_MIN} y el año actual.")
    tecnica: str = Field(min_length=2, max_length=80)
    precio: float = Field(gt=0, description="Precio en pesos colombianos.")
    descripcion: str = Field(min_length=5, max_length=2000)
    imagen_url: str | None = Field(default=None, max_length=255)
    disponible: bool = True
    stock: int = Field(default=1, ge=0, le=9999)

    _val_anio = field_validator("anio")(_validar_anio)


class ObraCreate(ObraBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "titulo": "Amanecer en el Valle", "artista": "Marina Solórzano",
                "anio": 2021, "tecnica": "Óleo sobre lienzo", "precio": 1250000,
                "descripcion": "Pinceladas cálidas que capturan la luz del primer sol.",
                "imagen_url": None, "disponible": True, "stock": 1,
            }
        }
    )


class ObraReplace(ObraBase):
    """Reemplazo COMPLETO del recurso (PUT). Exige todos los campos."""


class ObraUpdate(BaseModel):
    """Actualización PARCIAL (PATCH). Solo se modifica lo que se envía."""

    titulo: str | None = Field(default=None, min_length=2, max_length=120)
    artista: str | None = Field(default=None, min_length=2, max_length=80)
    anio: int | None = None
    tecnica: str | None = Field(default=None, min_length=2, max_length=80)
    precio: float | None = Field(default=None, gt=0)
    descripcion: str | None = Field(default=None, min_length=5, max_length=2000)
    imagen_url: str | None = Field(default=None, max_length=255)
    disponible: bool | None = None
    stock: int | None = Field(default=None, ge=0, le=9999)

    @field_validator("anio")
    @classmethod
    def validar_anio(cls, v: int | None) -> int | None:
        return v if v is None else _validar_anio(v)


class ObraOut(ObraBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: datetime


class ObraResumen(BaseModel):
    """Versión ligera para incrustar en pedidos, ventas y facturas."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    titulo: str
    artista: str
    precio: float
    imagen_url: str | None = None
