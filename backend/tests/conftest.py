"""Configuración compartida de la suite de pruebas.

Por defecto las pruebas corren sobre **SQLite en memoria**, que es rápido y no
necesita instalar nada. Para ejecutarlas contra el PostgreSQL real —la base
que usa el proyecto en producción— basta con exportar la variable:

    TEST_DATABASE_URL=postgresql+psycopg://oleo:oleo@localhost:5432/oleo_test
    pytest

Cada prueba recibe una base recién creada y poblada con tres usuarios, uno por
rol, de modo que ninguna pueda contaminar a otra.
"""
import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.limiter import limiter
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models.obra import Obra
from app.models.rol import Permiso, Rol
from app.models.servicio import Servicio
from app.models.usuario import Usuario

URL_PRUEBAS = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
ES_SQLITE = URL_PRUEBAS.startswith("sqlite")

# Con SQLite en memoria hace falta StaticPool para que todas las sesiones
# compartan la misma conexión; si no, cada una vería una base distinta.
opciones = (
    {"connect_args": {"check_same_thread": False}, "poolclass": StaticPool}
    if ES_SQLITE
    else {"poolclass": StaticPool}
)

test_engine = create_async_engine(URL_PRUEBAS, **opciones)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db

# El limitador de peticiones se desactiva en la suite: los fixtures inician
# sesión decenas de veces por minuto y lo dispararían. Que funciona de verdad
# se comprueba en tests/test_seguridad.py, que lo reactiva a propósito.
limiter.enabled = False

# ── Datos de partida ─────────────────────────────────────────────────────
PERMISOS_PRUEBA = [
    ("catalogo.ver", "Consultar obras y servicios"),
    ("catalogo.crear", "Crear obras y servicios"),
    ("ventas.crear", "Registrar ventas"),
    ("pqr.crear", "Radicar PQR"),
]

USUARIOS_PRUEBA = [
    ("Admin", "Prueba", "1000001", "admin@test.com", "Admin1234", "administrador"),
    ("Empleado", "Prueba", "1000002", "empleado@test.com", "Empleado123", "empleado"),
    ("Cliente", "Prueba", "1000003", "cliente@test.com", "Cliente123", "cliente"),
]


@pytest_asyncio.fixture(scope="function", autouse=True)
async def preparar_db():
    """Base aislada y recreada para cada prueba."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as db:
        permisos = [Permiso(codigo=c, descripcion=d) for c, d in PERMISOS_PRUEBA]
        db.add_all(permisos)
        await db.flush()

        roles = {}
        for nombre in ("administrador", "empleado", "cliente"):
            rol = Rol(nombre=nombre, descripcion=f"Rol {nombre}")
            rol.permisos = list(permisos) if nombre == "administrador" else []
            db.add(rol)
            await db.flush()
            roles[nombre] = rol

        for nombre, apellido, doc, email, password, rol in USUARIOS_PRUEBA:
            db.add(
                Usuario(
                    nombre=nombre, apellido=apellido, tipo_documento="CC",
                    numero_documento=doc, direccion="Calle de Prueba 123",
                    telefono="3000000000", email=email,
                    password_hash=hash_password(password), rol_id=roles[rol].id,
                )
            )
        await db.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def cabecera(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def token_admin(client):
    return await _login(client, "admin@test.com", "Admin1234")


@pytest_asyncio.fixture
async def token_empleado(client):
    return await _login(client, "empleado@test.com", "Empleado123")


@pytest_asyncio.fixture
async def token_cliente(client):
    return await _login(client, "cliente@test.com", "Cliente123")


@pytest_asyncio.fixture
async def obra(client, token_empleado):
    """Una obra del catálogo, con stock suficiente para varias pruebas."""
    resp = await client.post(
        "/api/productos",
        json={
            "titulo": "Obra de Prueba", "artista": "Artista Prueba", "anio": 2022,
            "tecnica": "Óleo sobre lienzo", "precio": 100000,
            "descripcion": "Descripción de prueba suficientemente larga.", "stock": 5,
        },
        headers=cabecera(token_empleado),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest_asyncio.fixture
async def servicio(client, token_empleado):
    resp = await client.post(
        "/api/servicios",
        json={
            "nombre": "Servicio de Prueba",
            "descripcion": "Descripción de prueba suficientemente larga.",
            "precio": 50000,
        },
        headers=cabecera(token_empleado),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest_asyncio.fixture
async def id_cliente(client, token_admin):
    resp = await client.get("/api/usuarios?rol=cliente", headers=cabecera(token_admin))
    return resp.json()["items"][0]["id"]
