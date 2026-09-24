"""Utilidades compartidas por los modelos ORM."""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def ahora_utc() -> datetime:
    """Instante actual en UTC, siempre con zona horaria explícita."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Añade `creado_en` y `actualizado_en` gestionados por el ORM."""

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=ahora_utc, nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=ahora_utc, onupdate=ahora_utc, nullable=False
    )
