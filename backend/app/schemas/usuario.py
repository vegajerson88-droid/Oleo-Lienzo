"""Esquemas de usuarios, roles, permisos y autenticación.

Las mismas reglas que valida el formulario de React se revalidan aquí: el
frontend puede saltarse, el backend no.
"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]{2,40}$")
SOLO_NUMEROS = re.compile(r"^\d+$")
PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$")
TIPOS_DOCUMENTO = {"CC", "CE", "TI", "PA"}

MENSAJE_PASSWORD = "Mínimo 8 caracteres, con mayúscula, minúscula y número."


class UsuarioBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=40, description="Nombres del usuario.")
    apellido: str = Field(min_length=2, max_length=40, description="Apellidos del usuario.")
    tipo_documento: str = Field(description="Uno de: CC, CE, TI, PA.")
    numero_documento: str = Field(min_length=6, max_length=15, description="Solo dígitos.")
    direccion: str = Field(min_length=5, max_length=100)
    telefono: str = Field(min_length=7, max_length=10, description="Solo dígitos.")
    email: EmailStr

    @field_validator("nombre", "apellido")
    @classmethod
    def validar_solo_letras(cls, v: str) -> str:
        v = v.strip()
        if not SOLO_LETRAS.match(v):
            raise ValueError("Solo se permiten letras y espacios (2 a 40 caracteres).")
        return v

    @field_validator("tipo_documento")
    @classmethod
    def validar_tipo_documento(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in TIPOS_DOCUMENTO:
            raise ValueError(f"tipo_documento debe ser uno de {sorted(TIPOS_DOCUMENTO)}.")
        return v

    @field_validator("numero_documento", "telefono")
    @classmethod
    def validar_solo_numeros(cls, v: str) -> str:
        v = v.strip()
        if not SOLO_NUMEROS.match(v):
            raise ValueError("Solo se permiten dígitos numéricos.")
        return v

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioCreate(UsuarioBase):
    """Registro público de un cliente desde el formulario del sitio."""

    password: str = Field(min_length=8, max_length=64)
    confirmar_password: str

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError(MENSAJE_PASSWORD)
        return v

    @model_validator(mode="after")
    def validar_confirmacion(self) -> "UsuarioCreate":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden.")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Sara",
                "apellido": "Pérez",
                "tipo_documento": "CC",
                "numero_documento": "1098765432",
                "direccion": "Calle 45 # 12-30",
                "telefono": "3009876543",
                "email": "sara.perez@ejemplo.com",
                "password": "Cliente123",
                "confirmar_password": "Cliente123",
            }
        }
    )


class UsuarioAdminCreate(UsuarioCreate):
    """Alta de usuario desde el panel: permite elegir el rol."""

    rol_nombre: str = Field(default="cliente", description="administrador, empleado o cliente.")


class UsuarioUpdate(BaseModel):
    """Actualización PARCIAL (PATCH): todos los campos son opcionales."""

    nombre: str | None = Field(default=None, min_length=2, max_length=40)
    apellido: str | None = Field(default=None, min_length=2, max_length=40)
    direccion: str | None = Field(default=None, min_length=5, max_length=100)
    telefono: str | None = Field(default=None, min_length=7, max_length=10)
    rol_id: int | None = Field(default=None, ge=1)
    activo: bool | None = None

    @field_validator("nombre", "apellido")
    @classmethod
    def validar_solo_letras(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not SOLO_LETRAS.match(v):
            raise ValueError("Solo se permiten letras y espacios (2 a 40 caracteres).")
        return v

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not SOLO_NUMEROS.match(v.strip()):
            raise ValueError("Solo se permiten dígitos numéricos.")
        return v.strip()


class UsuarioReplace(BaseModel):
    """Reemplazo COMPLETO (PUT): todos los campos son obligatorios.

    A diferencia de PATCH, aquí el cliente envía el recurso entero y lo que
    omita se considera un error de validación, no un "déjalo como está".
    """

    nombre: str = Field(min_length=2, max_length=40)
    apellido: str = Field(min_length=2, max_length=40)
    direccion: str = Field(min_length=5, max_length=100)
    telefono: str = Field(min_length=7, max_length=10)
    rol_id: int = Field(ge=1)
    activo: bool

    _val_letras = field_validator("nombre", "apellido")(UsuarioBase.validar_solo_letras.__func__)
    _val_numeros = field_validator("telefono")(UsuarioBase.validar_solo_numeros.__func__)


class UsuarioEstadoUpdate(BaseModel):
    """Cambio de estado activo/inactivo (PATCH /usuarios/{id}/estado)."""

    activo: bool = Field(description="true = activo, false = inactivo.")

    model_config = ConfigDict(json_schema_extra={"example": {"activo": False}})


class PermisoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    descripcion: str


class RolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    descripcion: str | None = None
    permisos: list[PermisoOut] = []


class UsuarioOut(BaseModel):
    """Representación pública de un usuario. Nunca incluye el hash."""

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


class UsuarioResumen(BaseModel):
    """Versión ligera para incrustar en ventas, facturas y PQR."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    apellido: str
    email: EmailStr


# ── Autenticación ────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=64)

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "admin@oleoylienzo.com", "password": "Admin1234"}}
    )


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Segundos de validez del token.")
    usuario: UsuarioOut


class RecuperarPasswordRequest(BaseModel):
    email: EmailStr

    model_config = ConfigDict(json_schema_extra={"example": {"email": "sara.perez@ejemplo.com"}})


class RestablecerPasswordRequest(BaseModel):
    token: str = Field(description="Token recibido por correo.")
    password: str = Field(min_length=8, max_length=64)
    confirmar_password: str

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError(MENSAJE_PASSWORD)
        return v

    @model_validator(mode="after")
    def validar_confirmacion(self) -> "RestablecerPasswordRequest":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class CambiarPasswordRequest(BaseModel):
    """Cambio de contraseña con la sesión ya iniciada."""

    password_actual: str = Field(min_length=1, max_length=64)
    password_nueva: str = Field(min_length=8, max_length=64)

    @field_validator("password_nueva")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError(MENSAJE_PASSWORD)
        return v
