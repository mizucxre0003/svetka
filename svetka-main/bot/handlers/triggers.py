"""
Обработчик триггеров/автоответов.
Проверяет сообщения на совпадение с триггерами и отвечает.
Триггеры кэшируются в Redis.
"""
import json
from aiogram import Router, F
from aiogram.types import Message
from core.backend import backend
from core.cache import get_redis, get_chat_settings_cached
from loguru import logger

router = Router()

TRIGGER_CACHE_TTL = 120  # секунд


async def get_triggers_cached(chat_id: int) -> list[dict]:
    r = await get_redis()
    key = f"triggers:{chat_id}"
    cached = await r.get(key)
    if cached:
        return json.loads(cached)
    data = await backend.get_triggers(chat_id)
    await r.setex(key, TRIGGER_CACHE_TTL, json.dumps(data))
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


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text)
async def trigger_handler(message: Message, chat_db: dict | None = None):
    if not chat_db or not message.from_user or message.from_user.is_bot:
        return

    settings = await get_chat_settings_cached(chat_db["id"], backend)
    if not settings or not settings.get("triggers_enabled"):
        return

    triggers = await get_triggers_cached(chat_db["id"])
    text = message.text or ""

    for trigger in triggers:
        if not trigger.get("is_enabled"):
            continue
        if match_trigger(trigger, text):
            try:
                await message.reply(trigger["response_text"])
            except Exception as e:
                logger.warning(f"Trigger reply failed: {e}")
            break
