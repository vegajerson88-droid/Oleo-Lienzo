import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.core.security import hash_password

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# StaticPool + una sola conexión compartida: necesario para que la DB en
# memoria sea la misma entre las distintas sesiones/requests del test.
test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def preparar_db():
    """DB en memoria, aislada y recreada para cada test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as db:
        admin_rol = Rol(nombre="administrador")
        empleado_rol = Rol(nombre="empleado")
        cliente_rol = Rol(nombre="cliente")
        db.add_all([admin_rol, empleado_rol, cliente_rol])
        await db.flush()

        db.add(Usuario(
            nombre="Admin", apellido="Prueba", tipo_documento="CC", numero_documento="1",
            direccion="Calle Test", telefono="3000000000", email="admin@test.com",
            password_hash=hash_password("Admin1234"), rol_id=admin_rol.id,
        ))
        db.add(Usuario(
            nombre="Empleado", apellido="Prueba", tipo_documento="CC", numero_documento="2",
            direccion="Calle Test", telefono="3000000001", email="empleado@test.com",
            password_hash=hash_password("Empleado123"), rol_id=empleado_rol.id,
        ))
        db.add(Usuario(
            nombre="Cliente", apellido="Prueba", tipo_documento="CC", numero_documento="3",
            direccion="Calle Test", telefono="3000000002", email="cliente@test.com",
            password_hash=hash_password("Cliente123"), rol_id=cliente_rol.id,
        ))
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
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def token_admin(client):
    return await _login(client, "admin@test.com", "Admin1234")


@pytest_asyncio.fixture
async def token_empleado(client):
    return await _login(client, "empleado@test.com", "Empleado123")


@pytest_asyncio.fixture
async def token_cliente(client):
    return await _login(client, "cliente@test.com", "Cliente123")
