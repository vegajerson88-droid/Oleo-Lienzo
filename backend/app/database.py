"""Motor y sesión de base de datos (SQLAlchemy 2.x async sobre PostgreSQL).

La URL de conexión llega siempre desde la variable de entorno DATABASE_URL:
    postgresql+psycopg://usuario:contraseña@host:puerto/base_de_datos

El driver es psycopg 3 en modo asíncrono. Las pruebas automatizadas usan
SQLite en memoria, por eso el motor detecta el dialecto y solo aplica las
opciones de pool cuando la base lo soporta.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

_es_sqlite = settings.database_url.startswith("sqlite")

# SQLite no admite pool_size/max_overflow; PostgreSQL sí los aprovecha.
_opciones_pool: dict = (
    {}
    if _es_sqlite
    else {
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_pre_ping": True,  # descarta conexiones muertas antes de usarlas
        "pool_recycle": 1800,
    }
)

engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    future=True,
    **_opciones_pool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: entrega una sesión de base de datos por request.

    Si el manejador lanza una excepción se revierte la transacción para que
    nunca quede un commit a medias.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_models() -> None:
    """Crea las tablas si no existen.

    Pensado para desarrollo y para el arranque del contenedor. El esquema
    oficial y versionado está en `sql/schema_postgresql.sql`.
    """
    # Importa el paquete de modelos para que todas las tablas queden
    # registradas en Base.metadata antes de crearlas.
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
