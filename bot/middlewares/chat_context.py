"""
Middleware для обогащения context'а данными о чате из backend.
Добавляет chat_db в data для всех handlers.
"""
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Any, Awaitable
from core.backend import backend
from loguru import logger


# Кэш chat_id → backend_chat_data (в памяти процесса, короткий TTL не нужен)
_chat_cache: dict[int, dict] = {}


class ChatContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        chat = event.chat
        if chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        tg_chat_id = chat.id

        # Ищем в памяти
        if tg_chat_id not in _chat_cache:
            # Запрос к backend
            result = await backend.get_chat_by_tg_id(tg_chat_id)
            if result and isinstance(result, list) and len(result) > 0:
                _chat_cache[tg_chat_id] = result[0]
            elif result and isinstance(result, dict):
                _chat_cache[tg_chat_id] = result

        data["chat_db"] = _chat_cache.get(tg_chat_id)
        return await handler(event, data)


def invalidate_chat(tg_chat_id: int):
    _chat_cache.pop(tg_chat_id, None)
