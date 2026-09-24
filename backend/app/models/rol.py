from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    # valores esperados: administrador, empleado, cliente

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")
