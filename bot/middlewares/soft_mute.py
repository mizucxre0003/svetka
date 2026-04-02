from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Any, Awaitable
from core.cache import is_soft_muted
from loguru import logger

class SoftMuteMiddleware(BaseMiddleware):
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
            
        user = event.from_user
        if not user:
            return await handler(event, data)

        # Проверяем, есть ли пользователь в списке софт-мута
        chat_db = data.get("chat_db")
        if chat_db and await is_soft_muted(chat_db["id"], user.id):
            try:
                await event.delete()
            except Exception:
                # Если не удалось удалить, возможно нет прав администратора
                # Чтобы не спамить, можно было бы сделать флаг, но для MVP просто игнорируем ошибку
                # или пишем лог
                logger.error(f"Cannot delete message in chat {chat.id}. Missing permissions?")
            return  # Прерываем обработку сообщения

        return await handler(event, data)
