"""Pruebas del flujo comercial: pedidos, ventas y facturación.

Cubren las reglas de negocio que no son un CRUD: máquinas de estado,
inventario, cálculo del IVA y aislamiento entre clientes.
"""

import pytest

from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio

IVA = 0.19


async def _crear_pedido(client, token_cliente, obra_id, cantidad=1, servicio_id=None):
    detalles = [{"obra_id": obra_id, "cantidad": cantidad}]
    if servicio_id:
        detalles.append({"servicio_id": servicio_id, "cantidad": 1})
    return await client.post(
        "/api/pedidos", json={"detalles": detalles}, headers=cabecera(token_cliente)
    )


# ── Pedidos ──────────────────────────────────────────────────────────────
async def test_crear_pedido_calcula_el_total(client, obra, token_cliente):
    resp = await _crear_pedido(client, token_cliente, obra["id"], cantidad=2)
    assert resp.status_code == 201
    data = resp.json()
    assert data["estado"] == "pendiente"
    assert data["total"] == obra["precio"] * 2


async def test_pedido_admite_obras_y_servicios(client, obra, servicio, token_cliente):
    resp = await _crear_pedido(client, token_cliente, obra["id"], 1, servicio["id"])
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["detalles"]) == 2
    assert data["total"] == obra["precio"] + servicio["precio"]
    tipos = {("obra" if d["obra"] else "servicio") for d in data["detalles"]}
    assert tipos == {"obra", "servicio"}


async def test_linea_debe_ser_obra_o_servicio_no_ambos(client, obra, servicio, token_cliente):
    ambos = await client.post(
        "/api/pedidos",
        json={"detalles": [{"obra_id": obra["id"], "servicio_id": servicio["id"]}]},
        headers=cabecera(token_cliente),
    )
    assert ambos.status_code == 422

    ninguno = await client.post(
        "/api/pedidos", json={"detalles": [{"cantidad": 1}]}, headers=cabecera(token_cliente)
    )
    assert ninguno.status_code == 422


async def test_solo_el_cliente_crea_pedidos_403(client, obra, token_empleado):
    resp = await client.post(
        "/api/pedidos",
        json={"detalles": [{"obra_id": obra["id"], "cantidad": 1}]},
        headers=cabecera(token_empleado),
    )
    assert resp.status_code == 403


async def test_pedido_respeta_el_stock(client, obra, token_cliente):
    """La obra de prueba tiene stock 5."""
    demasiado = await _crear_pedido(client, token_cliente, obra["id"], cantidad=6)
    assert demasiado.status_code == 422
    assert "stock" in demasiado.json()["detail"].lower()


async def test_el_pedido_reserva_inventario(client, obra, token_cliente):
    await _crear_pedido(client, token_cliente, obra["id"], cantidad=3)
    actual = (await client.get(f"/api/productos/{obra['id']}")).json()
    assert actual["stock"] == 2


async def test_obra_no_disponible_no_se_puede_pedir(client, obra, token_empleado, token_cliente):
    await client.patch(
        f"/api/productos/{obra['id']}",
        json={"disponible": False},
        headers=cabecera(token_empleado),
    )
    resp = await _crear_pedido(client, token_cliente, obra["id"])
    assert resp.status_code == 422


async def test_obra_inexistente_404(client, token_cliente):
    resp = await _crear_pedido(client, token_cliente, 9999)
    assert resp.status_code == 404


@pytest.mark.parametrize("estado_invalido", ["entregado", "pendiente"])
async def test_transiciones_invalidas_desde_pendiente_422(
    client, obra, token_cliente, token_admin, estado_invalido
):
    pedido = (await _crear_pedido(client, token_cliente, obra["id"])).json()
    resp = await client.patch(
        f"/api/pedidos/{pedido['id']}/estado",
        json={"nuevo_estado": estado_invalido},
        headers=cabecera(token_admin),
    )
    assert resp.status_code == 422


