from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

ANIO_MIN = 1400


class ObraBase(BaseModel):
    titulo: str = Field(min_length=2, max_length=120)
    artista: str = Field(min_length=2, max_length=80)
    anio: int
    tecnica: str = Field(min_length=2, max_length=80)
    precio: float = Field(gt=0)
    descripcion: str = Field(min_length=5)
    imagen_url: str | None = None
    disponible: bool = True

    @field_validator("anio")
    @classmethod
    def validar_anio(cls, v: int) -> int:
        anio_actual = date.today().year
        if v < ANIO_MIN or v > anio_actual:
            raise ValueError(f"anio debe estar entre {ANIO_MIN} y {anio_actual}.")
        return v


class ObraCreate(ObraBase):
    pass


class ObraUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=2, max_length=120)
    artista: str | None = Field(default=None, min_length=2, max_length=80)
    anio: int | None = None
    tecnica: str | None = Field(default=None, min_length=2, max_length=80)
    precio: float | None = Field(default=None, gt=0)
    descripcion: str | None = Field(default=None, min_length=5)
    imagen_url: str | None = None
    disponible: bool | None = None


class ObraOut(ObraBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
