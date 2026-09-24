"""Pruebas del módulo de PQR y del chatbot con IA."""

import pytest

from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio

PQR_VALIDA = {
    "tipo": "reclamo",
    "asunto": "El marco llegó con una esquina golpeada",
    "mensaje": "Recibí el pedido y el marco venía dañado en la esquina superior derecha.",
}


# ── PQR ──────────────────────────────────────────────────────────────────
async def test_radicar_pqr_autenticado_genera_radicado(client, token_cliente):
    resp = await client.post("/api/pqr", json=PQR_VALIDA, headers=cabecera(token_cliente))
    assert resp.status_code == 201
    data = resp.json()
    assert data["radicado"].startswith("PQR-")
    assert data["estado"] == "pendiente"
    assert data["contacto_email"] == "cliente@test.com"  # tomado de la sesión


async def test_radicar_pqr_sin_sesion_exige_datos_de_contacto(client):
    sin_contacto = await client.post("/api/pqr", json=PQR_VALIDA)
    assert sin_contacto.status_code == 422

    con_contacto = await client.post(
        "/api/pqr",
        json={
            **PQR_VALIDA,
            "contacto_nombre": "Visitante Anonimo",
            "contacto_email": "visitante@test.com",
        },
    )
    assert con_contacto.status_code == 201
    assert con_contacto.json()["cliente_id"] is None


@pytest.mark.parametrize("tipo", ["peticion", "queja", "reclamo", "sugerencia"])
async def test_se_admiten_los_cuatro_tipos(client, token_cliente, tipo):
    resp = await client.post(
        "/api/pqr", json={**PQR_VALIDA, "tipo": tipo}, headers=cabecera(token_cliente)
    )
    assert resp.status_code == 201 and resp.json()["tipo"] == tipo


async def test_tipo_invalido_422(client, token_cliente):
    resp = await client.post(
        "/api/pqr", json={**PQR_VALIDA, "tipo": "felicitacion"}, headers=cabecera(token_cliente)
    )
    assert resp.status_code == 422


async def test_mensaje_demasiado_corto_422(client, token_cliente):
    resp = await client.post(
        "/api/pqr", json={**PQR_VALIDA, "mensaje": "corto"}, headers=cabecera(token_cliente)
    )
    assert resp.status_code == 422


