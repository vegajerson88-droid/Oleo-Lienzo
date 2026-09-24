"""Pruebas del catálogo: obras (productos) y servicios."""

import pytest

from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio

OBRA_VALIDA = {
    "titulo": "Nueva Obra",
    "artista": "Artista Nuevo",
    "anio": 2023,
    "tecnica": "Acrílico sobre lienzo",
    "precio": 250000,
    "descripcion": "Descripción de prueba suficientemente larga.",
}


# ── Lectura pública ──────────────────────────────────────────────────────
async def test_listar_obras_es_publico(client):
    """La galería del sitio funciona sin iniciar sesión."""
    assert (await client.get("/api/productos")).status_code == 200


async def test_obtener_obra_inexistente_404(client):
    assert (await client.get("/api/productos/9999")).status_code == 404


async def test_id_invalido_en_la_ruta_422(client):
    assert (await client.get("/api/productos/0")).status_code == 422


# ── Autorización ─────────────────────────────────────────────────────────
async def test_crear_obra_sin_token_401(client):
    assert (await client.post("/api/productos", json=OBRA_VALIDA)).status_code == 401


async def test_crear_obra_cliente_403(client, token_cliente):
    resp = await client.post("/api/productos", json=OBRA_VALIDA, headers=cabecera(token_cliente))
    assert resp.status_code == 403


async def test_crear_obra_empleado_201(client, token_empleado):
    resp = await client.post("/api/productos", json=OBRA_VALIDA, headers=cabecera(token_empleado))
    assert resp.status_code == 201
    assert resp.json()["titulo"] == "Nueva Obra"


async def test_eliminar_obra_solo_admin(client, obra, token_empleado, token_admin):
    assert (
        await client.delete(f"/api/productos/{obra['id']}", headers=cabecera(token_empleado))
    ).status_code == 403
    assert (
        await client.delete(f"/api/productos/{obra['id']}", headers=cabecera(token_admin))
    ).status_code == 204


# ── PUT frente a PATCH ───────────────────────────────────────────────────
async def test_put_exige_el_recurso_completo(client, obra, token_empleado):
    parcial = await client.put(
        f"/api/productos/{obra['id']}",
        json={"titulo": "Solo el titulo"},
        headers=cabecera(token_empleado),
    )
    assert parcial.status_code == 422


async def test_put_reemplaza_todos_los_campos(client, obra, token_empleado):
    resp = await client.put(
        f"/api/productos/{obra['id']}",
        json={**OBRA_VALIDA, "titulo": "Reemplazada", "stock": 2, "disponible": True},
        headers=cabecera(token_empleado),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["titulo"] == "Reemplazada"
    assert data["tecnica"] == OBRA_VALIDA["tecnica"]  # también se sustituyó
    assert data["stock"] == 2


async def test_patch_solo_toca_lo_enviado(client, obra, token_empleado):
    resp = await client.patch(
        f"/api/productos/{obra['id']}",
        json={"precio": 999000},
        headers=cabecera(token_empleado),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["precio"] == 999000
    assert data["titulo"] == obra["titulo"]  # intacto


# ── Validaciones ─────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "campo,valor",
    [
        ("anio", 1000),  # anterior al mínimo
        ("anio", 3000),  # futuro
        ("precio", 0),  # debe ser > 0
        ("precio", -5000),
        ("titulo", "X"),  # demasiado corto
        ("descripcion", "ab"),  # demasiado corta
        ("stock", -1),  # no puede ser negativo
    ],
)
async def test_validaciones_de_obra_422(client, token_empleado, campo, valor):
    resp = await client.post(
        "/api/productos", json={**OBRA_VALIDA, campo: valor}, headers=cabecera(token_empleado)
    )
    assert resp.status_code == 422


# ── Filtros y paginación ─────────────────────────────────────────────────
async def test_filtros_y_paginacion(client, token_empleado):
    for titulo, artista, precio in [
        ("Amanecer", "Marina", 100000),
        ("Ocaso", "Marina", 500000),
        ("Otra", "Iván", 900000),
    ]:
        await client.post(
            "/api/productos",
            json={**OBRA_VALIDA, "titulo": titulo, "artista": artista, "precio": precio},
            headers=cabecera(token_empleado),
        )

    por_artista = await client.get("/api/productos?artista=Marina&page=1&page_size=1")
    assert por_artista.json()["total"] == 2
    assert len(por_artista.json()["items"]) == 1

    por_precio = await client.get("/api/productos?precio_min=400000&precio_max=600000")
    assert por_precio.json()["total"] == 1

    por_texto = await client.get("/api/productos?buscar=Amanecer")
    assert por_texto.json()["total"] == 1


# ── Servicios ────────────────────────────────────────────────────────────
SERVICIO_VALIDO = {
    "nombre": "Servicio Nuevo",
    "descripcion": "Descripción de prueba suficientemente larga.",
    "precio": 75000,
}


async def test_crear_servicio_nombre_duplicado_409(client, token_empleado):
    primero = await client.post(
        "/api/servicios", json=SERVICIO_VALIDO, headers=cabecera(token_empleado)
    )
    assert primero.status_code == 201
    segundo = await client.post(
        "/api/servicios", json=SERVICIO_VALIDO, headers=cabecera(token_empleado)
    )
    assert segundo.status_code == 409


async def test_servicio_put_y_patch(client, servicio, token_empleado):
    assert (
        await client.put(
            f"/api/servicios/{servicio['id']}",
            json={"nombre": "Incompleto"},
            headers=cabecera(token_empleado),
        )
    ).status_code == 422

    completo = await client.put(
        f"/api/servicios/{servicio['id']}",
        json={**SERVICIO_VALIDO, "nombre": "Servicio Reemplazado", "activo": False},
        headers=cabecera(token_empleado),
    )
    assert completo.status_code == 200 and completo.json()["activo"] is False

    parcial = await client.patch(
        f"/api/servicios/{servicio['id']}",
        json={"precio": 123000},
        headers=cabecera(token_empleado),
    )
    assert parcial.json()["precio"] == 123000
    assert parcial.json()["nombre"] == "Servicio Reemplazado"
