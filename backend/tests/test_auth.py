import pytest

pytestmark = pytest.mark.asyncio


async def test_registro_exitoso(client):
    resp = await client.post("/auth/registro", json={
        "nombre": "Nuevo", "apellido": "Usuario", "tipo_documento": "CC",
        "numero_documento": "99999999", "direccion": "Calle Falsa 123",
        "telefono": "3009999999", "email": "nuevo@test.com",
        "password": "Clave1234", "confirmar_password": "Clave1234",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "nuevo@test.com"
    assert data["rol"]["nombre"] == "cliente"


async def test_registro_email_duplicado_409(client):
    payload = {
        "nombre": "Ana", "apellido": "Ba", "tipo_documento": "CC", "numero_documento": "11111111",
        "direccion": "Calle 1234", "telefono": "3001111111", "email": "dup@test.com",
        "password": "Clave1234", "confirmar_password": "Clave1234",
    }
    r1 = await client.post("/auth/registro", json=payload)
    assert r1.status_code == 201
    payload["numero_documento"] = "22222222"
    r2 = await client.post("/auth/registro", json=payload)
    assert r2.status_code == 409


async def test_registro_password_invalido_422(client):
    resp = await client.post("/auth/registro", json={
        "nombre": "A", "apellido": "B", "tipo_documento": "CC", "numero_documento": "33333333",
        "direccion": "Calle 1", "telefono": "3001111111", "email": "malo@test.com",
        "password": "123", "confirmar_password": "123",
    })
    assert resp.status_code == 422


async def test_login_correcto(client):
    resp = await client.post("/auth/login", json={"email": "cliente@test.com", "password": "Cliente123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["usuario"]["email"] == "cliente@test.com"


async def test_login_password_incorrecto_401(client):
    resp = await client.post("/auth/login", json={"email": "cliente@test.com", "password": "incorrecta"})
    assert resp.status_code == 401


async def test_me_sin_token_401(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_con_token(client, token_cliente):
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token_cliente}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "cliente@test.com"
