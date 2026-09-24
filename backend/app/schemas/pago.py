"""Esquemas de la pasarela de pago (Stripe)."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.pago import EstadoPago


class CheckoutRequest(BaseModel):
    """Inicia el pago de una venta ya registrada."""

    venta_id: int = Field(ge=1)

    model_config = ConfigDict(json_schema_extra={"example": {"venta_id": 1}})


class CheckoutResponse(BaseModel):
    checkout_url: str = Field(description="URL alojada por Stripe donde paga el cliente.")
    session_id: str
    publishable_key: str = Field(description="Clave pública, segura de exponer.")


class PagoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    venta_id: int
    proveedor: str
    referencia_externa: str | None = None
    estado: EstadoPago
    monto: float
    moneda: str
