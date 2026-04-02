"""
Фильтры защиты чата:
- Антиссылки
- Стоп-слова
- Фильтр капса
- Фильтр повторов
"""
import re
import time
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from typing import Callable, Any, Awaitable
from core.cache import get_chat_settings_cached, get_redis
from core.backend import backend
from loguru import logger

URL_PATTERN = re.compile(
    r"(https?://|t\.me/|@\w+|www\.|bit\.ly|tinyurl|vk\.com|instagram\.com|youtube\.com)",
    re.IGNORECASE,
)


async def apply_protection_action(message: Message, action: str, chat_db: dict, settings: dict, reason: str):
    """Применить действие защитного фильтра."""
    await backend.increment_metric(chat_db["id"], "protection_triggers_count")
    await backend.log_event(
        chat_id=chat_db["id"],
        action_type=f"protection_{reason}",
        actor_tg_id=message.from_user.id if message.from_user else None,
        payload={"action": action},
    )

    try:
        await message.delete()
        await backend.increment_metric(chat_db["id"], "deleted_messages_count")
    except Exception:
        pass

    if action == "warn":
        warn_data = await backend.warn(
            chat_id=chat_db["id"],
            telegram_user_id=message.from_user.id,
            issued_by=None,
            reason=reason,
        )
        if warn_data:
            warns = await backend.get_warns(chat_db["id"], message.from_user.id)
            warn_limit = settings.get("default_warn_limit", 3)
            await message.answer(
                f"⚠️ {message.from_user.mention_html()}, предупреждение {warns['count']}/{warn_limit}.",
                parse_mode="HTML",
            )
            if warns["count"] >= warn_limit:
                await _auto_punish(message, chat_db, settings)

    elif action in ("mute", "delete_and_mute"):
        duration = settings.get("default_mute_duration", 3600)
        until = int(time.time()) + duration
        try:
            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions={"can_send_messages": False},
                until_date=until,
            )
        except Exception as e:
            logger.warning(f"Mute failed: {e}")


async def _auto_punish(message: Message, chat_db: dict, settings: dict):
    """Автоматическое наказание при достижении лимита варнов."""
    action = settings.get("warn_limit_action", "mute")
    duration = settings.get("default_mute_duration", 3600)
    if action == "ban":
        try:
            await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
            await backend.punish(chat_db["id"], message.from_user.id, None, "ban", "warn_limit_reached")
            await backend.increment_metric(chat_db["id"], "bans_count")
        except Exception as e:
            logger.warning(f"Auto-ban failed: {e}")
    else:
        until = int(time.time()) + duration
        try:
            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions={"can_send_messages": False},
                until_date=until,
            )
            await backend.punish(chat_db["id"], message.from_user.id, None, "mute",
                                  "warn_limit_reached", duration)
            await backend.increment_metric(chat_db["id"], "mutes_count")
        except Exception as e:
            logger.warning(f"Auto-mute failed: {e}")

    await message.answer(
        f"🔨 {message.from_user.mention_html()}, достигнут лимит предупреждений.",
        parse_mode="HTML",
    )


class ProtectionMiddleware(BaseMiddleware):
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
        if not settings:
            return await handler(event, data)

        text = event.text or event.caption or ""

        # ── Антиссылки ──────────────────────────────────────────────────────────
        if settings.get("anti_links_enabled") and URL_PATTERN.search(text):
            action = settings.get("anti_links_action", "delete")
            await apply_protection_action(event, action, chat_db, settings, "anti_links")
            return

        # ── Стоп-слова ──────────────────────────────────────────────────────────
        if settings.get("stop_words_enabled"):
            stop_words = settings.get("stop_words_list") or []
            text_lower = text.lower()
            for word in stop_words:
                if word.lower() in text_lower:
                    action = settings.get("stop_words_action", "delete")
                    await apply_protection_action(event, action, chat_db, settings, "stop_word")
                    return

        # ── Фильтр капса ────────────────────────────────────────────────────────
        if settings.get("caps_filter_enabled") and text:
            min_len = settings.get("caps_filter_min_length", 10)
            threshold = settings.get("caps_filter_threshold", 0.7)
            if len(text) >= min_len:
                upper_count = sum(1 for c in text if c.isupper())
                alpha_count = sum(1 for c in text if c.isalpha())
                if alpha_count > 0 and upper_count / alpha_count >= threshold:
                    await apply_protection_action(event, "delete", chat_db, settings, "caps_filter")
                    return

        # ── Фильтр повторов ─────────────────────────────────────────────────────
        if settings.get("repeat_filter_enabled") and text:
            r = await get_redis()
            key = f"repeat:{event.chat.id}:{event.from_user.id}"
            prev = await r.get(key)
            await r.setex(key, 300, text[:200])
            if prev and prev == text[:200]:
                await apply_protection_action(event, "delete", chat_db, settings, "repeat_filter")
                return

        return await handler(event, data)
