"""Esquemas de pedidos: la orden que arma el cliente en el sitio web."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.pedido import EstadoPedido
from app.schemas.obra import ObraResumen
from app.schemas.servicio import ServicioResumen


class DetallePedidoCreate(BaseModel):
    """Una línea del pedido: obra O servicio, nunca los dos."""

    obra_id: int | None = Field(default=None, ge=1)
    servicio_id: int | None = Field(default=None, ge=1)
    cantidad: int = Field(default=1, ge=1, le=99)

    @model_validator(mode="after")
    def exactamente_uno(self) -> "DetallePedidoCreate":
        if bool(self.obra_id) == bool(self.servicio_id):
            raise ValueError("Indica exactamente un obra_id o un servicio_id.")
        return self


class DetallePedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    obra: ObraResumen | None = None
    servicio: ServicioResumen | None = None
    descripcion: str
    cantidad: int
    precio_unitario: float
    subtotal: float


class PedidoCreate(BaseModel):
    detalles: list[DetallePedidoCreate] = Field(min_length=1, max_length=50)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detalles": [
                    {"obra_id": 1, "cantidad": 1},
                    {"servicio_id": 1, "cantidad": 1},
                ]
            }
        }
    )


class PedidoCambioEstado(BaseModel):
    nuevo_estado: EstadoPedido

    model_config = ConfigDict(json_schema_extra={"example": {"nuevo_estado": "confirmado"}})


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cliente_id: int
    estado: EstadoPedido
    total: float
    creado_en: datetime
    actualizado_en: datetime
    detalles: list[DetallePedidoOut]
