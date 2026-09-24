"""Usuarios del sistema (administradores, empleados y clientes)."""

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        # Consulta habitual del panel administrativo: filtrar por rol y estado.
        Index("ix_usuarios_rol_activo", "rol_id", "activo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    apellido: Mapped[str] = mapped_column(String(40), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(5), nullable=False)
    numero_documento: Mapped[str] = mapped_column(
        String(15), unique=True, index=True, nullable=False
    )
    direccion: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[str] = mapped_column(String(10), nullable=False)
    email: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    # Nunca se almacena la contraseña en claro: solo su hash bcrypt.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    rol: Mapped["Rol"] = relationship(back_populates="usuarios", lazy="joined")

    pedidos: Mapped[list["Pedido"]] = relationship(
        back_populates="cliente", foreign_keys="Pedido.cliente_id"
    )
    ventas: Mapped[list["Venta"]] = relationship(
        back_populates="cliente", foreign_keys="Venta.cliente_id"
    )
    pqrs: Mapped[list["PQR"]] = relationship(
        back_populates="cliente", foreign_keys="PQR.cliente_id"
    )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def tiene_permiso(self, codigo: str) -> bool:
        """Autorización granular: delega en los permisos del rol."""
        return bool(self.rol and self.rol.tiene_permiso(codigo))

    def __repr__(self) -> str:
        return f"<Usuario {self.email}>"
