"""
Общие команды: /start, /help, /rules, /stats, /settings
"""
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from core.backend import backend
from core.cache import get_chat_settings_cached
from core.config import get_settings
from loguru import logger

router = Router()
settings = get_settings()


def mini_app_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    """Кнопка открытия Mini App."""
    mini_app_url = f"{settings.BOT_WEBHOOK_URL.replace('/webhook', '')}/mini-app?chat_id={chat_id}"
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⚙️ Открыть настройки", url=mini_app_url)
    ]])


@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "👋 <b>Добрый день! Я Svetka.</b>\n\n"
            "Я — современный менеджер Telegram-сообществ.\n\n"
            "🔹 Добавьте меня в группу как администратора\n"
            "🔹 Откройте Mini App для быстрой настройки\n"
            "🔹 Управляйте модерацией, защитой, приветствиями и многим другим\n\n"
            "Используйте /help для списка команд.",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "👋 <b>Svetka активна в этой группе.</b>\n"
            "Используйте /help для списка команд.",
            parse_mode="HTML",
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Svetka — доступные команды:</b>\n\n"
        "<b>Общие:</b>\n"
        "/start — запуск бота\n"
        "/help — эта справка\n"
        "/rules — правила группы\n"
        "/stats — статистика чата\n"
        "/settings — открыть настройки\n\n"
        "<b>Модерация (только для админов):</b>\n"
        "/ban — забанить пользователя\n"
        "/mute — замутить пользователя\n"
        "/unmute — снять мут\n"
        "/warn — выдать предупреждение\n"
        "/unwarn — снять предупреждение\n\n"
        "💡 Полное управление доступно через Mini App."
    )
    await message.answer(text, parse_mode="HTML")

    # Логируем использование команды
    chat_db = None
    if message.chat.type in ("group", "supergroup"):
        # best effort
        try:
            from core.backend import backend as b
            pass
        except Exception:
            pass


@router.message(Command("rules"))
async def cmd_rules(message: Message, chat_db: dict | None = None):
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах.")
        return

    if not chat_db:
        await message.answer("❌ Чат не зарегистрирован в системе.")
        return

    cs = await get_chat_settings_cached(chat_db["id"], backend)
    if not cs or not cs.get("rules_enabled"):
        await message.answer("📋 Правила ещё не настроены. Администратор может добавить их через /settings.")
        return

    rules_text = cs.get("rules_text") or "Правила ещё не заданы."
    await message.answer(f"📋 <b>Правила группы:</b>\n\n{rules_text}", parse_mode="HTML")

    await backend.log_event(
        chat_id=chat_db["id"],
        action_type="rules_requested",
        actor_tg_id=message.from_user.id if message.from_user else None,
    )
    await backend.increment_metric(chat_db["id"], "commands_count")


@router.message(Command("stats"))
async def cmd_stats(message: Message, chat_db: dict | None = None):
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах.")
        return

    if not chat_db:
        await message.answer("❌ Чат не зарегистрирован в системе.")
        return

    summary = await backend.get_client()
    try:
        from core.config import get_settings as gs
        s = gs()
        import httpx
        async with httpx.AsyncClient(base_url=s.BACKEND_URL) as c:
            r = await c.get(f"/api/v1/analytics/{chat_db['id']}/summary", params={"days": 7})
            data = r.json() if r.is_success else {}
    except Exception:
        data = {}

    text = (
        f"📊 <b>Статистика за 7 дней:</b>\n\n"
        f"💬 Сообщений: {data.get('messages', 0)}\n"
        f"⚠️ Нарушений: {data.get('moderation_actions', 0)}\n"
        f"🔇 Предупреждений: {data.get('warnings', 0)}\n"
        f"🚫 Мутов: {data.get('mutes', 0)}\n"
        f"🔨 Банов: {data.get('bans', 0)}\n"
        f"🛡️ Срабатываний защиты: {data.get('protection_triggers', 0)}\n"
    )
    await message.answer(text, parse_mode="HTML")
    await backend.increment_metric(chat_db["id"], "commands_count")


@router.message(Command("settings"))
async def cmd_settings(message: Message, chat_db: dict | None = None):
    if message.chat.type == "private":
        await message.answer(
            "⚙️ <b>Настройки Svetka</b>\n\n"
            "Откройте Mini App для управления вашими группами:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⚙️ Открыть Mini App", web_app={"url": "https://example.com"})
            ]]),
            parse_mode="HTML",
        )
        return

    if not chat_db:
        await message.answer("❌ Сначала зарегистрируйте чат: добавьте бота и выдайте ему права администратора.")
        return

    await message.answer(
        "⚙️ <b>Управление группой</b>\n\nОткройте Mini App для полного управления настройками:",
        parse_mode="HTML",
    )
    await backend.increment_metric(chat_db["id"], "mini_app_opens_count")
