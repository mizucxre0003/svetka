"""
Redis-based cache для настроек чатов.
Бот кэширует settings чата в Redis на 60 секунд,
чтобы не дёргать backend при каждом сообщении.
"""
import json
from core.config import get_settings
import redis.asyncio as aioredis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import ConnectionError, TimeoutError

settings = get_settings()

_redis: aioredis.Redis | None = None

SETTINGS_TTL = 60  # секунд


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=10,
            socket_keepalive=True,
            retry_on_timeout=True,
            retry=Retry(ExponentialBackoff(cap=10, base=1), 3),
            retry_on_error=[ConnectionError, TimeoutError]
        )
    return _redis


async def get_chat_settings_cached(chat_id: int, backend_client) -> dict | None:
    r = await get_redis()
    key = f"chat_settings:{chat_id}"
    cached = await r.get(key)
    if cached:
        return json.loads(cached)
    data = await backend_client.get_settings(chat_id)
    if data:
        await r.setex(key, SETTINGS_TTL, json.dumps(data))
    return data


async def invalidate_chat_settings(chat_id: int):
    r = await get_redis()
    await r.delete(f"chat_settings:{chat_id}")


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
