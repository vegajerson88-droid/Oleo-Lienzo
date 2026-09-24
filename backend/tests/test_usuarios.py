"""Pruebas de la gestión de usuarios, roles y control de acceso."""
import pytest

from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio


async def test_listar_usuarios_requiere_autenticacion_401(client):
    assert (await client.get("/api/usuarios")).status_code == 401


async def test_listar_usuarios_prohibido_para_cliente_403(client, token_cliente):
    resp = await client.get("/api/usuarios", headers=cabecera(token_cliente))
    assert resp.status_code == 403


async def test_listar_usuarios_prohibido_para_empleado_403(client, token_empleado):
    """La gestión de usuarios es exclusiva del administrador."""
    resp = await client.get("/api/usuarios", headers=cabecera(token_empleado))
    assert resp.status_code == 403


async def test_listar_usuarios_admin_200(client, token_admin):
    resp = await client.get("/api/usuarios", headers=cabecera(token_admin))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    # Nunca se filtra el hash de la contraseña.
    assert all("password_hash" not in u for u in data["items"])


async def test_filtrar_por_rol_y_buscar(client, token_admin):
    por_rol = await client.get("/api/usuarios?rol=cliente", headers=cabecera(token_admin))
    assert por_rol.json()["total"] == 1

    buscando = await client.get(
        "/api/usuarios?buscar=empleado@test.com", headers=cabecera(token_admin)
    )
    assert buscando.json()["total"] == 1


async def test_paginacion(client, token_admin):
    resp = await client.get("/api/usuarios?page=1&page_size=2", headers=cabecera(token_admin))
    data = resp.json()
    assert data["total"] == 3 and len(data["items"]) == 2


async def test_obtener_usuario_inexistente_404(client, token_admin):
    assert (
        await client.get("/api/usuarios/9999", headers=cabecera(token_admin))
    ).status_code == 404


async def test_id_de_ruta_invalido_422(client, token_admin):
    """El parámetro de ruta está validado con Path(ge=1)."""
    assert (await client.get("/api/usuarios/0", headers=cabecera(token_admin))).status_code == 422
    assert (await client.get("/api/usuarios/-5", headers=cabecera(token_admin))).status_code == 422


async def test_crear_usuario_con_rol_desde_el_panel(client, token_admin):
    resp = await client.post(
        "/api/usuarios",
        json={
            "nombre": "Nuevo", "apellido": "Empleado", "tipo_documento": "CC",
            "numero_documento": "77777777", "direccion": "Calle 100 # 20-30",
            "telefono": "3007777777", "email": "nuevo.empleado@test.com",
            "password": "Clave1234", "confirmar_password": "Clave1234",
            "rol_nombre": "empleado",
        },
        headers=cabecera(token_admin),
    )
    assert resp.status_code == 201
    assert resp.json()["rol"]["nombre"] == "empleado"


async def test_put_exige_el_recurso_completo(client, token_admin, id_cliente):
    """PUT es reemplazo: omitir campos es un 422, no un «déjalo igual»."""
    parcial = await client.put(
        f"/api/usuarios/{id_cliente}", json={"nombre": "SoloNombre"},
        headers=cabecera(token_admin),
    )
    assert parcial.status_code == 422

    completo = await client.put(
        f"/api/usuarios/{id_cliente}",
        json={
            "nombre": "Reemplazado", "apellido": "Completo",
            "direccion": "Nueva Direccion 456", "telefono": "3111111111",
            "rol_id": 3, "activo": True,
        },
        headers=cabecera(token_admin),
    )
    assert completo.status_code == 200
    assert completo.json()["nombre"] == "Reemplazado"


async def test_patch_modifica_solo_lo_enviado(client, token_admin, id_cliente):
    original = (
        await client.get(f"/api/usuarios/{id_cliente}", headers=cabecera(token_admin))
    ).json()

    resp = await client.patch(
        f"/api/usuarios/{id_cliente}", json={"direccion": "Solo cambia la direccion"},
        headers=cabecera(token_admin),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["direccion"] == "Solo cambia la direccion"
    assert data["nombre"] == original["nombre"]  # lo demás sigue igual


async def test_patch_con_rol_inexistente_404(client, token_admin, id_cliente):
    resp = await client.patch(
        f"/api/usuarios/{id_cliente}", json={"rol_id": 999}, headers=cabecera(token_admin)
    )
    assert resp.status_code == 404


async def test_cambiar_estado_activo_inactivo(client, token_admin, id_cliente):
    desactivar = await client.patch(
        f"/api/usuarios/{id_cliente}/estado", json={"activo": False},
        headers=cabecera(token_admin),
    )
    assert desactivar.status_code == 200 and desactivar.json()["activo"] is False

    reactivar = await client.patch(
        f"/api/usuarios/{id_cliente}/estado", json={"activo": True},
        headers=cabecera(token_admin),
    )
    assert reactivar.json()["activo"] is True


async def test_admin_no_puede_desactivarse_ni_borrarse(client, token_admin):
    yo = (await client.get("/api/auth/me", headers=cabecera(token_admin))).json()["id"]
    desactivar = await client.patch(
        f"/api/usuarios/{yo}/estado", json={"activo": False}, headers=cabecera(token_admin)
    )
    assert desactivar.status_code == 422
    assert (
        await client.delete(f"/api/usuarios/{yo}", headers=cabecera(token_admin))
    ).status_code == 422


async def test_eliminar_usuario_sin_historial_204(client, token_admin):
    creado = await client.post(
        "/api/usuarios",
        json={
            "nombre": "Temporal", "apellido": "Borrar", "tipo_documento": "CC",
            "numero_documento": "66666666", "direccion": "Calle 1 # 2-3",
            "telefono": "3006666666", "email": "temporal@test.com",
            "password": "Clave1234", "confirmar_password": "Clave1234",
        },
        headers=cabecera(token_admin),
    )
    id_nuevo = creado.json()["id"]
    assert (
        await client.delete(f"/api/usuarios/{id_nuevo}", headers=cabecera(token_admin))
    ).status_code == 204


async def test_listar_roles_con_sus_permisos(client, token_admin):
    resp = await client.get("/api/usuarios/roles", headers=cabecera(token_admin))
    assert resp.status_code == 200
    roles = resp.json()
    assert {r["nombre"] for r in roles} == {"administrador", "empleado", "cliente"}
    admin = next(r for r in roles if r["nombre"] == "administrador")
    assert len(admin["permisos"]) > 0
