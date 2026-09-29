"""Pruebas con dobles de los servicios externos y del modelo de IA.

Ninguna de estas pruebas sale a la red ni carga el modelo entrenado: Groq y
scikit-learn se sustituyen por dobles. Así la suite es determinista, rápida y
puede ejecutarse sin credenciales, y además permite provocar a voluntad los
fallos del proveedor —tiempo de espera agotado, HTTP 500, respuesta con una
forma inesperada— que en una llamada real no se podrían reproducir.
"""

import httpx
import pytest

from app.core.config import get_settings
from app.services import ai_external, ai_local, chatbot
from tests.conftest import cabecera

pytestmark = pytest.mark.asyncio

settings = get_settings()


class RespuestaFalsa:
    """Doble de `httpx.Response` con lo justo que usa el código."""

    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request("POST", "https://doble.local"),
                response=httpx.Response(self.status_code),
            )


class ClienteFalso:
    """Doble de `httpx.AsyncClient` que devuelve o lanza lo que se le indique."""

    def __init__(self, resultado):
        self._resultado = resultado
        self.llamadas = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def post(self, *_args, **_kwargs):
        self.llamadas += 1
        if isinstance(self._resultado, Exception):
            raise self._resultado
        return self._resultado


def _doblar_httpx(monkeypatch, modulo, resultado) -> ClienteFalso:
    """Sustituye `httpx.AsyncClient` dentro de `modulo` por el doble."""
    doble = ClienteFalso(resultado)
    monkeypatch.setattr(modulo.httpx, "AsyncClient", lambda *a, **k: doble)
    return doble


@pytest.fixture
def con_groq(monkeypatch):
    """Hace creer al código que hay una clave configurada, sin usar ninguna real."""
    monkeypatch.setattr(settings, "groq_api_key", "clave-de-prueba-no-real")
    return settings


# ── Chatbot: el proveedor responde ───────────────────────────────────────
async def test_el_chatbot_usa_la_respuesta_de_la_ia(client, con_groq, monkeypatch):
    _doblar_httpx(
        monkeypatch,
        chatbot,
        RespuestaFalsa({"choices": [{"message": {"content": "  Hola, soy la IA.  "}}]}),
    )

    resp = await client.post(
        "/api/chatbot/mensaje",
        json={"mensaje": "¿Qué obras tienen?", "session_id": "doble-ok"},
    )

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["respuesta"] == "Hola, soy la IA."
    assert cuerpo["generado_por_ia"] is True
    assert cuerpo["modelo"] == settings.groq_model


# ── Chatbot: el proveedor falla y el servicio degrada ────────────────────
@pytest.mark.parametrize(
    "fallo, huella",
    [
        (httpx.TimeoutException("agotado"), "segundos"),
        (httpx.ConnectError("sin red"), "contactar"),
        (RespuestaFalsa({}, status_code=500), "HTTP 500"),
        (RespuestaFalsa({"otra_cosa": []}), "KeyError"),
    ],
)
async def test_el_chatbot_degrada_cuando_el_proveedor_falla(
    client, con_groq, monkeypatch, fallo, huella
):
    """Ante cualquier fallo responde el modo local y lo declara abiertamente."""
    _doblar_httpx(monkeypatch, chatbot, fallo)

    resp = await client.post(
        "/api/chatbot/mensaje",
        json={"mensaje": "¿Hacen envíos?", "session_id": "doble-fallo"},
    )

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["generado_por_ia"] is False, "no debe hacer pasar el respaldo por IA"
    assert cuerpo["respuesta"], "el respaldo local tiene que decir algo útil"
    assert huella in cuerpo["detalle"]


async def test_sin_clave_configurada_responde_el_modo_local(client, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "")

    resp = await client.post(
        "/api/chatbot/mensaje",
        json={"mensaje": "Hola", "session_id": "doble-sin-clave"},
    )

    cuerpo = resp.json()
    assert cuerpo["generado_por_ia"] is False
    assert "GROQ_API_KEY" in cuerpo["detalle"]


