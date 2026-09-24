"""Servicio de IA externa: genera una breve descripción sugerida para una obra.

Aislado en su propio servicio. Usa httpx async con timeout y un intento de
reintento controlado. Si falta la API key o el proveedor falla, degrada de
forma explícita (no inventa una respuesta como si fuera real).
"""
from __future__ import annotations

import httpx

from app.core.config import get_settings

settings = get_settings()


async def generar_descripcion_sugerida(titulo: str, tecnica: str) -> dict:
    if not settings.external_ai_api_key:
        return {
            "disponible": False,
            "detalle": "Falta configurar EXTERNAL_AI_API_KEY en .env para usar la IA externa.",
        }

    prompt = f"Escribe una frase breve y evocadora para una obra titulada '{titulo}' ({tecnica})."
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
    }
    headers = {"Authorization": f"Bearer {settings.external_ai_api_key}"}

    intentos = 2
    ultimo_error = None
    async with httpx.AsyncClient(timeout=settings.external_ai_timeout_seconds) as client:
        for _ in range(intentos):
            try:
                resp = await client.post(
                    f"{settings.external_ai_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                texto = data["choices"][0]["message"]["content"].strip()
                return {"disponible": True, "descripcion": texto}
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as exc:
                ultimo_error = str(exc)
                continue

    return {
        "disponible": False,
        "detalle": f"El proveedor externo de IA no respondió correctamente: {ultimo_error}",
    }
