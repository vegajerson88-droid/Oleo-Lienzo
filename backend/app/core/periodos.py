"""Periodos de los reportes de ventas.

El reporte nació cubriendo un solo día. Para que pueda cubrir también los
últimos quince días o el mes en curso sin que cada capa calcule las fechas por
su cuenta, el rango se representa con un objeto único que viaja del router al
generador de PDF y de Excel.
"""

import enum
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


class TipoPeriodo(str, enum.Enum):
    dia = "dia"
    quincena = "quincena"
    mes = "mes"
    personalizado = "personalizado"


# Cuántos días cubre cada periodo predefinido, contando el día de hoy.
DIAS_QUINCENA = 15


@dataclass(frozen=True)
class Periodo:
    """Rango de fechas de un reporte, con su nombre para los documentos."""

    desde: date
    hasta: date
    tipo: TipoPeriodo

    @property
    def es_un_solo_dia(self) -> bool:
        return self.desde == self.hasta

    @property
    def titulo(self) -> str:
        """Encabezado del documento: «Reporte diario», «de los últimos 15 días»…"""
        return {
            TipoPeriodo.dia: "Reporte diario de ventas",
            TipoPeriodo.quincena: "Reporte de ventas · últimos 15 días",
            TipoPeriodo.mes: "Reporte de ventas del mes",
            TipoPeriodo.personalizado: "Reporte de ventas por rango",
        }[self.tipo]

    @property
    def descripcion(self) -> str:
        """Cómo se lee el rango dentro del documento."""
        if self.es_un_solo_dia:
            return f"Ventas del {self.desde.strftime('%d/%m/%Y')}"
        return (
            f"Ventas del {self.desde.strftime('%d/%m/%Y')} "
            f"al {self.hasta.strftime('%d/%m/%Y')}"
        )

    @property
    def sufijo_archivo(self) -> str:
        """Parte variable del nombre del archivo descargado."""
        if self.es_un_solo_dia:
            return self.desde.isoformat()
        return f"{self.desde.isoformat()}_a_{self.hasta.isoformat()}"


def hoy() -> date:
    return datetime.now(timezone.utc).date()


def construir(
    tipo: TipoPeriodo,
    dia: date | None = None,
    desde: date | None = None,
    hasta: date | None = None,
) -> Periodo:
    """Resuelve el rango de fechas a partir del tipo pedido.

    Lanza `ValueError` si el rango personalizado está incompleto o invertido;
    el router lo traduce a un 422.
    """
    referencia = dia or hoy()

    if tipo is TipoPeriodo.dia:
        return Periodo(desde=referencia, hasta=referencia, tipo=tipo)

    if tipo is TipoPeriodo.quincena:
        # Quince días contando hoy: del día 14 hacia atrás hasta hoy.
        return Periodo(
            desde=referencia - timedelta(days=DIAS_QUINCENA - 1),
            hasta=referencia,
            tipo=tipo,
        )

    if tipo is TipoPeriodo.mes:
        # Del día 1 del mes de la fecha de referencia hasta esa fecha.
        return Periodo(desde=referencia.replace(day=1), hasta=referencia, tipo=tipo)

    # Personalizado
    if desde is None or hasta is None:
        raise ValueError("Un periodo personalizado necesita `desde` y `hasta`.")
    if desde > hasta:
        raise ValueError("`desde` no puede ser posterior a `hasta`.")
    return Periodo(desde=desde, hasta=hasta, tipo=tipo)