async def test_la_clave_nunca_viaja_al_cliente(client, con_groq, monkeypatch):
    """Ni en la respuesta correcta ni en el mensaje de error aparece la clave."""
    _doblar_httpx(monkeypatch, chatbot, RespuestaFalsa({}, status_code=401))

    resp = await client.post(
        "/api/chatbot/mensaje",
        json={"mensaje": "Hola", "session_id": "doble-secreto"},
    )

    assert "clave-de-prueba-no-real" not in resp.text


# ── IA externa: descripción sugerida ─────────────────────────────────────
async def test_descripcion_sugerida_con_el_proveedor_disponible(
    client, token_empleado, con_groq, monkeypatch
):
    _doblar_httpx(
        monkeypatch,
        ai_external,
        RespuestaFalsa({"choices": [{"message": {"content": '"Luz que respira."'}}]}),
    )

    resp = await client.get(
        "/api/ia/descripcion-sugerida?titulo=Nocturno&tecnica=Óleo",
        headers=cabecera(token_empleado),
    )

    cuerpo = resp.json()
    assert cuerpo["disponible"] is True
    # Las comillas que a veces añade el modelo se recortan.
    assert cuerpo["descripcion"] == "Luz que respira."


async def test_la_ia_externa_reintenta_y_luego_degrada(
    client, token_empleado, con_groq, monkeypatch
):
    doble = _doblar_httpx(monkeypatch, ai_external, httpx.TimeoutException("agotado"))

    resp = await client.get(
        "/api/ia/descripcion-sugerida?titulo=Nocturno&tecnica=Óleo",
        headers=cabecera(token_empleado),
    )

    cuerpo = resp.json()
    assert cuerpo["disponible"] is False
    assert doble.llamadas == ai_external.INTENTOS, "debe reintentar antes de rendirse"
    # No inventa una descripción haciéndola pasar por generada.
    assert "descripcion" not in cuerpo


# ── Modelo propio: doble en lugar del .joblib entrenado ──────────────────
class ModeloFalso:
    """Doble del modelo de scikit-learn: devuelve un precio fijo."""

    version = "doble-1.0"

    class _Interno:
        @staticmethod
        def predict(_x):
            return [1_234_567.0]

    modelo = _Interno()


async def test_precio_sugerido_con_el_modelo_doblado(client, token_empleado, monkeypatch):
    from app.main import app as aplicacion

    monkeypatch.setattr(aplicacion.state, "ai_local_model", ModeloFalso(), raising=False)

    resp = await client.get(
        "/api/ia/precio-sugerido?anio=2022&tecnica=Óleo sobre lienzo",
        headers=cabecera(token_empleado),
    )

    cuerpo = resp.json()
    assert cuerpo["disponible"] is True
    assert cuerpo["precio_estimado"] == 1_234_567.0
    assert cuerpo["version_modelo"] == "doble-1.0"


async def test_sin_modelo_entrenado_lo_declara(client, token_empleado, monkeypatch):
    from app.main import app as aplicacion

    monkeypatch.setattr(aplicacion.state, "ai_local_model", None, raising=False)

    resp = await client.get(
        "/api/ia/precio-sugerido?anio=2022&tecnica=Óleo",
        headers=cabecera(token_empleado),
    )

    cuerpo = resp.json()
    assert cuerpo["disponible"] is False
    assert "precio_estimado" not in cuerpo, "sin modelo no se inventa un número"


async def test_las_variables_las_deriva_el_servidor_de_la_obra(
    client, obra, token_empleado, monkeypatch
):
    """Con `obra_id`, el año y la técnica salen de la base, no del cliente."""
    vistas = {}

    def espia(modelo, anio, tecnica):
        vistas["anio"], vistas["tecnica"] = anio, tecnica
        return {"disponible": True, "precio_estimado": 1.0}

    monkeypatch.setattr(ai_local, "predecir_precio", espia)

    resp = await client.get(
        f"/api/ia/precio-sugerido?obra_id={obra['id']}&anio=1500&tecnica=Mentira",
        headers=cabecera(token_empleado),
    )

    assert resp.status_code == 200
    # Los valores que envió el cliente se ignoran: mandan los de la obra.
    assert vistas["anio"] == obra["anio"]
    assert vistas["tecnica"] == obra["tecnica"]


