"""Roles y permisos del sistema.

Un rol agrupa permisos; un permiso es una acción concreta identificada por un
código estable (por ejemplo `ventas.crear`). La autorización definitiva la
resuelve siempre el backend a partir de estos datos.
"""
from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Tabla intermedia de la relación muchos-a-muchos roles <-> permisos.
rol_permisos = Table(
    "rol_permisos",
    Base.metadata,
    Column("rol_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permiso_id", ForeignKey("permisos.id", ondelete="CASCADE"), primary_key=True),
)


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(160), nullable=False)

    roles: Mapped[list["Rol"]] = relationship(
        secondary=rol_permisos, back_populates="permisos"
    )

    def __repr__(self) -> str:
        return f"<Permiso {self.codigo}>"


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Valores esperados: administrador, empleado, cliente.
    nombre: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String(160), nullable=True)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")
    permisos: Mapped[list[Permiso]] = relationship(
        secondary=rol_permisos, back_populates="roles", lazy="selectin"
    )

    def tiene_permiso(self, codigo: str) -> bool:
        return any(p.codigo == codigo for p in self.permisos)

    def __repr__(self) -> str:
        return f"<Rol {self.nombre}>"
