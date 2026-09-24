"""Líneas de una venta: qué obra o servicio se vendió, cuánto y a qué precio."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DetalleVenta(Base):
    __tablename__ = "detalle_ventas"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalle_ventas_cantidad_positiva"),
        CheckConstraint("precio_unitario >= 0", name="ck_detalle_ventas_precio_no_negativo"),
        CheckConstraint("descuento >= 0", name="ck_detalle_ventas_descuento_no_negativo"),
        CheckConstraint("subtotal >= 0", name="ck_detalle_ventas_subtotal_no_negativo"),
        CheckConstraint(
            "(obra_id IS NOT NULL AND servicio_id IS NULL) OR "
            "(obra_id IS NULL AND servicio_id IS NOT NULL)",
            name="ck_detalle_ventas_obra_xor_servicio",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    obra_id: Mapped[int | None] = mapped_column(
        ForeignKey("obras.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servicios.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    # Instantánea del nombre y del precio: la factura no debe cambiar si más
    # tarde se edita el catálogo.
    descripcion: Mapped[str] = mapped_column(String(160), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    descuento: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    venta: Mapped["Venta"] = relationship(back_populates="detalles")
    obra: Mapped["Obra | None"] = relationship(lazy="joined")
    servicio: Mapped["Servicio | None"] = relationship(lazy="joined")

    @property
    def tipo(self) -> str:
        return "obra" if self.obra_id else "servicio"
