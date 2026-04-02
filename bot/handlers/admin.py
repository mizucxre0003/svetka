"""
Модерационные команды: /ban, /mute, /unmute, /warn, /unwarn
Только для администраторов с соответствующими правами.
"""
import time
import re
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from core.backend import backend
from core.cache import get_chat_settings_cached
from loguru import logger

router = Router()


def parse_duration(text: str | None) -> int | None:
    """Парсит '1h', '30m', '1d' в секунды. None = permanent."""
    if not text:
        return None
    match = re.match(r"^(\d+)([smhd])$", text.lower())
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    return {"s": val, "m": val * 60, "h": val * 3600, "d": val * 86400}[unit]


async def check_admin(message: Message) -> bool:
    """Проверка, является ли отправитель администратором."""
    if message.chat.type not in ("group", "supergroup"):
        return False
    try:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def get_target(message: Message) -> tuple[int | None, str, str | None]:
    """
    Получить цель команды.
    Возращает: (target_id, mention_html, error_message)
    """
    reply = message.reply_to_message
    if reply:
        if reply.from_user:
            return reply.from_user.id, reply.from_user.mention_html(), None
        elif reply.sender_chat:
            return None, "", "❌ Невозможно применить к каналу или анонимной группе."
        else:
            return None, "", "❌ Это сообщение недоступно для бота (возможно оно было отправлено до выдачи прав). Ответьте на более свежее сообщение."

    if message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" and ent.user:
                return ent.user.id, ent.user.mention_html(), None

    args = (message.text or message.caption or "").split()
    if len(args) > 1:
        # Проверяем, не передан ли ID напрямую (ID обычно длинные)
        if args[1].lstrip('-').isdigit() and len(args[1]) > 5:
            return int(args[1]), f'<a href="tg://user?id={args[1]}">Пользователь</a>', None
        elif args[1].startswith("@"):
            return None, "", "❌ Бот не может применять команды к @username без ответа на сообщение. Пожалуйста, ответьте на сообщение (Reply) пользователя."

    return None, "", "❌ Ответьте на сообщение пользователя или укажите его ID."


@router.message(Command("ban"))
async def cmd_ban(message: Message, chat_db: dict | None = None):
    if not await check_admin(message):
        return

    target_id, mention, err = await get_target(message)
    if not target_id:
        await message.reply(err or "❌ Цель не найдена.")
        return

    # Нельзя банить ботов/админов
    try:
        target_member = await message.bot.get_chat_member(message.chat.id, target_id)
        if target_member.status in ("administrator", "creator"):
            await message.reply("❌ Нельзя забанить администратора.")
            return
    except Exception:
        pass

    args = (message.text or message.caption or "").split()
    reason = " ".join(args[1:]) if len(args) > 1 else None

    try:
        await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=target_id)
    except Exception as e:
        await message.reply(f"❌ Не удалось забанить: {e}")
        return

    if chat_db:
        await backend.punish(
            chat_id=chat_db["id"],
            telegram_user_id=target_id,
            issued_by=message.from_user.id,
            ptype="ban",
            reason=reason,
        )
        await backend.log_event(
            chat_id=chat_db["id"],
            action_type="ban",
            actor_tg_id=message.from_user.id,
            target_tg_id=target_id,
            payload={"reason": reason},
        )
        await backend.increment_metric(chat_db["id"], "bans_count")
        await backend.increment_metric(chat_db["id"], "moderation_actions_count")

    reason_text = f"\n📝 Причина: {reason}" if reason else ""
    await message.reply(
        f"🔨 {mention} был забанен.{reason_text}",
        parse_mode="HTML",
    )
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("mute"))
async def cmd_mute(message: Message, chat_db: dict | None = None):
    if not await check_admin(message):
        return

    target_id, mention, err = await get_target(message)
    if not target_id:
        await message.reply(err or "❌ Цель не найдена.")
        return

    args = (message.text or message.caption or "").split()
    
    # Сдвигаем индексы, если первым аргументом был ID пользователя
    offset = 1
    if len(args) > 1 and args[1].lstrip('-').isdigit() and len(args[1]) > 5:
        offset = 2

    duration_str = args[offset] if len(args) > offset else None
    reason = " ".join(args[offset+1:]) if len(args) > offset + 1 else None

    duration = parse_duration(duration_str)
    if duration_str and not duration:
        reason = " ".join(args[offset:])
        duration = 3600  # default 1h

    final_duration = duration or 3600
    until = int(time.time()) + final_duration

    is_soft_mute = False
    try:
        await message.bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions={"can_send_messages": False},
            until_date=until,
        )
    except Exception as e:
        err = str(e).lower()
        if "participant_id_invalid" in err or "not_supergroup" in err or "can't restrict" in err or "chat_not_modified" in err or "not enough rights" in err:
            is_soft_mute = True
        else:
            await message.reply(f"❌ Не удалось замутить: {e}")
            return

    if chat_db:
        await backend.punish(
            chat_id=chat_db["id"],
            telegram_user_id=target_id,
            issued_by=message.from_user.id,
            ptype="mute",
            reason=reason,
            duration=final_duration,
        )
        if is_soft_mute:
            from core.cache import set_soft_mute
            await set_soft_mute(chat_db["id"], target_id, final_duration)

        await backend.log_event(
            chat_id=chat_db["id"],
            action_type="mute",
            actor_tg_id=message.from_user.id,
            target_tg_id=target_id,
            payload={"duration": final_duration, "reason": reason, "is_soft": is_soft_mute},
        )
        await backend.increment_metric(chat_db["id"], "mutes_count")
        await backend.increment_metric(chat_db["id"], "moderation_actions_count")

    duration_text = f" на {duration_str}" if duration_str else " на 1 час"
    reason_text = f"\n📝 Причина: {reason}" if reason else ""
    
    if is_soft_mute:
        dur_text = duration_str if duration_str else "1 час"
        await message.reply(
            f"⚠️ В этой группе не поддерживается стандартный мут. Я буду автоматически удалять все сообщения пользователя {mention} следующие {dur_text}.{reason_text}",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            f"🔇 {mention} замучен{duration_text}.{reason_text}",
            parse_mode="HTML",
        )

    # Schedule unmute message
    import asyncio
    async def schedule_unmute_notification():
        await asyncio.sleep(final_duration)
        try:
            await message.bot.send_message(
                message.chat.id, 
                f"🔊 Время мута истекло. Пользователь {mention} размучен.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    asyncio.create_task(schedule_unmute_notification())

    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("unmute"))
