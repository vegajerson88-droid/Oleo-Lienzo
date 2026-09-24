"""IA externa: redacta una descripción sugerida para una obra del catálogo.

Comparte proveedor con el chatbot (Groq) para no multiplicar credenciales.
Si la clave falta o el proveedor falla, degrada de forma explícita: informa de
que no está disponible en lugar de devolver un texto inventado como si fuera
una respuesta real del modelo.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("oleo_lienzo.ia")

INTENTOS = 2


async def generar_descripcion_sugerida(titulo: str, tecnica: str) -> dict:
    if not settings.groq_configurado:
        return {
            "disponible": False,
            "detalle": "Falta configurar GROQ_API_KEY en .env para usar la IA externa.",
        }

    prompt = (
        f"Escribe una sola frase evocadora, de máximo 25 palabras y en español, "
        f"para describir en el catálogo de una galería la obra «{titulo}» "
        f"({tecnica}). Responde únicamente con la frase, sin comillas."
    )
    payload = {
        "model": settings.groq_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.8,
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}

    ultimo_error = None
    async with httpx.AsyncClient(timeout=settings.groq_timeout_seconds) as cliente:
        for intento in range(INTENTOS):
            try:
                respuesta = await cliente.post(
                    f"{settings.groq_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                respuesta.raise_for_status()
                texto = respuesta.json()["choices"][0]["message"]["content"].strip()
                return {
                    "disponible": True,
                    "descripcion": texto.strip('"'),
                    "modelo": settings.groq_model,
                }
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
                ultimo_error = f"{type(exc).__name__}: {exc}"
                logger.info("Intento %d de IA externa fallido: %s", intento + 1, ultimo_error)

    return {
        "disponible": False,
        "detalle": f"El proveedor externo de IA no respondió correctamente. {ultimo_error}",
    }
