from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, Any

from core.database import get_db
from models.chat import ChatSettings

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsOut(BaseModel):
    chat_id: int
    welcome_enabled: bool
    welcome_text: Optional[str]
    welcome_buttons: Optional[Any]
    welcome_delete_after: Optional[int]
    rules_enabled: bool
    rules_text: Optional[str]
    anti_flood_enabled: bool
    anti_flood_limit: int
    anti_flood_interval: int
    anti_flood_action: str
    anti_links_enabled: bool
    anti_links_action: str
    stop_words_enabled: bool
    stop_words_list: Optional[Any]
    stop_words_action: str
    repeat_filter_enabled: bool
    repeat_filter_sensitivity: float
    caps_filter_enabled: bool
    caps_filter_threshold: float
    caps_filter_min_length: int
    triggers_enabled: bool
    logs_enabled: bool
    default_warn_limit: int
    warn_limit_action: str
    default_mute_duration: int

    class Config:
        from_attributes = True


class SettingsPatch(BaseModel):
    welcome_enabled: Optional[bool] = None
    welcome_text: Optional[str] = None
    welcome_buttons: Optional[Any] = None
    welcome_delete_after: Optional[int] = None
    rules_enabled: Optional[bool] = None
    rules_text: Optional[str] = None
    anti_flood_enabled: Optional[bool] = None
    anti_flood_limit: Optional[int] = None
    anti_flood_interval: Optional[int] = None
    anti_flood_action: Optional[str] = None
    anti_links_enabled: Optional[bool] = None
    anti_links_action: Optional[str] = None
    stop_words_enabled: Optional[bool] = None
    stop_words_list: Optional[list] = None
    stop_words_action: Optional[str] = None
    repeat_filter_enabled: Optional[bool] = None
    repeat_filter_sensitivity: Optional[float] = None
    caps_filter_enabled: Optional[bool] = None
    caps_filter_threshold: Optional[float] = None
    caps_filter_min_length: Optional[int] = None
    triggers_enabled: Optional[bool] = None
    logs_enabled: Optional[bool] = None
    default_warn_limit: Optional[int] = None
    warn_limit_action: Optional[str] = None
    default_mute_duration: Optional[int] = None


@router.get("/{chat_id}", response_model=SettingsOut)
async def get_settings(chat_id: int, db: AsyncSession = Depends(get_db)):
    settings = await db.get(ChatSettings, chat_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@router.patch("/{chat_id}", response_model=SettingsOut)
async def update_settings(
    chat_id: int,
    patch: SettingsPatch,
    db: AsyncSession = Depends(get_db),
):
    settings = await db.get(ChatSettings, chat_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    update_data = patch.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)

    await db.commit()
    await db.refresh(settings)
    return settings
