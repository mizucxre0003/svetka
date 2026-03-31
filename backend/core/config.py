from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://svetka:svetka_dev@localhost:5432/svetka"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Bot
    BOT_TOKEN: str = ""
    BOT_WEBHOOK_URL: str = ""

    # API Security
    API_SECRET_KEY: str = "change-me-in-production"

    # Super Admin Auth (Bearer token)
    ADMIN_TOKEN: str = "change-me-super-secret-admin-token"

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Тарифные лимиты
    FREE_TRIGGER_LIMIT: int = 10
    FREE_WARN_LIMIT: int = 3


@lru_cache()
def get_settings() -> Settings:
    return Settings()
