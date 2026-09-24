from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.pedido import EstadoPedido
from app.schemas.obra import ObraOut


class DetallePedidoCreate(BaseModel):
    obra_id: int
    cantidad: int = Field(default=1, ge=1)


class DetallePedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    obra: ObraOut
    cantidad: int
    precio_unitario: float


class PedidoCreate(BaseModel):
    detalles: list[DetallePedidoCreate] = Field(min_length=1)


class PedidoCambioEstado(BaseModel):
    nuevo_estado: EstadoPedido


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cliente_id: int
    estado: EstadoPedido
    total: float
    creado_en: datetime
    actualizado_en: datetime
    detalles: list[DetallePedidoOut]
