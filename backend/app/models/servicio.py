"""Servicios que la galería ofrece junto a las obras (enmarcado, envío…)."""
from sqlalchemy import Boolean, CheckConstraint, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Servicio(TimestampMixin, Base):
    __tablename__ = "servicios"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_servicios_precio_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    precio: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Servicio {self.nombre!r}>"
