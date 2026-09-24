"""Obras de arte: el catálogo de productos de la galería."""
from sqlalchemy import Boolean, CheckConstraint, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin


class Obra(TimestampMixin, Base):
    __tablename__ = "obras"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_obras_precio_positivo"),
        CheckConstraint("stock >= 0", name="ck_obras_stock_no_negativo"),
        CheckConstraint("anio >= 1400", name="ck_obras_anio_minimo"),
        Index("ix_obras_artista", "artista"),
        Index("ix_obras_disponible", "disponible"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    artista: Mapped[str] = mapped_column(String(80), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    tecnica: Mapped[str] = mapped_column(String(80), nullable=False)
    precio: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    imagen_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    disponible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Cada obra es una pieza única, pero el stock permite series y reimpresiones.
    stock: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    def __repr__(self) -> str:
        return f"<Obra {self.titulo!r}>"