async def test_ciclo_completo_del_pedido(client, obra, token_cliente, token_admin):
    pedido = (await _crear_pedido(client, token_cliente, obra["id"])).json()
    cabeceras = cabecera(token_admin)

    confirmado = await client.patch(
        f"/api/pedidos/{pedido['id']}/estado",
        json={"nuevo_estado": "confirmado"},
        headers=cabeceras,
    )
    assert confirmado.json()["estado"] == "confirmado"

    entregado = await client.patch(
        f"/api/pedidos/{pedido['id']}/estado",
        json={"nuevo_estado": "entregado"},
        headers=cabeceras,
    )
    assert entregado.json()["estado"] == "entregado"

    # Entregado es un estado final.
    final = await client.patch(
        f"/api/pedidos/{pedido['id']}/estado",
        json={"nuevo_estado": "cancelado"},
        headers=cabeceras,
    )
    assert final.status_code == 422


async def test_cancelar_devuelve_el_inventario(client, obra, token_cliente, token_admin):
    pedido = (await _crear_pedido(client, token_cliente, obra["id"], cantidad=2)).json()
    assert (await client.get(f"/api/productos/{obra['id']}")).json()["stock"] == 3

    await client.patch(
        f"/api/pedidos/{pedido['id']}/estado",
        json={"nuevo_estado": "cancelado"},
        headers=cabecera(token_admin),
    )
    assert (await client.get(f"/api/productos/{obra['id']}")).json()["stock"] == 5


async def test_un_cliente_no_ve_el_pedido_de_otro_403(client, obra, token_cliente):
    pedido = (await _crear_pedido(client, token_cliente, obra["id"])).json()

    registro = await client.post(
        "/api/auth/registro",
        json={
            "nombre": "Otro",
            "apellido": "Cliente",
            "tipo_documento": "CC",
            "numero_documento": "55555555",
            "direccion": "Calle X 12-34",
            "telefono": "3005555555",
            "email": "otro@test.com",
            "password": "Clave1234",
            "confirmar_password": "Clave1234",
        },
    )
    assert registro.status_code == 201
    otro = (
        await client.post(
            "/api/auth/login", json={"email": "otro@test.com", "password": "Clave1234"}
        )
    ).json()["access_token"]

    resp = await client.get(f"/api/pedidos/{pedido['id']}", headers=cabecera(otro))
    assert resp.status_code == 403


# ── Confirmar un pedido genera la venta ──────────────────────────────────
async def test_confirmar_pedido_genera_la_venta(client, obra, token_cliente, token_admin):
    pedido = (await _crear_pedido(client, token_cliente, obra["id"], cantidad=2)).json()
    await client.patch(
        f"/api/pedidos/{pedido['id']}/estado",
        json={"nuevo_estado": "confirmado"},
        headers=cabecera(token_admin),
    )

    ventas = (await client.get("/api/ventas", headers=cabecera(token_admin))).json()
    assert ventas["total"] == 1
    venta = ventas["items"][0]
    assert venta["pedido_id"] == pedido["id"]
    assert venta["estado"] == "pendiente_pago"
    assert venta["numero"].startswith("V-")
    # El IVA se calcula sobre la base gravable, no sobre el bruto.
    assert venta["impuestos"] == pytest.approx((venta["subtotal"] - venta["descuento"]) * IVA)
    assert venta["total"] == pytest.approx(
        venta["subtotal"] - venta["descuento"] + venta["impuestos"]
    )


# ── Ventas ───────────────────────────────────────────────────────────────
async def test_registrar_venta_manual_con_descuento(
    client, obra, servicio, token_admin, id_cliente
):
    resp = await client.post(
        "/api/ventas",
        json={
            "cliente_id": id_cliente,
            "detalles": [
                {"obra_id": obra["id"], "cantidad": 1},
                {"servicio_id": servicio["id"], "cantidad": 2},
            ],
            "descuento": 10000,
            "metodo_pago": "efectivo",
        },
        headers=cabecera(token_admin),
    )
    assert resp.status_code == 201
    venta = resp.json()
    esperado = obra["precio"] + servicio["precio"] * 2
    assert venta["subtotal"] == esperado
    assert venta["descuento"] == 10000
    assert venta["impuestos"] == pytest.approx((esperado - 10000) * IVA)
    assert venta["total"] == pytest.approx((esperado - 10000) * (1 + IVA))


