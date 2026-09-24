"""Pruebas de registro, inicio de sesión y gestión de la contraseña."""
import pytest

from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio

REGISTRO_VALIDO = {
    "nombre": "Nuevo", "apellido": "Usuario", "tipo_documento": "CC",
    "numero_documento": "99999999", "direccion": "Calle Falsa 123",
    "telefono": "3009999999", "email": "nuevo@test.com",
    "password": "Clave1234", "confirmar_password": "Clave1234",
}


async def test_registro_exitoso_asigna_rol_cliente(client):
    resp = await client.post("/api/auth/registro", json=REGISTRO_VALIDO)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "nuevo@test.com"
    assert data["rol"]["nombre"] == "cliente"
    # La respuesta nunca debe exponer la contraseña ni su hash.
    assert "password" not in data and "password_hash" not in data


async def test_registro_email_duplicado_409(client):
    assert (await client.post("/api/auth/registro", json=REGISTRO_VALIDO)).status_code == 201
    otro = {**REGISTRO_VALIDO, "numero_documento": "88888888"}
    assert (await client.post("/api/auth/registro", json=otro)).status_code == 409


async def test_registro_documento_duplicado_409(client):
    assert (await client.post("/api/auth/registro", json=REGISTRO_VALIDO)).status_code == 201
    otro = {**REGISTRO_VALIDO, "email": "distinto@test.com"}
    assert (await client.post("/api/auth/registro", json=otro)).status_code == 409


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("password", "123"),                 # no cumple la política
        ("confirmar_password", "Otra1234"),  # no coincide
        ("email", "no-es-un-email"),
        ("telefono", "abc1234"),             # solo dígitos
        ("numero_documento", "12"),          # demasiado corto
        ("nombre", "Juan123"),               # solo letras
        ("tipo_documento", "XX"),            # fuera del catálogo
    ],
)
async def test_registro_validaciones_422(client, campo, valor):
    assert (
        await client.post("/api/auth/registro", json={**REGISTRO_VALIDO, campo: valor})
    ).status_code == 422


async def test_registro_normaliza_email_a_minusculas(client):
    resp = await client.post(
        "/api/auth/registro", json={**REGISTRO_VALIDO, "email": "MAYUSCULAS@Test.COM"}
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "mayusculas@test.com"


async def test_login_correcto_devuelve_jwt_y_usuario(client):
    resp = await client.post(
        "/api/auth/login", json={"email": "cliente@test.com", "password": "Cliente123"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert len(data["access_token"].split(".")) == 3  # cabecera.payload.firma
    assert data["usuario"]["email"] == "cliente@test.com"


async def test_login_password_incorrecto_401(client):
    resp = await client.post(
        "/api/auth/login", json={"email": "cliente@test.com", "password": "incorrecta"}
    )
    assert resp.status_code == 401


async def test_login_email_inexistente_da_el_mismo_error(client):
    """No debe poder deducirse qué correos están registrados."""
    inexistente = await client.post(
        "/api/auth/login", json={"email": "nadie@test.com", "password": "Cualquiera1"}
    )
    existente = await client.post(
        "/api/auth/login", json={"email": "cliente@test.com", "password": "incorrecta"}
    )
    assert inexistente.status_code == existente.status_code == 401
    assert inexistente.json()["detail"] == existente.json()["detail"]


async def test_login_usuario_inactivo_403(client, token_admin, id_cliente):
    await client.patch(
        f"/api/usuarios/{id_cliente}/estado", json={"activo": False},
        headers=cabecera(token_admin),
    )
    resp = await client.post(
        "/api/auth/login", json={"email": "cliente@test.com", "password": "Cliente123"}
    )
    assert resp.status_code == 403


async def test_me_sin_token_401(client):
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_me_con_token_invalido_401(client):
    resp = await client.get("/api/auth/me", headers=cabecera("token.claramente.falso"))
    assert resp.status_code == 401


async def test_me_devuelve_rol_y_permisos(client, token_admin):
    resp = await client.get("/api/auth/me", headers=cabecera(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@test.com"
    assert data["rol"]["nombre"] == "administrador"
    assert len(data["rol"]["permisos"]) > 0


async def test_token_oauth2_para_swagger(client):
    """El botón Authorize de Swagger usa el flujo OAuth2 con formulario."""
    resp = await client.post(
        "/api/auth/token",
        data={"username": "admin@test.com", "password": "Admin1234"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_cambiar_password_requiere_la_actual(client, token_cliente):
    resp = await client.post(
        "/api/auth/cambiar-password",
        json={"password_actual": "EstaNoEs1", "password_nueva": "NuevaClave1"},
        headers=cabecera(token_cliente),
    )
    assert resp.status_code == 401


async def test_cambiar_password_y_entrar_con_la_nueva(client, token_cliente):
    resp = await client.post(
        "/api/auth/cambiar-password",
        json={"password_actual": "Cliente123", "password_nueva": "NuevaClave1"},
        headers=cabecera(token_cliente),
    )
    assert resp.status_code == 200

    antigua = await client.post(
        "/api/auth/login", json={"email": "cliente@test.com", "password": "Cliente123"}
    )
    assert antigua.status_code == 401
    nueva = await client.post(
        "/api/auth/login", json={"email": "cliente@test.com", "password": "NuevaClave1"}
    )
    assert nueva.status_code == 200


async def test_recuperar_password_no_revela_si_el_correo_existe(client):
    registrado = await client.post(
        "/api/auth/recuperar-password", json={"email": "cliente@test.com"}
    )
    desconocido = await client.post(
        "/api/auth/recuperar-password", json={"email": "nadie@test.com"}
    )
    assert registrado.status_code == desconocido.status_code == 200
    assert registrado.json() == desconocido.json()


async def test_restablecer_con_token_invalido_400(client):
    resp = await client.post(
        "/api/auth/restablecer-password",
        json={"token": "esto.no.es.un.token", "password": "NuevaClave1",
              "confirmar_password": "NuevaClave1"},
    )
    assert resp.status_code == 400


async def test_restablecer_con_token_valido(client):
    from app.core.security import create_reset_token

    token = create_reset_token("cliente@test.com")
    resp = await client.post(
        "/api/auth/restablecer-password",
        json={"token": token, "password": "Restablecida1",
              "confirmar_password": "Restablecida1"},
    )
    assert resp.status_code == 200
    login = await client.post(
        "/api/auth/login", json={"email": "cliente@test.com", "password": "Restablecida1"}
    )
    assert login.status_code == 200


async def test_token_de_reset_no_sirve_para_autenticarse(client):
    """Un enlace de recuperación no puede dar acceso a la API."""
    from app.core.security import create_reset_token

    resp = await client.get(
        "/api/auth/me", headers=cabecera(create_reset_token("admin@test.com"))
    )
    assert resp.status_code == 401


async def test_token_expirado_401(client):
    from app.core.security import create_access_token

    expirado = create_access_token("admin@test.com", "administrador", expires_minutes=-1)
    assert (await client.get("/api/auth/me", headers=cabecera(expirado))).status_code == 401
