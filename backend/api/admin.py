from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

from core.database import get_db
from core.auth import require_admin
from models.chat import Chat, ChatStatus, TariffPlan
from models.user import User
from models.metrics import DailyMetrics
from models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from models.log import Log, SystemLog
from models.internal_note import InternalNote

router = APIRouter(prefix="/admin", tags=["admin"])


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard", dependencies=[Depends(require_admin)])
async def admin_dashboard(db: AsyncSession = Depends(get_db)):
    """Главная страница Super Admin: ключевые метрики."""
    total_chats = await db.scalar(select(func.count(Chat.id)))
    active_chats = await db.scalar(select(func.count(Chat.id)).where(Chat.status == ChatStatus.active))

    # Новые за 24h, 7d, 30d
    now = datetime.now(timezone.utc)
    new_today = await db.scalar(
        select(func.count(Chat.id)).where(Chat.connected_at >= now - timedelta(days=1))
    )
    new_week = await db.scalar(
        select(func.count(Chat.id)).where(Chat.connected_at >= now - timedelta(days=7))
    )
    new_month = await db.scalar(
        select(func.count(Chat.id)).where(Chat.connected_at >= now - timedelta(days=30))
    )

    # DAU / WAU / MAU (активные чаты)
    dau = await db.scalar(
        select(func.count(Chat.id)).where(Chat.last_activity_at >= now - timedelta(days=1))
    )
    wau = await db.scalar(
        select(func.count(Chat.id)).where(Chat.last_activity_at >= now - timedelta(days=7))
    )
    mau = await db.scalar(
        select(func.count(Chat.id)).where(Chat.last_activity_at >= now - timedelta(days=30))
    )

    # Тарифы
    free_count = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.plan == SubscriptionPlan.free)
    )
    pro_count = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.plan == SubscriptionPlan.pro)
    )
    trial_count = await db.scalar(
        select(func.count(Subscription.id)).where(Subscription.plan == SubscriptionPlan.trial)
    )

    # Сообщения / модерационные действия за 7 дней
    since_date = (now - timedelta(days=7)).date()
    totals = await db.execute(
        select(
            func.sum(DailyMetrics.messages_count),
            func.sum(DailyMetrics.moderation_actions_count),
            func.sum(DailyMetrics.mini_app_opens_count),
            func.sum(DailyMetrics.protection_triggers_count),
        ).where(DailyMetrics.date >= since_date)
    )
    t = totals.one()

    # Growth chart (последние 30 дней)
    from models.chat import Chat as ChatModel
    growth = []
    for i in range(29, -1, -1):
        d = (now - timedelta(days=i)).date()
        cnt = await db.scalar(
            select(func.count(Chat.id)).where(
                func.date(Chat.connected_at) == d
            )
        )
        growth.append({"date": str(d), "new_chats": cnt or 0})

    return {
        "total_chats": total_chats or 0,
        "active_chats": active_chats or 0,
        "new_today": new_today or 0,
        "new_week": new_week or 0,
        "new_month": new_month or 0,
        "dau": dau or 0,
        "wau": wau or 0,
        "mau": mau or 0,
        "free_count": free_count or 0,
        "pro_count": pro_count or 0,
        "trial_count": trial_count or 0,
        "messages_7d": t[0] or 0,
        "moderation_actions_7d": t[1] or 0,
        "mini_app_opens_7d": t[2] or 0,
        "protection_triggers_7d": t[3] or 0,
        "growth_chart": growth,
    }


# ─── Groups List ──────────────────────────────────────────────────────────────

@router.get("/groups", dependencies=[Depends(require_admin)])
async def admin_list_groups(
    status: Optional[str] = None,
    tariff: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Chat)
    if status:
        q = q.where(Chat.status == status)
    if tariff:
        q = q.where(Chat.tariff == tariff)
    if search:
        q = q.where(Chat.title.ilike(f"%{search}%"))
    result = await db.execute(q.order_by(Chat.connected_at.desc()).offset(offset).limit(limit))
    chats = result.scalars().all()

    total = await db.scalar(select(func.count(Chat.id)))

    return {
        "total": total,
        "items": [
            {
                "id": c.id,
                "telegram_chat_id": c.telegram_chat_id,
                "title": c.title,
                "username": c.username,
                "connected_at": c.connected_at,
                "last_activity_at": c.last_activity_at,
                "member_count": c.member_count,
                "tariff": c.tariff,
                "status": c.status,
            }
            for c in chats
        ],
    }