async def test_descuento_no_puede_superar_el_subtotal(client, obra, token_admin, id_cliente):
    resp = await client.post(
        "/api/ventas",
        json={
            "cliente_id": id_cliente,
            "detalles": [{"obra_id": obra["id"], "cantidad": 1, "descuento": 999999999}],
        },
        headers=cabecera(token_admin),
    )
    assert resp.status_code == 422


async def test_cliente_no_puede_registrar_ventas_403(client, obra, token_cliente, id_cliente):
    resp = await client.post(
        "/api/ventas",
        json={"cliente_id": id_cliente, "detalles": [{"obra_id": obra["id"], "cantidad": 1}]},
        headers=cabecera(token_cliente),
    )
    assert resp.status_code == 403


async def test_venta_pagada_no_se_anula_sino_que_se_reembolsa(
    client, obra, token_admin, id_cliente
):
    venta = (
        await client.post(
            "/api/ventas",
            json={"cliente_id": id_cliente, "detalles": [{"obra_id": obra["id"], "cantidad": 1}]},
            headers=cabecera(token_admin),
        )
    ).json()
    cabeceras = cabecera(token_admin)

    pagada = await client.patch(
        f"/api/ventas/{venta['id']}/estado", json={"nuevo_estado": "pagada"}, headers=cabeceras
    )
    assert pagada.json()["estado"] == "pagada"

    anular = await client.patch(
        f"/api/ventas/{venta['id']}/estado", json={"nuevo_estado": "anulada"}, headers=cabeceras
    )
    assert anular.status_code == 422

    reembolso = await client.patch(
        f"/api/ventas/{venta['id']}/estado",
        json={"nuevo_estado": "reembolsada"},
        headers=cabeceras,
    )
    assert reembolso.json()["estado"] == "reembolsada"


async def test_anular_una_venta_devuelve_el_inventario(client, obra, token_admin, id_cliente):
    venta = (
        await client.post(
            "/api/ventas",
            json={"cliente_id": id_cliente, "detalles": [{"obra_id": obra["id"], "cantidad": 2}]},
            headers=cabecera(token_admin),
        )
    ).json()
    assert (await client.get(f"/api/productos/{obra['id']}")).json()["stock"] == 3

    await client.patch(
        f"/api/ventas/{venta['id']}/estado",
        json={"nuevo_estado": "anulada"},
        headers=cabecera(token_admin),
    )
    assert (await client.get(f"/api/productos/{obra['id']}")).json()["stock"] == 5


async def test_historial_con_filtros(client, obra, token_admin, id_cliente):
    for _ in range(3):
        await client.post(
            "/api/ventas",
            json={"cliente_id": id_cliente, "detalles": [{"obra_id": obra["id"], "cantidad": 1}]},
            headers=cabecera(token_admin),
        )
    cabeceras = cabecera(token_admin)

    todas = await client.get("/api/ventas", headers=cabeceras)
    assert todas.json()["total"] == 3

    por_obra = await client.get(f"/api/ventas?obra_id={obra['id']}", headers=cabeceras)
    assert por_obra.json()["total"] == 3

    por_estado = await client.get("/api/ventas?estado=pagada", headers=cabeceras)
    assert por_estado.json()["total"] == 0

    por_valor = await client.get("/api/ventas?total_min=999999999", headers=cabeceras)
    assert por_valor.json()["total"] == 0

    rango_invertido = await client.get(
        "/api/ventas?fecha_inicio=2026-12-31&fecha_fin=2026-01-01", headers=cabeceras
    )
    assert rango_invertido.status_code == 422


async def test_el_cliente_solo_ve_sus_propias_ventas(
    client, obra, token_admin, token_cliente, id_cliente
):
    await client.post(
        "/api/ventas",
        json={"cliente_id": id_cliente, "detalles": [{"obra_id": obra["id"], "cantidad": 1}]},
        headers=cabecera(token_admin),
    )
    # Aunque pida explícitamente otro cliente_id, el backend impone el suyo.
    resp = await client.get("/api/ventas?cliente_id=1", headers=cabecera(token_cliente))
    assert resp.status_code == 200
    assert all(v["cliente_id"] == id_cliente for v in resp.json()["items"])


