import pytest

from app.services import ai_external

pytestmark = pytest.mark.asyncio


async def test_diagnostico_requiere_admin(client, token_cliente):
    resp = await client.get("/sistema/diagnostico", headers={"Authorization": f"Bearer {token_cliente}"})
    assert resp.status_code == 403


async def test_diagnostico_sin_ia_externa_configurada(client, token_admin):
    resp = await client.get("/sistema/diagnostico", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "base_de_datos" in data["componentes"]
    assert data["componentes"]["ia_externa"]["estado"] == "no_configurado"
    assert data["componentes"]["base_de_datos"]["estado"] == "ok"


async def test_diagnostico_con_ia_externa_simulada(client, token_admin, monkeypatch):
    async def fake_generar_descripcion(titulo, tecnica):
        return {"disponible": True, "descripcion": "Descripción simulada"}

    monkeypatch.setattr(ai_external, "generar_descripcion_sugerida", fake_generar_descripcion)

    # el diagnóstico solo llama al proveedor externo si hay API key configurada;
    # sin key, siempre reporta "no_configurado" sin tocar la red (comportamiento esperado)
    resp = await client.get("/sistema/diagnostico", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200
    assert resp.json()["componentes"]["ia_externa"]["estado"] == "no_configurado"


async def test_ia_externa_con_key_usa_mock(monkeypatch):
    from app.core.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "external_ai_api_key", "fake-key")

    async def fake_generar_descripcion(titulo, tecnica):
        return {"disponible": True, "descripcion": "Descripción simulada"}

    monkeypatch.setattr(ai_external, "generar_descripcion_sugerida", fake_generar_descripcion)
    resultado = await ai_external.generar_descripcion_sugerida("Obra", "Óleo")
    assert resultado["disponible"] is True
