"""Pruebas de reportes, dashboards, diagnóstico del sistema, IA y pagos."""

import pytest

from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio

TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


async def _venta(client, token_admin, obra, id_cliente, cantidad=1):
    return (
        await client.post(
            "/api/ventas",
            json={
                "cliente_id": id_cliente,
                "detalles": [{"obra_id": obra["id"], "cantidad": cantidad}],
            },
            headers=cabecera(token_admin),
        )
    ).json()


# ── Reportes ─────────────────────────────────────────────────────────────
async def test_reporte_json_consolida_los_totales(client, obra, token_admin, id_cliente):
    await _venta(client, token_admin, obra, id_cliente, cantidad=2)
    resp = await client.get("/api/reportes/ventas-diarias", headers=cabecera(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["resumen"]["ventas_registradas"] == 1
    assert data["resumen"]["unidades_vendidas"] == 2
    assert data["resumen"]["total"] > 0
    assert len(data["ventas"]) == 1
    assert data["ventas"][0]["items"][0]["tipo"] == "obra"


async def test_reporte_de_un_dia_sin_ventas(client, token_admin):
    resp = await client.get(
        "/api/reportes/ventas-diarias?dia=2020-01-01", headers=cabecera(token_admin)
    )
    assert resp.status_code == 200
    assert resp.json()["resumen"]["ventas_registradas"] == 0


async def test_exportar_el_reporte_a_pdf(client, obra, token_admin, id_cliente):
    await _venta(client, token_admin, obra, id_cliente)
    resp = await client.get("/api/reportes/ventas-diarias/pdf", headers=cabecera(token_admin))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert "attachment" in resp.headers["content-disposition"]


async def test_exportar_el_reporte_a_excel(client, obra, token_admin, id_cliente):
    await _venta(client, token_admin, obra, id_cliente)
    resp = await client.get("/api/reportes/ventas-diarias/excel", headers=cabecera(token_admin))
    assert resp.status_code == 200
    assert resp.headers["content-type"] == TIPO_EXCEL
    # Un .xlsx es un ZIP: debe empezar por su firma.
    assert resp.content.startswith(b"PK")


async def test_el_excel_se_abre_y_trae_las_dos_hojas(client, obra, token_admin, id_cliente):
    import io

    import openpyxl

    await _venta(client, token_admin, obra, id_cliente)
    resp = await client.get("/api/reportes/ventas-diarias/excel", headers=cabecera(token_admin))
    libro = openpyxl.load_workbook(io.BytesIO(resp.content))
    assert libro.sheetnames == ["Ventas", "Resumen"]
    hoja = libro["Ventas"]
    assert hoja.auto_filter.ref is not None  # filtros activos
    assert hoja.freeze_panes is not None  # cabecera congelada


async def test_los_reportes_son_solo_para_admin_y_empleado(client, token_cliente):
    for ruta in ("", "/pdf", "/excel"):
        resp = await client.get(
            f"/api/reportes/ventas-diarias{ruta}", headers=cabecera(token_cliente)
        )
        assert resp.status_code == 403


# ── Dashboards ───────────────────────────────────────────────────────────
async def test_dashboard_del_administrador(client, obra, token_admin, id_cliente):
    await _venta(client, token_admin, obra, id_cliente)
    resp = await client.get("/api/dashboard", headers=cabecera(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["rol"] == "administrador"

    claves = {i["clave"] for i in data["indicadores"]}
    assert {"total_usuarios", "total_ventas", "ingresos", "pqr_pendientes"} <= claves

    tipos = {g["tipo"] for g in data["graficos"]}
    assert {"linea", "barras"} <= tipos  # hay gráfico lineal y de barras


async def test_el_empleado_no_ve_usuarios_ni_ingresos(client, token_empleado):
    resp = await client.get("/api/dashboard", headers=cabecera(token_empleado))
    data = resp.json()
    claves = {i["clave"] for i in data["indicadores"]}
    assert "total_obras" in claves
    assert "total_usuarios" not in claves
    assert "ingresos" not in claves


async def test_el_cliente_solo_ve_su_propia_actividad(client, token_cliente):
    resp = await client.get("/api/dashboard", headers=cabecera(token_cliente))
    data = resp.json()
    assert data["rol"] == "cliente"
    claves = {i["clave"] for i in data["indicadores"]}
    assert claves == {
        "mis_pedidos",
        "mis_compras",
        "total_invertido",
        "mis_facturas",
        "mis_pqr_abiertas",
    }


async def test_el_dashboard_calcula_los_datos_en_la_base(client, obra, token_admin, id_cliente):
    """Los indicadores salen de la base, no están escritos en el frontend."""
    antes = (await client.get("/api/dashboard", headers=cabecera(token_admin))).json()
    ventas_antes = next(i for i in antes["indicadores"] if i["clave"] == "total_ventas")["valor"]

    await _venta(client, token_admin, obra, id_cliente)

    despues = (await client.get("/api/dashboard", headers=cabecera(token_admin))).json()
    ventas_despues = next(i for i in despues["indicadores"] if i["clave"] == "total_ventas")[
        "valor"
    ]
    assert ventas_despues == ventas_antes + 1


async def test_dashboard_con_rango_de_fechas_invertido_422(client, token_admin):
    resp = await client.get(
        "/api/dashboard?fecha_inicio=2026-12-31&fecha_fin=2026-01-01",
        headers=cabecera(token_admin),
    )
    assert resp.status_code == 422


async def test_dashboard_requiere_sesion_401(client):
    assert (await client.get("/api/dashboard")).status_code == 401


# ── Diagnóstico del sistema ──────────────────────────────────────────────
async def test_salud_es_publica(client):
    resp = await client.get("/api/sistema/salud")
    assert resp.status_code == 200
    assert resp.json()["estado"] == "ok"


async def test_el_diagnostico_es_solo_para_admin_403(client, token_cliente):
    resp = await client.get("/api/sistema/diagnostico", headers=cabecera(token_cliente))
    assert resp.status_code == 403


async def test_el_diagnostico_comprueba_cada_dependencia(client, token_admin):
    """No devuelve «ok» a secas: consulta cada servicio y reporta su latencia."""
    resp = await client.get("/api/sistema/diagnostico", headers=cabecera(token_admin))
    assert resp.status_code == 200
    data = resp.json()

    esperados = {"base_de_datos", "ia_local", "ia_externa", "pasarela_pago", "correo"}
    assert esperados == set(data["componentes"])

    # La base de datos se comprueba con una consulta real.
    bd = data["componentes"]["base_de_datos"]
    assert bd["estado"] == "ok"
    assert bd["latencia_ms"] >= 0
    assert bd["detalle"]

    # Las integraciones sin configurar se declaran como tal, no como error.
    for nombre in ("ia_externa", "pasarela_pago", "correo"):
        assert data["componentes"][nombre]["estado"] == "no_configurado"
        assert data["componentes"][nombre]["detalle"]

    # Sin errores reales, el estado general no es «degradado».
    assert data["estado_general"] == "ok"


# ── Inteligencia Artificial ──────────────────────────────────────────────
async def test_la_ia_del_catalogo_es_solo_para_el_personal_403(client, token_cliente):
    resp = await client.get(
        "/api/ia/precio-sugerido?anio=2022&tecnica=Óleo", headers=cabecera(token_cliente)
    )
    assert resp.status_code == 403


async def test_precio_sugerido_declara_si_el_modelo_no_esta_entrenado(client, token_empleado):
    resp = await client.get(
        "/api/ia/precio-sugerido?anio=2022&tecnica=Óleo", headers=cabecera(token_empleado)
    )
    assert resp.status_code == 200
    data = resp.json()
    # Con o sin modelo, la respuesta es honesta sobre su disponibilidad.
    assert "disponible" in data
    if not data["disponible"]:
        assert data["detalle"]
    else:
        assert data["precio_estimado"] >= 0


async def test_parametros_de_la_ia_validados_422(client, token_empleado):
    resp = await client.get(
        "/api/ia/precio-sugerido?anio=99&tecnica=x", headers=cabecera(token_empleado)
    )
    assert resp.status_code == 422


async def test_descripcion_sugerida_sin_clave_degrada(client, token_empleado):
    resp = await client.get(
        "/api/ia/descripcion-sugerida?titulo=Nocturno&tecnica=Óleo",
        headers=cabecera(token_empleado),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["disponible"] is False
    assert "GROQ_API_KEY" in data["detalle"]


# ── Pagos ────────────────────────────────────────────────────────────────
async def test_la_configuracion_expone_solo_la_clave_publica(client):
    resp = await client.get("/api/pagos/configuracion")
    assert resp.status_code == 200
    data = resp.json()
    assert data["configurado"] is False
    assert "publishable_key" in data
    assert "secret" not in resp.text.lower()


async def test_checkout_sin_stripe_configurado_422(client, obra, token_admin, id_cliente):
    venta = await _venta(client, token_admin, obra, id_cliente)
    resp = await client.post(
        "/api/pagos/checkout", json={"venta_id": venta["id"]}, headers=cabecera(token_admin)
    )
    assert resp.status_code == 422
    assert "STRIPE_SECRET_KEY" in resp.json()["detail"]


async def test_checkout_de_venta_inexistente_404(client, token_admin):
    resp = await client.post(
        "/api/pagos/checkout", json={"venta_id": 9999}, headers=cabecera(token_admin)
    )
    assert resp.status_code == 404


async def test_el_webhook_rechaza_una_firma_invalida_400(client):
    """Sin verificar la firma, cualquiera podría fingir un pago completado."""
    resp = await client.post(
        "/api/pagos/webhook",
        content=b'{"type":"checkout.session.completed"}',
        headers={"Stripe-Signature": "firma-falsa", "Content-Type": "application/json"},
    )
    assert resp.status_code == 400


async def test_el_webhook_rechaza_una_peticion_sin_firma_400(client):
    resp = await client.post(
        "/api/pagos/webhook",
        content=b'{"type":"checkout.session.completed"}',
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
