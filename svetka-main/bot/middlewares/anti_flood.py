"""
Антифлуд middleware через Redis sliding window.
Считает количество сообщений пользователя за интервал.
Настройки берутся из chat_settings.
"""
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Any, Awaitable
from core.cache import get_redis
from core.backend import backend
from core.cache import get_chat_settings_cached
from loguru import logger
import time


class AntiFloodMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        # Только для групп/супергрупп
        chat = event.chat
        if chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        user = event.from_user
        if not user or user.is_bot:
            return await handler(event, data)

        # Получить настройки
        chat_data = data.get("chat_db")
        if not chat_data:
            return await handler(event, data)

        settings = await get_chat_settings_cached(chat_data["id"], backend)
        if not settings or not settings.get("anti_flood_enabled"):
            return await handler(event, data)

        limit = settings.get("anti_flood_limit", 5)
        interval = settings.get("anti_flood_interval", 5)
        action = settings.get("anti_flood_action", "mute")

        r = await get_redis()
        key = f"flood:{chat.id}:{user.id}"
        now = int(time.time())
        window_start = now - interval

        # Удаляем старые записи и добавляем текущий timestamp
        pipe = r.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now * 1000 + user.id % 1000): now})
        pipe.zcard(key)
        pipe.expire(key, interval + 1)
        results = await pipe.execute()
        count = results[2]

        if count > limit:
            logger.info(f"AntiFlood triggered: user {user.id} in chat {chat.id}, count={count}")
            try:
                await event.delete()
            except Exception:
                pass

            # Применить наказание
            if action == "mute":
                from datetime import timedelta
                until = int(time.time()) + settings.get("default_mute_duration", 3600)
                try:
                    await event.bot.restrict_chat_member(
                        chat_id=chat.id,
                        user_id=user.id,
                        permissions={"can_send_messages": False},
                        until_date=until,
                    )
                except Exception as e:
                    logger.warning(f"Mute failed: {e}")

            await backend.log_event(
                chat_id=chat_data["id"],
                action_type="anti_flood_triggered",
                actor_tg_id=user.id,
                payload={"count": count, "limit": limit, "action": action},
            )
            await backend.increment_metric(chat_data["id"], "protection_triggers_count")
            return  # Не передаём дальше

        return await handler(event, data)
