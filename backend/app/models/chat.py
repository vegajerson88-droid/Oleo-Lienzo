"""Conversaciones y mensajes del chatbot.

Se persisten para poder darle memoria al asistente dentro de una misma
conversación y para que el administrador pueda auditar qué se respondió.
"""
import enum

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class RolMensaje(str, enum.Enum):
    usuario = "usuario"
    asistente = "asistente"
    sistema = "sistema"


RolMensajeDB = Enum(
    RolMensaje,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="rol_mensaje",
)


class Conversacion(TimestampMixin, Base):
    __tablename__ = "conversaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Identificador de sesión del navegador: permite conversar sin iniciar sesión.
    session_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    titulo: Mapped[str] = mapped_column(String(140), default="Nueva conversación", nullable=False)

    usuario: Mapped["Usuario | None"] = relationship()
    mensajes: Mapped[list["Mensaje"]] = relationship(
        back_populates="conversacion",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Mensaje.id",
    )

    def __repr__(self) -> str:
        return f"<Conversacion #{self.id}>"


class Mensaje(TimestampMixin, Base):
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversacion_id: Mapped[int] = mapped_column(
        ForeignKey("conversaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rol: Mapped[RolMensaje] = mapped_column(RolMensajeDB, nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)

    conversacion: Mapped["Conversacion"] = relationship(back_populates="mensajes")

    def __repr__(self) -> str:
        return f"<Mensaje {self.rol} #{self.id}>"
