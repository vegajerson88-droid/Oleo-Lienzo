import pytest

pytestmark = pytest.mark.asyncio


async def _crear_obra_y_pedido(client, token_empleado, token_cliente):
    obra_resp = await client.post("/productos", json={
        "titulo": "Obra Pedido", "artista": "Artista", "anio": 2021,
        "tecnica": "Óleo sobre lienzo", "precio": 200000,
        "descripcion": "Descripción de prueba suficientemente larga.",
    }, headers={"Authorization": f"Bearer {token_empleado}"})
    obra_id = obra_resp.json()["id"]

    pedido_resp = await client.post("/pedidos", json={
        "detalles": [{"obra_id": obra_id, "cantidad": 2}]
    }, headers={"Authorization": f"Bearer {token_cliente}"})
    return pedido_resp


async def test_crear_pedido_calcula_total(client, token_empleado, token_cliente):
    resp = await _crear_obra_y_pedido(client, token_empleado, token_cliente)
    assert resp.status_code == 201
    data = resp.json()
    assert data["estado"] == "pendiente"
    assert data["total"] == 400000.0


async def test_solo_cliente_crea_pedido_403(client, token_empleado):
    resp = await client.post("/pedidos", json={"detalles": [{"obra_id": 1, "cantidad": 1}]},
                              headers={"Authorization": f"Bearer {token_empleado}"})
    assert resp.status_code == 403


async def test_transicion_invalida_422(client, token_empleado, token_cliente, token_admin):
    pedido = (await _crear_obra_y_pedido(client, token_empleado, token_cliente)).json()
    resp = await client.patch(f"/pedidos/{pedido['id']}/estado", json={"nuevo_estado": "entregado"},
                               headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 422


async def test_transicion_valida_pendiente_a_confirmado(client, token_empleado, token_cliente, token_admin):
    pedido = (await _crear_obra_y_pedido(client, token_empleado, token_cliente)).json()
    resp = await client.patch(f"/pedidos/{pedido['id']}/estado", json={"nuevo_estado": "confirmado"},
                               headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200
    assert resp.json()["estado"] == "confirmado"


async def test_transicion_completa_hasta_entregado(client, token_empleado, token_cliente, token_admin):
    pedido = (await _crear_obra_y_pedido(client, token_empleado, token_cliente)).json()
    headers = {"Authorization": f"Bearer {token_admin}"}
    r1 = await client.patch(f"/pedidos/{pedido['id']}/estado", json={"nuevo_estado": "confirmado"}, headers=headers)
    assert r1.status_code == 200
    r2 = await client.patch(f"/pedidos/{pedido['id']}/estado", json={"nuevo_estado": "entregado"}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["estado"] == "entregado"

    # ya entregado: no hay transiciones válidas posteriores
    r3 = await client.patch(f"/pedidos/{pedido['id']}/estado", json={"nuevo_estado": "cancelado"}, headers=headers)
    assert r3.status_code == 422


async def test_cliente_no_ve_pedido_de_otro_403(client, token_empleado, token_cliente):
    pedido = (await _crear_obra_y_pedido(client, token_empleado, token_cliente)).json()

    otro_registro = await client.post("/auth/registro", json={
        "nombre": "Otro", "apellido": "Cliente", "tipo_documento": "CC", "numero_documento": "55555555",
        "direccion": "Calle X", "telefono": "3005555555", "email": "otro@test.com",
        "password": "Clave1234", "confirmar_password": "Clave1234",
    })
    assert otro_registro.status_code == 201
    login_otro = await client.post("/auth/login", json={"email": "otro@test.com", "password": "Clave1234"})
    token_otro = login_otro.json()["access_token"]

    resp = await client.get(f"/pedidos/{pedido['id']}", headers={"Authorization": f"Bearer {token_otro}"})
    assert resp.status_code == 403
