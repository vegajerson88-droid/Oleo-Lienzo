"""Esquemas de servicios (enmarcado, restauración, envío…)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ServicioBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str = Field(min_length=5, max_length=2000)
    precio: float = Field(gt=0, description="Precio en pesos colombianos.")
    activo: bool = True


class ServicioCreate(ServicioBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Enmarcado personalizado",
                "descripcion": "Enmarcado a medida para obras adquiridas en la galería.",
                "precio": 150000,
                "activo": True,
            }
        }
    )


class ServicioReplace(ServicioBase):
    """Reemplazo COMPLETO del recurso (PUT)."""


class ServicioUpdate(BaseModel):
    """Actualización PARCIAL (PATCH)."""

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, min_length=5, max_length=2000)
    precio: float | None = Field(default=None, gt=0)
    activo: bool | None = None


class ServicioOut(ServicioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creado_en: datetime


class ServicioResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    precio: float
