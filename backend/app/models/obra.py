from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Obra(Base):
    __tablename__ = "obras"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    artista: Mapped[str] = mapped_column(String(80), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    tecnica: Mapped[str] = mapped_column(String(80), nullable=False)
    precio: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    imagen_url: Mapped[str] = mapped_column(String(255), nullable=True)
    disponible: Mapped[bool] = mapped_column(default=True)
