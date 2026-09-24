"""Esquemas del módulo de PQR (peticiones, quejas y reclamos)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.pqr import EstadoPQR, TipoPQR
from app.schemas.usuario import UsuarioResumen


class PQRCreate(BaseModel):
    tipo: TipoPQR
    asunto: str = Field(min_length=5, max_length=140)
    mensaje: str = Field(min_length=10, max_length=2000)
    # Solo se usan cuando quien radica no ha iniciado sesión.
    contacto_nombre: str | None = Field(default=None, min_length=2, max_length=90)
    contacto_email: EmailStr | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tipo": "reclamo",
                "asunto": "La obra llegó con el marco dañado",
                "mensaje": "Recibí el pedido #12 y el marco venía roto en una esquina.",
                "contacto_nombre": "Sara Pérez",
                "contacto_email": "sara.perez@ejemplo.com",
            }
        }
    )


class PQRResponder(BaseModel):
    respuesta: str = Field(min_length=10, max_length=2000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "respuesta": "Lamentamos el inconveniente. Programamos la recogida "
                "y el reemplazo del marco sin costo."
            }
        }
    )


class PQRCambioEstado(BaseModel):
    nuevo_estado: EstadoPQR

    model_config = ConfigDict(json_schema_extra={"example": {"nuevo_estado": "en_proceso"}})


class PQROut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    radicado: str
    cliente_id: int | None = None
    cliente: UsuarioResumen | None = None
    contacto_nombre: str
    contacto_email: str
    tipo: TipoPQR
    asunto: str
    mensaje: str
    estado: EstadoPQR
    respuesta: str | None = None
    respondido_por_id: int | None = None
    respondido_en: datetime | None = None
    creado_en: datetime
    actualizado_en: datetime