async def test_hace_falta_obra_id_o_bien_anio_y_tecnica(client, token_empleado):
    resp = await client.get("/api/ia/precio-sugerido", headers=cabecera(token_empleado))
    assert resp.status_code == 422
    assert resp.json()["error"] == "ValidationError"


async def test_una_obra_inexistente_responde_404(client, token_empleado):
    resp = await client.get(
        "/api/ia/precio-sugerido?obra_id=999999", headers=cabecera(token_empleado)
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "NotFound"


# ── Tareas en segundo plano: sesión propia y captura de excepciones ──────
async def test_la_tarea_de_compra_abre_su_propia_sesion(monkeypatch):
    """La tarea relee la venta por su id, sin depender del objeto del ORM."""
    from app.services import tareas
    from tests.conftest import TestSessionLocal

    monkeypatch.setattr(tareas, "AsyncSessionLocal", TestSessionLocal)

    enviados = []

    async def correo_falso(venta, numero_factura=None):
        # Si la sesión no estuviera abierta, tocar las relaciones fallaría.
        enviados.append((venta.numero, len(venta.detalles), venta.cliente.email))
        return True

    monkeypatch.setattr(tareas.email_service, "enviar_confirmacion_compra", correo_falso)

    async with TestSessionLocal() as db:
        from sqlalchemy import select

        from app.models.usuario import Usuario

        cliente = (
            await db.execute(select(Usuario).where(Usuario.email == "cliente@test.com"))
        ).scalar_one()
        from app.models.venta import EstadoVenta, MetodoPago, Venta

        venta = Venta(
            numero="V-PRUEBA-1",
            cliente_id=cliente.id,
            estado=EstadoVenta.pagada,
            metodo_pago=MetodoPago.efectivo,
            subtotal=1000,
            descuento=0,
            impuestos=190,
            total=1190,
        )
        db.add(venta)
        await db.commit()
        venta_id = venta.id

    await tareas.confirmar_compra(venta_id)

    assert enviados == [("V-PRUEBA-1", 0, "cliente@test.com")]


async def test_la_tarea_no_deja_escapar_excepciones(monkeypatch, caplog):
    """Si el envío falla, la tarea lo registra pero no propaga el error."""
    from app.services import tareas
    from tests.conftest import TestSessionLocal

    monkeypatch.setattr(tareas, "AsyncSessionLocal", TestSessionLocal)

    async def correo_que_revienta(*_a, **_k):
        raise RuntimeError("el servidor de correo se cayó")

    monkeypatch.setattr(tareas.email_service, "enviar_pqr_radicada", correo_que_revienta)

    async with TestSessionLocal() as db:
        from app.models.pqr import PQR, EstadoPQR, TipoPQR

        pqr = PQR(
            radicado="PQR-PRUEBA",
            tipo=TipoPQR.peticion,
            asunto="Asunto de prueba",
            mensaje="Mensaje de prueba suficientemente largo.",
            estado=EstadoPQR.pendiente,
            contacto_nombre="Quien Sea",
            contacto_email="quien@sea.com",
        )
        db.add(pqr)
        await db.commit()
        pqr_id = pqr.id

    # No debe lanzar: el fallo se queda en el log.
    await tareas.avisar_pqr_radicada(pqr_id)


async def test_la_tarea_tolera_que_el_registro_ya_no_exista(monkeypatch):
    """Si entre la respuesta y la tarea se borró el registro, no revienta."""
    from app.services import tareas
    from tests.conftest import TestSessionLocal

    monkeypatch.setattr(tareas, "AsyncSessionLocal", TestSessionLocal)
    await tareas.confirmar_compra(999_999)
