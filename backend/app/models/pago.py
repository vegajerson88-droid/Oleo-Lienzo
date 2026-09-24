"""Pagos asociados a una venta.

Solo se guardan referencias del proveedor (Stripe). Ningún dato de tarjeta
—número, CVV, fecha de expiración— toca nuestra base de datos: el cliente
introduce esa información directamente en el checkout alojado por Stripe.
"""

import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class EstadoPago(str, enum.Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    fallido = "fallido"
    reembolsado = "reembolsado"


EstadoPagoDB = Enum(
    EstadoPago,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="estado_pago",
)


class Pago(TimestampMixin, Base):
    __tablename__ = "pagos"
    __table_args__ = (CheckConstraint("monto >= 0", name="ck_pagos_monto_no_negativo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proveedor: Mapped[str] = mapped_column(String(30), default="stripe", nullable=False)
    # Identificador de la sesión de checkout en el proveedor.
    referencia_externa: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payment_intent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estado: Mapped[EstadoPago] = mapped_column(
        EstadoPagoDB, default=EstadoPago.pendiente, nullable=False
    )
    monto: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    moneda: Mapped[str] = mapped_column(String(6), default="COP", nullable=False)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)

    venta: Mapped["Venta"] = relationship(back_populates="pagos")

    def __repr__(self) -> str:
        return f"<Pago venta={self.venta_id} {self.estado}>"