# ── Facturación ──────────────────────────────────────────────────────────
async def _venta_para_facturar(client, obra, token_admin, id_cliente):
    return (
        await client.post(
            "/api/ventas",
            json={"cliente_id": id_cliente, "detalles": [{"obra_id": obra["id"], "cantidad": 1}]},
            headers=cabecera(token_admin),
        )
    ).json()


async def test_emitir_factura_congela_los_datos(client, obra, token_admin, id_cliente):
    venta = await _venta_para_facturar(client, obra, token_admin, id_cliente)
    resp = await client.post(
        "/api/facturas", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
    )
    assert resp.status_code == 201
    factura = resp.json()
    assert factura["numero"].startswith("OL-")
    assert factura["total"] == venta["total"]
    assert factura["cliente_nombre"]
    assert factura["cliente_documento"]
    assert len(factura["detalles"]) == 1


async def test_una_venta_solo_se_factura_una_vez_409(client, obra, token_admin, id_cliente):
    venta = await _venta_para_facturar(client, obra, token_admin, id_cliente)
    primera = await client.post(
        "/api/facturas", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
    )
    assert primera.status_code == 201
    segunda = await client.post(
        "/api/facturas", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
    )
    assert segunda.status_code == 409


async def test_no_se_factura_una_venta_anulada_422(client, obra, token_admin, id_cliente):
    venta = await _venta_para_facturar(client, obra, token_admin, id_cliente)
    await client.patch(
        f"/api/ventas/{venta['id']}/estado",
        json={"nuevo_estado": "anulada"},
        headers=cabecera(token_admin),
    )
    resp = await client.post(
        "/api/facturas", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
    )
    assert resp.status_code == 422


async def test_facturar_una_venta_inexistente_404(client, token_admin):
    resp = await client.post(
        "/api/facturas", json={"venta_id": 9999}, headers=cabecera(token_admin)
    )
    assert resp.status_code == 404


async def test_descargar_la_factura_en_pdf(client, obra, token_admin, id_cliente):
    venta = await _venta_para_facturar(client, obra, token_admin, id_cliente)
    factura = (
        await client.post(
            "/api/facturas", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
        )
    ).json()

    resp = await client.get(f"/api/facturas/{factura['id']}/pdf", headers=cabecera(token_admin))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")  # es un PDF de verdad
    assert factura["numero"] in resp.headers["content-disposition"]


async def test_buscar_facturas_por_numero_y_cliente(client, obra, token_admin, id_cliente):
    venta = await _venta_para_facturar(client, obra, token_admin, id_cliente)
    factura = (
        await client.post(
            "/api/facturas", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
        )
    ).json()
    cabeceras = cabecera(token_admin)

    por_numero = await client.get(f"/api/facturas?numero={factura['numero']}", headers=cabeceras)
    assert por_numero.json()["total"] == 1

    por_cliente = await client.get(f"/api/facturas?cliente_id={id_cliente}", headers=cabeceras)
    assert por_cliente.json()["total"] == 1

    sin_coincidencias = await client.get("/api/facturas?numero=OL-999999", headers=cabeceras)
    assert sin_coincidencias.json()["total"] == 0


async def test_transiciones_de_la_factura(client, obra, token_admin, id_cliente):
    venta = await _venta_para_facturar(client, obra, token_admin, id_cliente)
    factura = (
        await client.post(
            "/api/facturas", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
        )
    ).json()
    cabeceras = cabecera(token_admin)

    pagada = await client.patch(
        f"/api/facturas/{factura['id']}/estado",
        json={"nuevo_estado": "pagada"},
        headers=cabeceras,
    )
    assert pagada.json()["estado"] == "pagada"

    anulada = await client.patch(
        f"/api/facturas/{factura['id']}/estado",
        json={"nuevo_estado": "anulada"},
        headers=cabeceras,
    )
    assert anulada.json()["estado"] == "anulada"

    # Anulada es un estado final.
    final = await client.patch(
        f"/api/facturas/{factura['id']}/estado",
        json={"nuevo_estado": "pagada"},
        headers=cabeceras,
    )
    assert final.status_code == 422
