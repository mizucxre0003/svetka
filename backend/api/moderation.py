from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from core.database import get_db
from models.punishment import Punishment, PunishmentType, PunishmentStatus
from models.warning import Warning, WarningStatus
from models.user import User

router = APIRouter(prefix="/moderation", tags=["moderation"])


class PunishmentCreate(BaseModel):
    chat_id: int
    telegram_user_id: int
    issued_by_telegram_user_id: Optional[int] = None
    type: PunishmentType
    reason: Optional[str] = None
    duration_seconds: Optional[int] = None  # None = permanent


class WarningCreate(BaseModel):
    chat_id: int
    telegram_user_id: int
    issued_by_telegram_user_id: Optional[int] = None
    reason: Optional[str] = None


class PunishmentOut(BaseModel):
    id: int
    chat_id: int
    user_id: int
    type: str
    reason: Optional[str]
    starts_at: datetime
    expires_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


class WarningOut(BaseModel):
    id: int
    chat_id: int
    user_id: int
    reason: Optional[str]
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


async def get_or_create_user(db: AsyncSession, telegram_user_id: int) -> User:
    result = await db.execute(select(User).where(User.telegram_user_id == telegram_user_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_user_id=telegram_user_id, created_at=datetime.now(timezone.utc))
        db.add(user)
        await db.flush()
    return user


@router.post("/punish", response_model=PunishmentOut, status_code=status.HTTP_201_CREATED)
async def create_punishment(data: PunishmentCreate, db: AsyncSession = Depends(get_db)):
    user = await get_or_create_user(db, data.telegram_user_id)
    issuer = None
    if data.issued_by_telegram_user_id:
        issuer = await get_or_create_user(db, data.issued_by_telegram_user_id)

    starts = datetime.now(timezone.utc)
    expires = None
    if data.duration_seconds:
        from datetime import timedelta
        expires = starts + timedelta(seconds=data.duration_seconds)

    punishment = Punishment(
        chat_id=data.chat_id,
        user_id=user.id,
        issued_by_user_id=issuer.id if issuer else None,
        type=data.type,
        reason=data.reason,
        starts_at=starts,
        expires_at=expires,
    )
    db.add(punishment)
    await db.commit()
    await db.refresh(punishment)
    return punishment


@router.patch("/punish/{punishment_id}/revoke")
async def revoke_punishment(punishment_id: int, db: AsyncSession = Depends(get_db)):
    p = await db.get(Punishment, punishment_id)
    if not p:
        raise HTTPException(status_code=404, detail="Punishment not found")
    p.status = PunishmentStatus.revoked
    await db.commit()
    return {"ok": True}


@router.get("/punishments/{chat_id}", response_model=list[PunishmentOut])
async def list_punishments(
    chat_id: int,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    q = select(Punishment).where(Punishment.chat_id == chat_id)
    if active_only:
        q = q.where(Punishment.status == PunishmentStatus.active)
    result = await db.execute(q.order_by(Punishment.starts_at.desc()).limit(100))
    return result.scalars().all()


@router.post("/warn", response_model=WarningOut, status_code=status.HTTP_201_CREATED)
async def create_warning(data: WarningCreate, db: AsyncSession = Depends(get_db)):
    user = await get_or_create_user(db, data.telegram_user_id)
    issuer = None
    if data.issued_by_telegram_user_id:
        issuer = await get_or_create_user(db, data.issued_by_telegram_user_id)

    warning = Warning(
        chat_id=data.chat_id,
        user_id=user.id,
        issued_by_user_id=issuer.id if issuer else None,
        reason=data.reason,
        created_at=datetime.now(timezone.utc),
    )
    db.add(warning)
    await db.commit()
    await db.refresh(warning)
    return warning


@router.get("/warns/{chat_id}/{telegram_user_id}")
async def get_user_warns(chat_id: int, telegram_user_id: int, db: AsyncSession = Depends(get_db)):
    """Число активных варнов пользователя в чате."""
    result = await db.execute(
        select(User).where(User.telegram_user_id == telegram_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return {"count": 0, "warnings": []}

    warns_result = await db.execute(
        select(Warning)
        .where(Warning.chat_id == chat_id)
        .where(Warning.user_id == user.id)
        .where(Warning.status == WarningStatus.active)
    )
    warns = warns_result.scalars().all()
    return {"count": len(warns), "warnings": [{"id": w.id, "reason": w.reason, "created_at": w.created_at} for w in warns]}


@router.patch("/warn/{warning_id}/revoke")
async def revoke_warning(warning_id: int, db: AsyncSession = Depends(get_db)):
    w = await db.get(Warning, warning_id)
    if not w:
        raise HTTPException(status_code=404, detail="Warning not found")
    w.status = WarningStatus.revoked
    await db.commit()
    return {"ok": True}
