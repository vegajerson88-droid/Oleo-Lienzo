"""Esquemas del chatbot con Inteligencia Artificial."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import RolMensaje


class MensajeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rol: RolMensaje
    contenido: str
    creado_en: datetime


class ChatRequest(BaseModel):
    mensaje: str = Field(min_length=1, max_length=1000)
    session_id: str = Field(
        min_length=8,
        max_length=64,
        description="Identificador de la conversación en el navegador.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mensaje": "¿Qué obras de Marina Solórzano tienen disponibles?",
                "session_id": "4f9a1c2e-7b3d-4a56-9e01-2c8d5f6a7b90",
            }
        }
    )


class ChatResponse(BaseModel):
    respuesta: str
    conversacion_id: int
    # `false` cuando Groq no está configurado o falló y respondió el modo local.
    generado_por_ia: bool
    modelo: str | None = None
    detalle: str | None = Field(default=None, description="Motivo de la degradación, si la hubo.")


class ConversacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: str
    usuario_id: int | None = None
    titulo: str
    creado_en: datetime
    mensajes: list[MensajeOut] = []
