import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÁáéíóúñÑ\s]{2,40}$")
SOLO_NUMEROS = re.compile(r"^\d+$")
PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$")
TIPOS_DOCUMENTO = {"CC", "CE", "TI", "PA"}


class UsuarioBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=40)
    apellido: str = Field(min_length=2, max_length=40)
    tipo_documento: str
    numero_documento: str = Field(min_length=6, max_length=15)
    direccion: str = Field(min_length=5, max_length=100)
    telefono: str = Field(min_length=7, max_length=10)
    email: EmailStr

    @field_validator("nombre", "apellido")
    @classmethod
    def validar_solo_letras(cls, v: str) -> str:
        if not SOLO_LETRAS.match(v):
            raise ValueError("Solo se permiten letras y espacios (2 a 40 caracteres).")
        return v

    @field_validator("tipo_documento")
    @classmethod
    def validar_tipo_documento(cls, v: str) -> str:
        if v not in TIPOS_DOCUMENTO:
            raise ValueError(f"tipo_documento debe ser uno de {sorted(TIPOS_DOCUMENTO)}")
        return v

    @field_validator("numero_documento", "telefono")
    @classmethod
    def validar_solo_numeros(cls, v: str) -> str:
        if not SOLO_NUMEROS.match(v):
            raise ValueError("Solo se permiten dígitos numéricos.")
        return v


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=8, max_length=64)
    confirmar_password: str

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError("Mínimo 8 caracteres, con mayúscula, minúscula y número.")
        return v

    @model_validator(mode="after")
    def validar_confirmacion(self) -> "UsuarioCreate":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=40)
    apellido: str | None = Field(default=None, min_length=2, max_length=40)
    direccion: str | None = Field(default=None, min_length=5, max_length=100)
    telefono: str | None = Field(default=None, min_length=7, max_length=10)
    rol_id: int | None = None
    activo: bool | None = None


class RolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    apellido: str
    tipo_documento: str
    numero_documento: str
    direccion: str
    telefono: str
    email: EmailStr
    activo: bool
    creado_en: datetime
    rol: RolOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
