from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BOT_TOKEN: str
    BOT_WEBHOOK_URL: str = ""
    BACKEND_URL: str = "http://backend:8000"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENVIRONMENT: str = "development"

    # ID чата для логов (опционально)
    LOG_CHAT_ID: int = 0


@lru_cache()
def get_settings() -> BotSettings:
    return BotSettings()
