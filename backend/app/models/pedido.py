"""Pedidos: la orden que el cliente arma desde el sitio web.

Un pedido confirmado genera una venta (ver `app/models/venta.py`), que a su
vez puede facturarse. Ese encadenamiento es la columna vertebral de la lógica
comercial del proyecto.
"""
import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class EstadoPedido(str, enum.Enum):
    pendiente = "pendiente"
    confirmado = "confirmado"
    entregado = "entregado"
    cancelado = "cancelado"


# Transiciones válidas de estado (origen -> destinos permitidos).
TRANSICIONES_VALIDAS: dict[EstadoPedido, set[EstadoPedido]] = {
    EstadoPedido.pendiente: {EstadoPedido.confirmado, EstadoPedido.cancelado},
    EstadoPedido.confirmado: {EstadoPedido.entregado, EstadoPedido.cancelado},
    EstadoPedido.entregado: set(),
    EstadoPedido.cancelado: set(),
}

# `native_enum=False` guarda el estado como VARCHAR + CHECK: portable entre
# PostgreSQL y SQLite, y legible en el script SQL.
EstadoPedidoDB = Enum(
    EstadoPedido,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="estado_pedido",
)


class Pedido(TimestampMixin, Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_pedidos_total_no_negativo"),
        Index("ix_pedidos_cliente_estado", "cliente_id", "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    estado: Mapped[EstadoPedido] = mapped_column(
        EstadoPedidoDB, default=EstadoPedido.pendiente, nullable=False
    )
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    cliente: Mapped["Usuario"] = relationship(
        back_populates="pedidos", foreign_keys=[cliente_id], lazy="joined"
    )
    detalles: Mapped[list["DetallePedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )
    venta: Mapped["Venta | None"] = relationship(back_populates="pedido", uselist=False)

    def __repr__(self) -> str:
        return f"<Pedido #{self.id} {self.estado}>"