async def cmd_unmute(message: Message, chat_db: dict | None = None):
    if not await check_admin(message):
        return

    target_id, mention, err = await get_target(message)
    if not target_id:
        await message.reply(err or "❌ Цель не найдена.")
        return

    is_soft_unmute = False
    try:
        await message.bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
            },
        )
    except Exception as e:
        err = str(e).lower()
        if "participant_id_invalid" in err or "not_supergroup" in err or "can't restrict" in err or "chat_not_modified" in err or "not enough rights" in err:
            is_soft_unmute = True
        else:
            await message.reply(f"❌ Не удалось снять мут: {e}")
            return

    if chat_db:
        from core.cache import clear_soft_mute
        await clear_soft_mute(chat_db["id"], target_id)
        
        await backend.log_event(
            chat_id=chat_db["id"],
            action_type="unmute",
            actor_tg_id=message.from_user.id,
            target_tg_id=target_id,
        )
        await backend.increment_metric(chat_db["id"], "moderation_actions_count")

    await message.reply(f"🔊 {mention} размучен администратором.", parse_mode="HTML")
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("warn"))
async def cmd_warn(message: Message, chat_db: dict | None = None):
    if not await check_admin(message):
        return

    target_id, mention, err = await get_target(message)
    if not target_id:
        await message.reply(err or "❌ Цель не найдена.")
        return

    args = (message.text or message.caption or "").split()
    reason = " ".join(args[1:]) if len(args) > 1 else None

    if not chat_db:
        await message.reply("❌ Чат не зарегистрирован.")
        return

    cs = await get_chat_settings_cached(chat_db["id"], backend)
    warn_limit = cs.get("default_warn_limit", 3) if cs else 3

    await backend.warn(
        chat_id=chat_db["id"],
        telegram_user_id=target_id,
        issued_by=message.from_user.id,
        reason=reason,
    )

    warns = await backend.get_warns(chat_db["id"], target_id)
    count = warns["count"]

    reason_text = f"\n📝 Причина: {reason}" if reason else ""
    await message.reply(
        f"⚠️ {mention} получает предупреждение {count}/{warn_limit}.{reason_text}",
        parse_mode="HTML",
    )

    await backend.log_event(
        chat_id=chat_db["id"],
        action_type="warn",
        actor_tg_id=message.from_user.id,
        target_tg_id=target_id,
        payload={"count": count, "limit": warn_limit, "reason": reason},
    )
    await backend.increment_metric(chat_db["id"], "warnings_count")
    await backend.increment_metric(chat_db["id"], "moderation_actions_count")

    # Автонаказание при достижении лимита
    if count >= warn_limit and cs:
        action = cs.get("warn_limit_action", "mute")
        duration = cs.get("default_mute_duration", 3600)
        if action == "ban":
            try:
                await message.bot.ban_chat_member(chat_id=message.chat.id, user_id=target_id)
                await backend.punish(chat_db["id"], target_id, message.from_user.id,
                                     "ban", "warn_limit_reached")
                await backend.increment_metric(chat_db["id"], "bans_count")
                await message.answer(
                    f"🔨 {mention}: достигнут лимит предупреждений. Бан.",
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Auto-ban failed: {e}")
        else:
            until = int(time.time()) + duration
            try:
                await message.bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=target_id,
                    permissions={"can_send_messages": False},
                    until_date=until,
                )
                await backend.punish(chat_db["id"], target_id, message.from_user.id,
                                     "mute", "warn_limit_reached", duration)
                await backend.increment_metric(chat_db["id"], "mutes_count")
                await message.answer(
                    f"🔇 {mention}: достигнут лимит предупреждений. Мут.",
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Auto-mute failed: {e}")

    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("unwarn"))
async def cmd_unwarn(message: Message, chat_db: dict | None = None):
    if not await check_admin(message):
        return

    target_id, mention, err = await get_target(message)
    if not target_id or not chat_db:
        await message.reply(err or "❌ Цель не найдена.")
        return

    warns = await backend.get_warns(chat_db["id"], target_id)
    if warns["count"] == 0:
        await message.reply(f"ℹ️ У {mention} нет активных предупреждений.", parse_mode="HTML")
        return

    # Снимаем последнее предупреждение
    last_warn = warns["warnings"][-1]
    await backend.revoke_warn(last_warn["id"])

    await message.reply(
        f"✅ Предупреждение снято с {mention}. Осталось: {warns['count'] - 1}.",
        parse_mode="HTML",
    )
    await backend.log_event(
        chat_id=chat_db["id"],
        action_type="unwarn",
        actor_tg_id=message.from_user.id,
        target_tg_id=target_id,
    )
    try:
        await message.delete()
    except Exception:
        pass
