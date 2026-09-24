"""Esquemas de los dashboards y las estadísticas.

Todos los valores llegan calculados desde la base de datos: el frontend no
escribe ni un solo número a mano (requisito 15 del quinto avance).
"""

from pydantic import BaseModel, Field


class IndicadorCard(BaseModel):
    """Una tarjeta de indicador del dashboard."""

    clave: str = Field(description="Identificador estable, p. ej. `ventas_totales`.")
    etiqueta: str
    valor: float
    formato: str = Field(default="numero", description="numero | moneda | porcentaje")
    variacion: float | None = Field(
        default=None, description="Variación porcentual frente al periodo anterior."
    )


class PuntoSerie(BaseModel):
    """Un punto de una serie temporal o categórica."""

    etiqueta: str
    valor: float


class SerieGrafico(BaseModel):
    nombre: str
    tipo: str = Field(description="barras | linea")
    puntos: list[PuntoSerie]


class DashboardOut(BaseModel):
    """Respuesta del dashboard, ya adaptada al rol de quien consulta."""

    rol: str
    periodo_inicio: str | None = None
    periodo_fin: str | None = None
    indicadores: list[IndicadorCard]
    graficos: list[SerieGrafico]
