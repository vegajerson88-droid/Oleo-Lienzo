"""Esquemas del módulo de ventas."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.venta import EstadoVenta, MetodoPago
from app.schemas.obra import ObraResumen
from app.schemas.servicio import ServicioResumen
from app.schemas.usuario import UsuarioResumen


class DetalleVentaCreate(BaseModel):
    obra_id: int | None = Field(default=None, ge=1)
    servicio_id: int | None = Field(default=None, ge=1)
    cantidad: int = Field(default=1, ge=1, le=99)
    descuento: float = Field(default=0, ge=0, description="Descuento de esta línea, en pesos.")

    @model_validator(mode="after")
    def exactamente_uno(self) -> "DetalleVentaCreate":
        if bool(self.obra_id) == bool(self.servicio_id):
            raise ValueError("Indica exactamente un obra_id o un servicio_id.")
        return self


class DetalleVentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    obra: ObraResumen | None = None
    servicio: ServicioResumen | None = None
    descripcion: str
    cantidad: int
    precio_unitario: float
    descuento: float
    subtotal: float


class VentaCreate(BaseModel):
    """Registro manual de una venta desde el panel (venta presencial)."""

    cliente_id: int = Field(ge=1)
    detalles: list[DetalleVentaCreate] = Field(min_length=1, max_length=50)
    descuento: float = Field(default=0, ge=0, description="Descuento global, en pesos.")
    metodo_pago: MetodoPago = MetodoPago.efectivo
    observaciones: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cliente_id": 3,
                "detalles": [
                    {"obra_id": 1, "cantidad": 1, "descuento": 0},
                    {"servicio_id": 1, "cantidad": 1, "descuento": 0},
                ],
                "descuento": 50000,
                "metodo_pago": "efectivo",
                "observaciones": "Venta en sala, entrega inmediata.",
            }
        }
    )


class VentaCambioEstado(BaseModel):
    nuevo_estado: EstadoVenta

    model_config = ConfigDict(json_schema_extra={"example": {"nuevo_estado": "pagada"}})


class VentaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    numero: str
    cliente_id: int
    cliente: UsuarioResumen | None = None
    usuario_id: int | None = None
    pedido_id: int | None = None
    estado: EstadoVenta
    metodo_pago: MetodoPago
    subtotal: float
    descuento: float
    impuestos: float
    total: float
    observaciones: str | None = None
    creado_en: datetime
    actualizado_en: datetime
    detalles: list[DetalleVentaOut] = []
    factura_numero: str | None = None


class VentaFiltros(BaseModel):
    """Criterios del historial de ventas (requisito 3 del quinto avance)."""

    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    cliente_id: int | None = Field(default=None, ge=1)
    obra_id: int | None = Field(default=None, ge=1)
    servicio_id: int | None = Field(default=None, ge=1)
    estado: EstadoVenta | None = None
    total_min: float | None = Field(default=None, ge=0)
    total_max: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def rangos_coherentes(self) -> "VentaFiltros":
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValueError("fecha_inicio no puede ser posterior a fecha_fin.")
        if (
            self.total_min is not None
            and self.total_max is not None
            and self.total_min > self.total_max
        ):
            raise ValueError("total_min no puede ser mayor que total_max.")
        return self
