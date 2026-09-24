"""Pruebas de los mecanismos de seguridad transversales."""
import pytest

from app.core.limiter import limiter
from app.core.security import hash_password, verify_password
from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio


async def test_el_limitador_corta_los_intentos_de_fuerza_bruta(client):
    """Reactiva el limitador (la suite lo desactiva) y comprueba el 429."""
    limiter.enabled = True
    limiter.reset()
    try:
        codigos = []
        for _ in range(25):
            resp = await client.post(
                "/api/auth/login",
                json={"email": "admin@test.com", "password": "contrasena-incorrecta"},
            )
            codigos.append(resp.status_code)
        assert 401 in codigos, "los primeros intentos deben rechazarse por credenciales"
        assert 429 in codigos, "a partir del límite debe responder 429"
    finally:
        limiter.enabled = False
        limiter.reset()


async def test_las_contrasenas_se_guardan_con_bcrypt_y_sal():
    hash_1 = hash_password("MismaClave1")
    hash_2 = hash_password("MismaClave1")
    assert hash_1.startswith("$2b$")           # identificador de bcrypt
    assert hash_1 != hash_2                    # cada hash lleva su propia sal
    assert "MismaClave1" not in hash_1         # la contraseña no es recuperable
    assert verify_password("MismaClave1", hash_1)
    assert not verify_password("OtraClave1", hash_1)


async def test_verificar_contra_un_hash_corrupto_no_revienta():
    assert verify_password("cualquiera", "esto-no-es-un-hash") is False


async def test_las_cabeceras_de_seguridad_viajan_en_la_respuesta(client):
    resp = await client.get("/api/productos")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "no-referrer"


async def test_los_errores_comparten_un_formato_uniforme(client, token_admin):
    no_encontrado = await client.get("/api/usuarios/9999", headers=cabecera(token_admin))
    assert no_encontrado.status_code == 404
    assert "detail" in no_encontrado.json()

    validacion = await client.post(
        "/api/auth/registro", json={"nombre": "X"}
    )
    assert validacion.status_code == 422
    cuerpo = validacion.json()
    assert cuerpo["error"] == "ValidationError"
    assert isinstance(cuerpo["detail"], list)


async def test_ninguna_respuesta_expone_el_hash_de_la_contrasena(client, token_admin):
    for ruta in ("/api/usuarios", "/api/auth/me"):
        resp = await client.get(ruta, headers=cabecera(token_admin))
        assert "password" not in resp.text.lower() or "password_hash" not in resp.text


async def test_la_configuracion_no_lleva_secretos_escritos_en_el_codigo():
    """Las credenciales de los servicios externos vienen del entorno."""
    from app.core.config import Settings

    por_defecto = Settings()
    assert por_defecto.groq_api_key == ""
    assert por_defecto.stripe_secret_key == ""
    assert por_defecto.stripe_webhook_secret == ""
    assert por_defecto.email_password == ""
