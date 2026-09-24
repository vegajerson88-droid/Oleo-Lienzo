import pytest

pytestmark = pytest.mark.asyncio


async def _crear_obra(client, token, titulo="Obra Test", artista="Artista Test"):
    resp = await client.post("/productos", json={
        "titulo": titulo, "artista": artista, "anio": 2022,
        "tecnica": "Óleo sobre lienzo", "precio": 100000,
        "descripcion": "Descripción de prueba suficientemente larga.",
    }, headers={"Authorization": f"Bearer {token}"})
    return resp


async def test_crear_obra_sin_autenticacion_401(client):
    resp = await client.post("/productos", json={
        "titulo": "X", "artista": "Y", "anio": 2020, "tecnica": "Óleo",
        "precio": 1000, "descripcion": "Descripción válida.",
    })
    assert resp.status_code == 401


async def test_crear_obra_cliente_403(client, token_cliente):
    resp = await _crear_obra(client, token_cliente)
    assert resp.status_code == 403


async def test_crear_obra_empleado_201(client, token_empleado):
    resp = await _crear_obra(client, token_empleado)
    assert resp.status_code == 201
    assert resp.json()["titulo"] == "Obra Test"


async def test_obtener_obra_404(client):
    resp = await client.get("/productos/999")
    assert resp.status_code == 404


async def test_listar_obras_filtro_y_paginacion(client, token_empleado):
    await _crear_obra(client, token_empleado, titulo="Amanecer", artista="Marina")
    await _crear_obra(client, token_empleado, titulo="Ocaso", artista="Marina")
    await _crear_obra(client, token_empleado, titulo="Otra", artista="Iván")

    resp = await client.get("/productos", params={"artista": "Marina", "page": 1, "page_size": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 1


async def test_eliminar_obra_solo_admin(client, token_empleado, token_admin):
    creada = await _crear_obra(client, token_empleado)
    obra_id = creada.json()["id"]

    resp_empleado = await client.delete(f"/productos/{obra_id}", headers={"Authorization": f"Bearer {token_empleado}"})
    assert resp_empleado.status_code == 403

    resp_admin = await client.delete(f"/productos/{obra_id}", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp_admin.status_code == 204


async def test_validacion_anio_422(client, token_empleado):
    resp = await client.post("/productos", json={
        "titulo": "Obra", "artista": "Artista", "anio": 1000, "tecnica": "Óleo",
        "precio": 1000, "descripcion": "Descripción válida.",
    }, headers={"Authorization": f"Bearer {token_empleado}"})
    assert resp.status_code == 422
