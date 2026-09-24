"""Facturas de venta.

La factura es un documento congelado: copia los importes de la venta en el
momento de emitirse y ya no cambia aunque la venta se edite después.
"""

import enum
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, ahora_utc


class EstadoFactura(str, enum.Enum):
    emitida = "emitida"
    pagada = "pagada"
    anulada = "anulada"


TRANSICIONES_FACTURA: dict[EstadoFactura, set[EstadoFactura]] = {
    EstadoFactura.emitida: {EstadoFactura.pagada, EstadoFactura.anulada},
    EstadoFactura.pagada: {EstadoFactura.anulada},
    EstadoFactura.anulada: set(),
}

EstadoFacturaDB = Enum(
    EstadoFactura,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="estado_factura",
)


class Factura(TimestampMixin, Base):
    __tablename__ = "facturas"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_facturas_subtotal_no_negativo"),
        CheckConstraint("total >= 0", name="ck_facturas_total_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Consecutivo fiscal legible: OL-000001.
    numero: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)

    # Una venta genera como máximo una factura.
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    estado: Mapped[EstadoFactura] = mapped_column(
        EstadoFacturaDB, default=EstadoFactura.emitida, nullable=False
    )
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=ahora_utc, nullable=False, index=True
    )

    # Datos del cliente congelados en el momento de emitir.
    cliente_nombre: Mapped[str] = mapped_column(String(90), nullable=False)
    cliente_documento: Mapped[str] = mapped_column(String(25), nullable=False)
    cliente_email: Mapped[str] = mapped_column(String(80), nullable=False)
    cliente_direccion: Mapped[str] = mapped_column(String(100), nullable=False)
    cliente_telefono: Mapped[str] = mapped_column(String(15), nullable=False)

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    descuento: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    impuestos: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    iva_porcentaje: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    venta: Mapped["Venta"] = relationship(back_populates="factura", lazy="joined")
    cliente: Mapped["Usuario"] = relationship(foreign_keys=[cliente_id])

    @property
    def detalles(self) -> list:
        """Líneas facturadas: son las de la venta que originó la factura."""
        return list(self.venta.detalles) if self.venta else []

    def __repr__(self) -> str:
        return f"<Factura {self.numero} {self.estado}>"
