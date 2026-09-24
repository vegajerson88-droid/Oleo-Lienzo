"""Configuración central de la aplicación, leída desde variables de entorno (.env)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Óleo & Lienzo API"
    environment: str = "development"

    # Base de datos
    database_url: str = "sqlite+aiosqlite:///./oleo_lienzo.db"

    # JWT
    jwt_secret_key: str = "cambia-esta-clave-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # IA externa (opcional)
    external_ai_api_key: str = ""
    external_ai_base_url: str = "https://api.openai.com/v1"
    external_ai_timeout_seconds: float = 5.0

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
