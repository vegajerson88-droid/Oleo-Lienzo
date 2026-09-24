"""Líneas de un pedido: obras y/o servicios con su cantidad y precio."""
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DetallePedido(Base):
    __tablename__ = "detalles_pedido"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalles_pedido_cantidad_positiva"),
        CheckConstraint(
            "precio_unitario >= 0", name="ck_detalles_pedido_precio_no_negativo"
        ),
        # Cada línea apunta exactamente a una obra o a un servicio, nunca a
        # ambos ni a ninguno.
        CheckConstraint(
            "(obra_id IS NOT NULL AND servicio_id IS NULL) OR "
            "(obra_id IS NULL AND servicio_id IS NOT NULL)",
            name="ck_detalles_pedido_obra_xor_servicio",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    obra_id: Mapped[int | None] = mapped_column(
        ForeignKey("obras.id", ondelete="RESTRICT"), nullable=True
    )
    servicio_id: Mapped[int | None] = mapped_column(
        ForeignKey("servicios.id", ondelete="RESTRICT"), nullable=True
    )
    # Copia del nombre en el momento del pedido: si la obra cambia de título
    # más adelante, el histórico del pedido no se altera.
    descripcion: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    cantidad: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    precio_unitario: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    pedido: Mapped["Pedido"] = relationship(back_populates="detalles")
    obra: Mapped["Obra | None"] = relationship(lazy="joined")
    servicio: Mapped["Servicio | None"] = relationship(lazy="joined")

    @property
    def subtotal(self) -> float:
        return float(self.precio_unitario) * self.cantidad
