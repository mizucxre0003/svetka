from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime, timezone

from core.database import get_db
from models.log import Log, SystemLog

router = APIRouter(prefix="/logs", tags=["logs"])


class LogCreate(BaseModel):
    chat_id: int
    actor_telegram_user_id: Optional[int] = None
    target_telegram_user_id: Optional[int] = None
    action_type: str
    payload: Optional[dict] = None


class LogOut(BaseModel):
    id: int
    chat_id: int
    actor_user_id: Optional[int]
    target_user_id: Optional[int]
    action_type: str
    payload_json: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True


class SystemLogCreate(BaseModel):
    level: str  # error | warning | info
    service: str  # bot | backend | tma | db
    event_type: str
    payload: Optional[dict] = None


@router.post("/", status_code=201)
async def create_log(data: LogCreate, db: AsyncSession = Depends(get_db)):
    from models.user import User

    actor_id = None
    target_id = None

    if data.actor_telegram_user_id:
        r = await db.execute(select(User).where(User.telegram_user_id == data.actor_telegram_user_id))
        u = r.scalar_one_or_none()
        if u:
            actor_id = u.id

    if data.target_telegram_user_id:
        r = await db.execute(select(User).where(User.telegram_user_id == data.target_telegram_user_id))
        u = r.scalar_one_or_none()
        if u:
            target_id = u.id

    log = Log(
        chat_id=data.chat_id,
        actor_user_id=actor_id,
        target_user_id=target_id,
        action_type=data.action_type,
        payload_json=data.payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    return {"ok": True}


@router.get("/chat/{chat_id}", response_model=list[LogOut])
async def get_chat_logs(
    chat_id: int,
    action_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Log).where(Log.chat_id == chat_id)
    if action_type:
        q = q.where(Log.action_type == action_type)
    result = await db.execute(q.order_by(Log.created_at.desc()).offset(offset).limit(limit))
    return result.scalars().all()


@router.post("/system", status_code=201)
async def create_system_log(data: SystemLogCreate, db: AsyncSession = Depends(get_db)):
    log = SystemLog(
        level=data.level,
        service=data.service,
        event_type=data.event_type,
        payload_json=data.payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    return {"ok": True}


@router.get("/system", response_model=list[dict])
async def get_system_logs(
    level: Optional[str] = None,
    service: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(SystemLog)
    if level:
        q = q.where(SystemLog.level == level)
    if service:
        q = q.where(SystemLog.service == service)
    result = await db.execute(q.order_by(SystemLog.created_at.desc()).limit(limit))
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "level": l.level,
            "service": l.service,
            "event_type": l.event_type,
            "payload_json": l.payload_json,
            "created_at": l.created_at,
        }
        for l in logs
    ]
