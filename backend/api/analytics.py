from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta, date
from typing import Optional

from core.database import get_db
from models.metrics import DailyMetrics, CommandUsage
from models.punishment import Punishment
from models.warning import Warning
from models.log import Log

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/{chat_id}/summary")
async def get_chat_summary(chat_id: int, days: int = 7, db: AsyncSession = Depends(get_db)):
    """Агрегированная статистика по чату за N дней."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_date = since.date()

    # Суммы из daily_metrics
    metrics_result = await db.execute(
        select(
            func.sum(DailyMetrics.messages_count).label("messages"),
            func.sum(DailyMetrics.moderation_actions_count).label("moderation_actions"),
            func.sum(DailyMetrics.warnings_count).label("warnings"),
            func.sum(DailyMetrics.mutes_count).label("mutes"),
            func.sum(DailyMetrics.bans_count).label("bans"),
            func.sum(DailyMetrics.deleted_messages_count).label("deleted_messages"),
            func.sum(DailyMetrics.mini_app_opens_count).label("mini_app_opens"),
            func.sum(DailyMetrics.active_users_count).label("active_users"),
            func.sum(DailyMetrics.protection_triggers_count).label("protection_triggers"),
        ).where(
            DailyMetrics.chat_id == chat_id,
            DailyMetrics.date >= since_date,
        )
    )
    row = metrics_result.one()

    # Топ команд
    commands_result = await db.execute(
        select(CommandUsage.command, func.count().label("cnt"))
        .where(CommandUsage.chat_id == chat_id, CommandUsage.created_at >= since)
        .group_by(CommandUsage.command)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_commands = [{"command": r.command, "count": r.cnt} for r in commands_result]

    # Daily breakdown
    daily_result = await db.execute(
        select(DailyMetrics)
        .where(DailyMetrics.chat_id == chat_id, DailyMetrics.date >= since_date)
        .order_by(DailyMetrics.date)
    )
    daily = daily_result.scalars().all()

    return {
        "chat_id": chat_id,
        "period_days": days,
        "messages": row.messages or 0,
        "moderation_actions": row.moderation_actions or 0,
        "warnings": row.warnings or 0,
        "mutes": row.mutes or 0,
        "bans": row.bans or 0,
        "deleted_messages": row.deleted_messages or 0,
        "mini_app_opens": row.mini_app_opens or 0,
        "protection_triggers": row.protection_triggers or 0,
        "top_commands": top_commands,
        "daily": [
            {
                "date": str(d.date),
                "messages": d.messages_count,
                "active_users": d.active_users_count,
                "moderation_actions": d.moderation_actions_count,
            }
            for d in daily
        ],
    }


@router.post("/{chat_id}/increment")
async def increment_metric(
    chat_id: int,
    field: str,
    db: AsyncSession = Depends(get_db),
):
    """Атомарное увеличение метрики на 1 за сегодня."""
    allowed_fields = {
        "messages_count", "commands_count", "moderation_actions_count",
        "warnings_count", "mutes_count", "bans_count", "deleted_messages_count",
        "mini_app_opens_count", "active_users_count", "protection_triggers_count",
    }
    if field not in allowed_fields:
        return {"error": "Invalid field"}

    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(DailyMetrics).where(
            DailyMetrics.chat_id == chat_id,
            DailyMetrics.date == today,
        )
    )
    metrics = result.scalar_one_or_none()
    if not metrics:
        metrics = DailyMetrics(chat_id=chat_id, date=today)
        db.add(metrics)
        await db.flush()

    setattr(metrics, field, getattr(metrics, field) + 1)
    await db.commit()
    return {"ok": True}
