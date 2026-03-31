"""
Обработка системных событий:
- Бот добавлен в группу
- Бот удалён из группы
- Бот получил/потерял права администратора
"""
from aiogram import Router
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.types import ChatMemberUpdated, Message
from aiogram.filters import Command
from core.backend import backend
from middlewares.chat_context import invalidate_chat
from loguru import logger

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def bot_added_to_chat(event: ChatMemberUpdated):
    """Бот добавлен в группу — регистрируем чат."""
    chat = event.chat
    user = event.from_user

    if chat.type not in ("group", "supergroup"):
        return

    logger.info(f"Bot added to chat {chat.id} '{chat.title}' by user {user.id}")

    # Регистрируем чат
    result = await backend.register_chat(
        telegram_chat_id=chat.id,
        title=chat.title or "Unknown",
        username=chat.username,
        member_count=0,
        telegram_user_id=user.id,
    )

    if result:
        # Инвалидируем кэш
        invalidate_chat(chat.id)

        # Логируем событие
        await backend.log_event(
            chat_id=result["id"],
            action_type="bot_added",
            actor_tg_id=user.id,
            payload={"chat_title": chat.title, "chat_id": chat.id},
        )

        # Приветствие при добавлении
        try:
            await event.bot.send_message(
                chat_id=chat.id,
                text=(
                    "👋 <b>Привет! Я Svetka.</b>\n\n"
                    "Я помогу управлять этой группой: модерация, защита, приветствия, правила и многое другое.\n\n"
                    "📱 Откройте настройки через команду /settings или прямо в Telegram Mini App."
                ),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Failed to send welcome to {chat.id}: {e}")
    else:
        logger.error(f"Failed to register chat {chat.id}")


@router.my_chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def bot_removed_from_chat(event: ChatMemberUpdated):
    """Бот удалён из группы."""
    chat = event.chat
    user = event.from_user

    logger.info(f"Bot removed from chat {chat.id} by user {user.id}")
    invalidate_chat(chat.id)

    # Пытаемся логировать (chat может быть уже зарегистрирован)
    # Получаем chat из backend через прямой запрос
    try:
        import httpx
        from core.config import get_settings
        settings = get_settings()
        async with httpx.AsyncClient(base_url=settings.BACKEND_URL) as c:
            r = await c.get("/api/v1/admin/groups", params={"search": str(chat.id)},
                           headers={"Authorization": f"Bearer {settings.__dict__.get('ADMIN_TOKEN', '')}"})
    except Exception:
        pass


@router.chat_member()
async def member_status_update(event: ChatMemberUpdated):
    """Изменение статуса участника (включая бота)."""
    pass