async def test_responder_una_pqr(client, token_cliente, token_empleado):
    pqr = (await client.post("/api/pqr", json=PQR_VALIDA, headers=cabecera(token_cliente))).json()

    resp = await client.post(
        f"/api/pqr/{pqr['id']}/responder",
        json={"respuesta": "Lamentamos el inconveniente, programamos el reemplazo sin costo."},
        headers=cabecera(token_empleado),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["estado"] == "respondida"
    assert data["respondido_por_id"] is not None
    assert data["respondido_en"] is not None


async def test_el_cliente_no_puede_responder_su_propia_pqr_403(client, token_cliente):
    pqr = (await client.post("/api/pqr", json=PQR_VALIDA, headers=cabecera(token_cliente))).json()
    resp = await client.post(
        f"/api/pqr/{pqr['id']}/responder",
        json={"respuesta": "Intento de auto-responderme la solicitud."},
        headers=cabecera(token_cliente),
    )
    assert resp.status_code == 403


async def test_no_se_marca_respondida_sin_respuesta_422(client, token_cliente, token_admin):
    pqr = (await client.post("/api/pqr", json=PQR_VALIDA, headers=cabecera(token_cliente))).json()
    resp = await client.patch(
        f"/api/pqr/{pqr['id']}/estado",
        json={"nuevo_estado": "respondida"},
        headers=cabecera(token_admin),
    )
    assert resp.status_code == 422


async def test_una_pqr_cerrada_es_final(client, token_cliente, token_admin):
    pqr = (await client.post("/api/pqr", json=PQR_VALIDA, headers=cabecera(token_cliente))).json()
    cabeceras = cabecera(token_admin)

    cerrada = await client.patch(
        f"/api/pqr/{pqr['id']}/estado", json={"nuevo_estado": "cerrada"}, headers=cabeceras
    )
    assert cerrada.json()["estado"] == "cerrada"

    reabrir = await client.patch(
        f"/api/pqr/{pqr['id']}/estado", json={"nuevo_estado": "en_proceso"}, headers=cabeceras
    )
    assert reabrir.status_code == 422

    responder = await client.post(
        f"/api/pqr/{pqr['id']}/responder",
        json={"respuesta": "Intento de responder una solicitud ya cerrada."},
        headers=cabeceras,
    )
    assert responder.status_code == 422


async def test_el_cliente_solo_ve_sus_propias_pqr(client, token_cliente, token_admin):
    await client.post("/api/pqr", json=PQR_VALIDA, headers=cabecera(token_cliente))
    await client.post(
        "/api/pqr",
        json={**PQR_VALIDA, "contacto_nombre": "Otro", "contacto_email": "otro@test.com"},
    )

    del_admin = await client.get("/api/pqr", headers=cabecera(token_admin))
    assert del_admin.json()["total"] == 2

    del_cliente = await client.get("/api/pqr", headers=cabecera(token_cliente))
    assert del_cliente.json()["total"] == 1


async def test_filtrar_pqr_por_estado_y_tipo(client, token_cliente, token_admin):
    await client.post(
        "/api/pqr", json={**PQR_VALIDA, "tipo": "queja"}, headers=cabecera(token_cliente)
    )
    cabeceras = cabecera(token_admin)
    assert (await client.get("/api/pqr?tipo=queja", headers=cabeceras)).json()["total"] == 1
    assert (await client.get("/api/pqr?tipo=peticion", headers=cabeceras)).json()["total"] == 0
    assert (await client.get("/api/pqr?estado=pendiente", headers=cabeceras)).json()["total"] == 1


# ── Chatbot ──────────────────────────────────────────────────────────────
async def test_el_chatbot_responde_sin_iniciar_sesion(client):
    resp = await client.post(
        "/api/chatbot/mensaje",
        json={"mensaje": "¿Cuál es el horario de la galería?", "session_id": "sesion-de-prueba-1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["respuesta"]) > 0
    assert data["conversacion_id"] > 0


async def test_sin_clave_de_groq_declara_el_modo_local(client):
    """No debe fingir que respondió la IA cuando no está configurada."""
    resp = await client.post(
        "/api/chatbot/mensaje",
        json={"mensaje": "¿Hacen envíos a todo el país?", "session_id": "sesion-de-prueba-2"},
    )
    data = resp.json()
    assert data["generado_por_ia"] is False
    assert "GROQ_API_KEY" in data["detalle"]
    assert "envío" in data["respuesta"].lower() or "envio" in data["respuesta"].lower()


async def test_la_conversacion_se_persiste(client):
    sesion = "sesion-persistente-123"
    primera = await client.post(
        "/api/chatbot/mensaje", json={"mensaje": "Hola, buenas tardes", "session_id": sesion}
    )
    segunda = await client.post(
        "/api/chatbot/mensaje", json={"mensaje": "¿Cómo compro una obra?", "session_id": sesion}
    )
    # La misma sesión continúa la misma conversación.
    assert primera.json()["conversacion_id"] == segunda.json()["conversacion_id"]


async def test_el_admin_audita_las_conversaciones(client, token_admin):
    await client.post(
        "/api/chatbot/mensaje",
        json={"mensaje": "Quiero radicar una queja", "session_id": "sesion-auditoria"},
    )
    resp = await client.get("/api/chatbot/conversaciones", headers=cabecera(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    # Se guardan tanto la pregunta como la respuesta.
    assert len(data["items"][0]["mensajes"]) == 2
    roles = {m["rol"] for m in data["items"][0]["mensajes"]}
    assert roles == {"usuario", "asistente"}


async def test_las_conversaciones_son_solo_para_el_admin_403(client, token_cliente):
    resp = await client.get("/api/chatbot/conversaciones", headers=cabecera(token_cliente))
    assert resp.status_code == 403


async def test_mensaje_vacio_422(client):
    resp = await client.post(
        "/api/chatbot/mensaje", json={"mensaje": "", "session_id": "sesion-vacia-1"}
    )
    assert resp.status_code == 422
