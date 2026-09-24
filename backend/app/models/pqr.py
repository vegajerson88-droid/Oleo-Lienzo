"""PQR: peticiones, quejas, reclamos y sugerencias.

Pueden radicarlas clientes autenticados o visitantes desde el chatbot; por eso
`cliente_id` admite nulos y se guardan nombre y correo de contacto.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class TipoPQR(str, enum.Enum):
    peticion = "peticion"
    queja = "queja"
    reclamo = "reclamo"
    sugerencia = "sugerencia"


class EstadoPQR(str, enum.Enum):
    pendiente = "pendiente"
    en_proceso = "en_proceso"
    respondida = "respondida"
    cerrada = "cerrada"


# Una PQR cerrada es definitiva; una respondida aún puede reabrirse si el
# cliente no queda conforme.
TRANSICIONES_PQR: dict[EstadoPQR, set[EstadoPQR]] = {
    EstadoPQR.pendiente: {EstadoPQR.en_proceso, EstadoPQR.respondida, EstadoPQR.cerrada},
    EstadoPQR.en_proceso: {EstadoPQR.respondida, EstadoPQR.cerrada},
    EstadoPQR.respondida: {EstadoPQR.cerrada, EstadoPQR.en_proceso},
    EstadoPQR.cerrada: set(),
}

TipoPQRDB = Enum(
    TipoPQR,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="tipo_pqr",
)

EstadoPQRDB = Enum(
    EstadoPQR,
    native_enum=False,
    length=20,
    values_callable=lambda e: [m.value for m in e],
    name="estado_pqr",
)


class PQR(TimestampMixin, Base):
    __tablename__ = "pqr"
    __table_args__ = (Index("ix_pqr_estado_creado", "estado", "creado_en"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Número de radicado legible: PQR-000001.
    radicado: Mapped[str] = mapped_column(String(24), unique=True, index=True, nullable=False)

    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Datos de contacto para radicados anónimos hechos desde el chatbot.
    contacto_nombre: Mapped[str] = mapped_column(String(90), nullable=False)
    contacto_email: Mapped[str] = mapped_column(String(80), nullable=False)

    tipo: Mapped[TipoPQR] = mapped_column(TipoPQRDB, nullable=False)
    asunto: Mapped[str] = mapped_column(String(140), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoPQR] = mapped_column(
        EstadoPQRDB, default=EstadoPQR.pendiente, nullable=False
    )

    respuesta: Mapped[str | None] = mapped_column(Text, nullable=True)
    respondido_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    respondido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cliente: Mapped["Usuario | None"] = relationship(
        back_populates="pqrs", foreign_keys=[cliente_id], lazy="joined"
    )
    respondido_por: Mapped["Usuario | None"] = relationship(foreign_keys=[respondido_por_id])

    def __repr__(self) -> str:
        return f"<PQR {self.radicado} {self.estado}>"
