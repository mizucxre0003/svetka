from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from core.database import get_db
from models.trigger import Trigger

router = APIRouter(prefix="/triggers", tags=["triggers"])


class TriggerCreate(BaseModel):
    trigger_text: str
    response_text: str
    match_type: str = "contains"
    is_enabled: bool = True


class TriggerOut(BaseModel):
    id: int
    chat_id: int
    trigger_text: str
    response_text: str
    is_enabled: bool
    match_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TriggerPatch(BaseModel):
    trigger_text: Optional[str] = None
    response_text: Optional[str] = None
    match_type: Optional[str] = None
    is_enabled: Optional[bool] = None


@router.get("/{chat_id}", response_model=list[TriggerOut])
async def list_triggers(chat_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Trigger).where(Trigger.chat_id == chat_id).order_by(Trigger.created_at)
    )
    return result.scalars().all()


@router.post("/{chat_id}", response_model=TriggerOut, status_code=status.HTTP_201_CREATED)
async def create_trigger(chat_id: int, data: TriggerCreate, db: AsyncSession = Depends(get_db)):
    # Лимит для Free плана
    count_result = await db.execute(
        select(Trigger).where(Trigger.chat_id == chat_id)
    )
    existing = count_result.scalars().all()
    if len(existing) >= 50:
        raise HTTPException(status_code=400, detail="Trigger limit reached")

    trigger = Trigger(
        chat_id=chat_id,
        trigger_text=data.trigger_text,
        response_text=data.response_text,
        match_type=data.match_type,
        is_enabled=data.is_enabled,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(trigger)
    await db.commit()
    await db.refresh(trigger)
    return trigger


@router.patch("/{trigger_id}", response_model=TriggerOut)
async def update_trigger(
    trigger_id: int,
    patch: TriggerPatch,
    db: AsyncSession = Depends(get_db),
):
    trigger = await db.get(Trigger, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")

    update_data = patch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(trigger, key, value)
    trigger.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(trigger)
    return trigger


@router.delete("/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(trigger_id: int, db: AsyncSession = Depends(get_db)):
    trigger = await db.get(Trigger, trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail="Trigger not found")
    await db.delete(trigger)
    await db.commit()
