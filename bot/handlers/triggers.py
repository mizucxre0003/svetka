"""
Обработчик триггеров/автоответов.
Проверяет сообщения на совпадение с триггерами и отвечает.
Триггеры кэшируются в Redis.
"""
import json
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Any, Awaitable
from core.backend import backend
from core.cache import get_redis, get_chat_settings_cached
from loguru import logger

TRIGGER_CACHE_TTL = 120  # секунд


async def get_triggers_cached(chat_id: int) -> list[dict]:
    key = f"triggers:{chat_id}"
    try:
        r = await get_redis()
        cached = await r.get(key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis error getting triggers: {e}")
        r = None

    data = await backend.get_triggers(chat_id)
    
    if r:
        try:
            await r.setex(key, TRIGGER_CACHE_TTL, json.dumps(data))
        except Exception:
            pass
            
    return data


def match_trigger(trigger: dict, text: str) -> bool:
    t = trigger.get("trigger_text", "").lower()
    match_type = trigger.get("match_type", "contains")
    text_l = text.lower()
    if match_type == "exact":
        return text_l == t
    elif match_type == "startswith":
        return text_l.startswith(t)
    else:
        return t in text_l


class TriggersMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        chat_db = data.get("chat_db")
        if not chat_db or event.chat.type not in ("group", "supergroup") or not event.from_user or event.from_user.is_bot:
            return await handler(event, data)

        settings = await get_chat_settings_cached(chat_db["id"], backend)
        if not settings or not settings.get("triggers_enabled"):
            return await handler(event, data)

        triggers = await get_triggers_cached(chat_db["id"])
        text = event.text or ""

        for trigger in triggers:
            if not trigger.get("is_enabled"):
                continue
            if match_trigger(trigger, text):
                try:
                    await event.reply(trigger["response_text"])
                except Exception as e:
                    logger.warning(f"Trigger reply failed: {e}")
                # Don't break, allow multiple triggers or just one? Usually just one
                break
                
        return await handler(event, data)