# ─── Group Card ───────────────────────────────────────────────────────────────

@router.get("/groups/{chat_id}", dependencies=[Depends(require_admin)])
async def admin_get_group(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Логи
    logs_result = await db.execute(
        select(Log).where(Log.chat_id == chat_id).order_by(Log.created_at.desc()).limit(20)
    )
    logs = logs_result.scalars().all()

    # Метрики
    since = (datetime.now(timezone.utc) - timedelta(days=30)).date()
    metrics_result = await db.execute(
        select(
            func.sum(DailyMetrics.messages_count),
            func.sum(DailyMetrics.bans_count),
            func.sum(DailyMetrics.mutes_count),
            func.sum(DailyMetrics.warnings_count),
            func.sum(DailyMetrics.mini_app_opens_count),
        ).where(DailyMetrics.chat_id == chat_id, DailyMetrics.date >= since)
    )
    m = metrics_result.one()

    # Заметки
    notes_result = await db.execute(
        select(InternalNote).where(InternalNote.chat_id == chat_id).order_by(InternalNote.created_at.desc())
    )
    notes = notes_result.scalars().all()

    return {
        "chat": {
            "id": chat.id,
            "telegram_chat_id": chat.telegram_chat_id,
            "title": chat.title,
            "username": chat.username,
            "connected_at": chat.connected_at,
            "last_activity_at": chat.last_activity_at,
            "member_count": chat.member_count,
            "tariff": chat.tariff,
            "status": chat.status,
        },
        "metrics_30d": {
            "messages": m[0] or 0,
            "bans": m[1] or 0,
            "mutes": m[2] or 0,
            "warnings": m[3] or 0,
            "mini_app_opens": m[4] or 0,
        },
        "recent_logs": [
            {"action_type": l.action_type, "created_at": l.created_at, "payload": l.payload_json}
            for l in logs
        ],
        "notes": [
            {"id": n.id, "text": n.text, "created_by": n.created_by, "created_at": n.created_at}
            for n in notes
        ],
    }


# ─── Notes ────────────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    text: str


@router.post("/groups/{chat_id}/notes", dependencies=[Depends(require_admin)])
async def add_note(chat_id: int, data: NoteCreate, db: AsyncSession = Depends(get_db)):
    note = InternalNote(
        chat_id=chat_id,
        created_by="admin",
        text=data.text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(note)
    await db.commit()
    return {"ok": True}


# ─── Tariffs ──────────────────────────────────────────────────────────────────

class TariffUpdate(BaseModel):
    plan: str  # free | trial | pro
    duration_days: Optional[int] = None  # None = permanent


@router.patch("/groups/{chat_id}/tariff", dependencies=[Depends(require_admin)])
async def update_tariff(chat_id: int, data: TariffUpdate, db: AsyncSession = Depends(get_db)):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat.tariff = data.plan

    sub = await db.scalar(select(Subscription).where(Subscription.chat_id == chat_id))
    if not sub:
        sub = Subscription(chat_id=chat_id, started_at=datetime.now(timezone.utc))
        db.add(sub)

    sub.plan = SubscriptionPlan(data.plan)
    sub.status = SubscriptionStatus.active
    sub.started_at = datetime.now(timezone.utc)
    sub.is_trial = data.plan == "trial"
    sub.granted_by = "admin"
    if data.duration_days:
        sub.expires_at = datetime.now(timezone.utc) + timedelta(days=data.duration_days)
    else:
        sub.expires_at = None

    await db.commit()
    return {"ok": True}


# ─── Block / Unblock ──────────────────────────────────────────────────────────

@router.patch("/groups/{chat_id}/block", dependencies=[Depends(require_admin)])
async def block_group(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404)
    chat.status = ChatStatus.blocked
    await db.commit()
    return {"ok": True}


@router.patch("/groups/{chat_id}/unblock", dependencies=[Depends(require_admin)])
async def unblock_group(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404)
    chat.status = ChatStatus.active
    await db.commit()
    return {"ok": True}


# ─── Usage Analytics ──────────────────────────────────────────────────────────

@router.get("/analytics/usage", dependencies=[Depends(require_admin)])
async def usage_analytics(db: AsyncSession = Depends(get_db)):
    """Агрегированная аналитика: какие функции используются."""
    from models.chat import ChatSettings

    total_chats = await db.scalar(select(func.count(Chat.id))) or 0
    if total_chats == 0:
        return {}

    s = await db.execute(
        select(
            func.count().filter(ChatSettings.welcome_enabled == True).label("welcome"),
            func.count().filter(ChatSettings.anti_flood_enabled == True).label("anti_flood"),
            func.count().filter(ChatSettings.anti_links_enabled == True).label("anti_links"),
            func.count().filter(ChatSettings.stop_words_enabled == True).label("stop_words"),
            func.count().filter(ChatSettings.caps_filter_enabled == True).label("caps_filter"),
            func.count().filter(ChatSettings.triggers_enabled == True).label("triggers"),
            func.count().filter(ChatSettings.rules_enabled == True).label("rules"),
        )
    )
    row = s.one()

    def pct(v):
        return round((v or 0) / total_chats * 100, 1)

    return {
        "total_chats": total_chats,
        "welcome_enabled": {"count": row.welcome or 0, "pct": pct(row.welcome)},
        "anti_flood_enabled": {"count": row.anti_flood or 0, "pct": pct(row.anti_flood)},
        "anti_links_enabled": {"count": row.anti_links or 0, "pct": pct(row.anti_links)},
        "stop_words_enabled": {"count": row.stop_words or 0, "pct": pct(row.stop_words)},
        "caps_filter_enabled": {"count": row.caps_filter or 0, "pct": pct(row.caps_filter)},
        "triggers_enabled": {"count": row.triggers or 0, "pct": pct(row.triggers)},
        "rules_enabled": {"count": row.rules or 0, "pct": pct(row.rules)},
    }


# ─── Funnel ───────────────────────────────────────────────────────────────────

@router.get("/analytics/funnel", dependencies=[Depends(require_admin)])
async def activation_funnel(db: AsyncSession = Depends(get_db)):
    """Воронка активации групп."""
    from models.chat import ChatSettings

    step1 = await db.scalar(select(func.count(Chat.id))) or 0

    # Шаг 2: Настройки созданы (бот получил права и зарегистрировал группу)
    step2 = step1  # все зарегистрированные

    # Шаг 3: Открыт Mini App (mini_app_opens_count > 0)
    step3_q = await db.execute(
        select(func.count(func.distinct(DailyMetrics.chat_id)))
        .where(DailyMetrics.mini_app_opens_count > 0)
    )
    step3 = step3_q.scalar() or 0

    # Шаг 4: Включено приветствие
    step4 = await db.scalar(
        select(func.count()).select_from(ChatSettings).where(ChatSettings.welcome_enabled == True)
    ) or 0

    # Шаг 5: Включена защита (антифлуд или антиссылки)
    step5 = await db.scalar(
        select(func.count()).select_from(ChatSettings).where(
            (ChatSettings.anti_flood_enabled == True) | (ChatSettings.anti_links_enabled == True)
        )
    ) or 0

    # Шаг 6: Настроены правила
    step6 = await db.scalar(
        select(func.count()).select_from(ChatSettings).where(ChatSettings.rules_enabled == True)
    ) or 0

    # Шаг 7: Включены триггеры
    step7 = await db.scalar(
        select(func.count()).select_from(ChatSettings).where(ChatSettings.triggers_enabled == True)
    ) or 0

    # Шаг 8: Активна (last_activity < 7 дней)
    step8 = await db.scalar(
        select(func.count(Chat.id)).where(
            Chat.last_activity_at >= datetime.now(timezone.utc) - timedelta(days=7)
        )
    ) or 0

    def pct(v, base=step1):
        if base == 0:
            return 0
        return round(v / base * 100, 1)

    return [
        {"step": 1, "label": "Бот добавлен", "count": step1, "pct": 100},
        {"step": 2, "label": "Группа зарегистрирована", "count": step2, "pct": pct(step2)},
        {"step": 3, "label": "Открыт Mini App", "count": step3, "pct": pct(step3)},
        {"step": 4, "label": "Включено приветствие", "count": step4, "pct": pct(step4)},
        {"step": 5, "label": "Включена защита", "count": step5, "pct": pct(step5)},
        {"step": 6, "label": "Настроены правила", "count": step6, "pct": pct(step6)},
        {"step": 7, "label": "Включены триггеры", "count": step7, "pct": pct(step7)},
        {"step": 8, "label": "Группа активна (7д)", "count": step8, "pct": pct(step8)},
    ]
