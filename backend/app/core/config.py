"""Configuración central de la aplicación, leída desde variables de entorno (.env).

Ninguna credencial vive en el código: todo valor sensible se define en `.env`
(ver `.env.example`). Los valores por defecto que aparecen aquí son seguros
para desarrollo y nunca contienen secretos reales.
"""

from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # ── Aplicación ────────────────────────────────────────────────────────
    app_name: str = "Óleo & Lienzo API"
    app_version: str = "5.0.0"
    environment: str = "development"

    # ── Base de datos (PostgreSQL) ────────────────────────────────────────
    # Formato: postgresql+psycopg://usuario:contraseña@host:puerto/base_de_datos
    database_url: str = "postgresql+psycopg://oleo:oleo@localhost:5432/oleo_lienzo"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # ── Seguridad / JWT ───────────────────────────────────────────────────
    jwt_secret_key: str = "cambia-esta-clave-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    # Ventana de validez del enlace de recuperación de contraseña.
    reset_token_expire_minutes: int = 30
    # Intentos de login permitidos por IP y minuto (protección de fuerza bruta).
    login_rate_limit: str = "20/minute"

    # ── CORS / Frontend ───────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    frontend_url: str = "http://localhost:5173"

    # ── IA: Groq (plan gratuito) ──────────────────────────────────────────
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 20.0
    groq_max_tokens: int = 500

    # ── Pasarela de pago: Stripe ──────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_currency: str = "cop"

    # ── Correo saliente (SMTP) ────────────────────────────────────────────
    email_host: str = ""
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_from: str = "no-responder@oleoylienzo.com"
    email_from_name: str = "Óleo & Lienzo"
    email_use_tls: bool = True
    email_timeout_seconds: float = 15.0

    # ── Datos fiscales de la empresa (facturas y correos) ─────────────────
    empresa_nombre: str = "Óleo & Lienzo S.A.S."
    empresa_nit: str = "901.234.567-8"
    empresa_direccion: str = "Calle 45 # 12-30"
    empresa_ciudad: str = "Bogotá D.C., Colombia"
    empresa_telefono: str = "+57 300 123 4567"
    empresa_email: str = "contacto@oleoylienzo.com"

    # ── Reglas de negocio ─────────────────────────────────────────────────
    iva_porcentaje: float = 19.0
    factura_prefijo: str = "OL"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def iva_tasa(self) -> Decimal:
        """IVA como tasa decimal (19.0 -> 0.19)."""
        return Decimal(str(self.iva_porcentaje)) / Decimal("100")

    @property
    def groq_configurado(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def stripe_configurado(self) -> bool:
        return bool(self.stripe_secret_key)

    @property
    def email_configurado(self) -> bool:
        return bool(self.email_host and self.email_user and self.email_password)

    @property
    def es_produccion(self) -> bool:
        return self.environment.lower() in ("production", "produccion", "prod")


@lru_cache
def get_settings() -> Settings:
    return Settings()
