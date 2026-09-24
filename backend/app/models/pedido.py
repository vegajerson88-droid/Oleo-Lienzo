import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EstadoPedido(str, enum.Enum):
    pendiente = "pendiente"
    confirmado = "confirmado"
    entregado = "entregado"
    cancelado = "cancelado"


# Transiciones válidas de estado (de -> conjunto de estados permitidos)
TRANSICIONES_VALIDAS: dict[EstadoPedido, set[EstadoPedido]] = {
    EstadoPedido.pendiente: {EstadoPedido.confirmado, EstadoPedido.cancelado},
    EstadoPedido.confirmado: {EstadoPedido.entregado, EstadoPedido.cancelado},
    EstadoPedido.entregado: set(),
    EstadoPedido.cancelado: set(),
}


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    estado: Mapped[EstadoPedido] = mapped_column(
        Enum(EstadoPedido), default=EstadoPedido.pendiente, nullable=False
    )
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    cliente: Mapped["Usuario"] = relationship(back_populates="pedidos", lazy="joined")
    detalles: Mapped[list["DetallePedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )
