"""Esquemas de facturación."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.factura import EstadoFactura
from app.schemas.venta import DetalleVentaOut


class FacturaCreate(BaseModel):
    """Emitir una factura a partir de una venta existente."""

    venta_id: int = Field(ge=1)
    observaciones: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={"example": {"venta_id": 1, "observaciones": None}}
    )


class FacturaCambioEstado(BaseModel):
    nuevo_estado: EstadoFactura

    model_config = ConfigDict(json_schema_extra={"example": {"nuevo_estado": "pagada"}})


class FacturaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: str
    venta_id: int
    cliente_id: int
    estado: EstadoFactura
    fecha_emision: datetime
    cliente_nombre: str
    cliente_documento: str
    cliente_email: str
    cliente_direccion: str
    cliente_telefono: str
    subtotal: float
    descuento: float
    impuestos: float
    iva_porcentaje: float
    total: float
    observaciones: str | None = None
    detalles: list[DetalleVentaOut] = []
