from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    apellido: Mapped[str] = mapped_column(String(40), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(5), nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    direccion: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[str] = mapped_column(String(10), nullable=False)
    email: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    rol: Mapped["Rol"] = relationship(back_populates="usuarios", lazy="joined")

    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cliente")
