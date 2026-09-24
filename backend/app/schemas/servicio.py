from pydantic import BaseModel, ConfigDict, Field


class ServicioBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str = Field(min_length=5)
    precio: float = Field(gt=0)
    activo: bool = True


class ServicioCreate(ServicioBase):
    pass


class ServicioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, min_length=5)
    precio: float | None = Field(default=None, gt=0)
    activo: bool | None = None


class ServicioOut(ServicioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
