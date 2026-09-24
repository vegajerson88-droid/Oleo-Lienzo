"""Motor y sesión de base de datos (SQLAlchemy 2.x async)."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos ORM."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependencia de FastAPI: entrega una sesión de DB por request."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """Crea las tablas si no existen (para desarrollo; en prod usar migraciones)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
