"""Ventas: la transacción comercial del proyecto.

Una venta nace de dos maneras:
  * automáticamente, cuando un pedido del sitio web pasa a `confirmado`;
  * manualmente, cuando un administrador o empleado registra una venta
    presencial desde el panel.

Guarda el desglose económico completo (subtotal, descuento, IVA, total) porque
es la fuente de la que se alimentan los reportes, los dashboards y las facturas.
"""

import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class EstadoVenta(str, enum.Enum):
    pendiente_pago = "pendiente_pago"
    pagada = "pagada"
    anulada = "anulada"
    reembolsada = "reembolsada"


class MetodoPago(str, enum.Enum):
    efectivo = "efectivo"
    transferencia = "transferencia"
    tarjeta = "tarjeta"
    otro = "otro"


# Una venta pagada ya no puede anularse: se reembolsa, que deja rastro contable.
TRANSICIONES_VENTA: dict[EstadoVenta, set[EstadoVenta]] = {
    EstadoVenta.pendiente_pago: {EstadoVenta.pagada, EstadoVenta.anulada},
    EstadoVenta.pagada: {EstadoVenta.reembolsada},
    EstadoVenta.anulada: set(),
    EstadoVenta.reembolsada: set(),
}

EstadoVentaDB = Enum(
    EstadoVenta,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="estado_venta",
)

MetodoPagoDB = Enum(
    MetodoPago,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="metodo_pago",
)


class Venta(TimestampMixin, Base):
    __tablename__ = "ventas"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_ventas_subtotal_no_negativo"),
        CheckConstraint("descuento >= 0", name="ck_ventas_descuento_no_negativo"),
        CheckConstraint("impuestos >= 0", name="ck_ventas_impuestos_no_negativo"),
        CheckConstraint("total >= 0", name="ck_ventas_total_no_negativo"),
        CheckConstraint("descuento <= subtotal", name="ck_ventas_descuento_max"),
        Index("ix_ventas_creado_estado", "creado_en", "estado"),
        Index("ix_ventas_cliente_creado", "cliente_id", "creado_en"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Consecutivo legible: V-2026-000001. Se asigna tras obtener el id.
    numero: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)

    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Empleado o administrador que registró la operación. Nulo cuando la venta
    # se generó sola desde el sitio web.
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    pedido_id: Mapped[int | None] = mapped_column(
        ForeignKey("pedidos.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    estado: Mapped[EstadoVenta] = mapped_column(
        EstadoVentaDB, default=EstadoVenta.pendiente_pago, nullable=False
    )
    metodo_pago: Mapped[MetodoPago] = mapped_column(
        MetodoPagoDB, default=MetodoPago.tarjeta, nullable=False
    )

    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    descuento: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    impuestos: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    cliente: Mapped["Usuario"] = relationship(
        back_populates="ventas", foreign_keys=[cliente_id], lazy="joined"
    )
    registrada_por: Mapped["Usuario | None"] = relationship(foreign_keys=[usuario_id])
    pedido: Mapped["Pedido | None"] = relationship(back_populates="venta")
    detalles: Mapped[list["DetalleVenta"]] = relationship(
        back_populates="venta", cascade="all, delete-orphan", lazy="selectin"
    )
    factura: Mapped["Factura | None"] = relationship(
        back_populates="venta", uselist=False, lazy="selectin"
    )
    pagos: Mapped[list["Pago"]] = relationship(
        back_populates="venta", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def factura_numero(self) -> str | None:
        """Número de la factura emitida, si ya se emitió."""
        return self.factura.numero if self.factura else None

    def __repr__(self) -> str:
        return f"<Venta {self.numero} {self.estado}>"
