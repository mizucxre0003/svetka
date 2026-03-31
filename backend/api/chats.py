from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from core.database import get_db
from models.chat import Chat, ChatSettings, ChatStatus, TariffPlan
from models.user import User

router = APIRouter(prefix="/chats", tags=["chats"])


class ChatCreate(BaseModel):
    telegram_chat_id: int
    title: str
    username: Optional[str] = None
    member_count: int = 0


class ChatOut(BaseModel):
    id: int
    telegram_chat_id: int
    title: str
    username: Optional[str]
    connected_at: datetime
    last_activity_at: Optional[datetime]
    member_count: int
    tariff: str
    status: str

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ChatOut])
async def list_chats(
    telegram_user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Список чатов, доступных пользователю."""
    from models.chat import ChatMember
    result = await db.execute(
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .join(User, User.id == ChatMember.user_id)
        .where(User.telegram_user_id == telegram_user_id)
        .where(Chat.status == ChatStatus.active)
    )
    return result.scalars().all()


@router.get("/{chat_id}", response_model=ChatOut)
async def get_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.post("/register", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
async def register_chat(
    data: ChatCreate,
    telegram_user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового чата при добавлении бота."""
    # Найти или создать пользователя
    user_result = await db.execute(
        select(User).where(User.telegram_user_id == telegram_user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        user = User(telegram_user_id=telegram_user_id, created_at=datetime.now(timezone.utc))
        db.add(user)
        await db.flush()

    # Проверить, не подключён ли уже чат
    existing = await db.execute(
        select(Chat).where(Chat.telegram_chat_id == data.telegram_chat_id)
    )
    chat = existing.scalar_one_or_none()

    if chat:
        # Переактивировать если был неактивен
        chat.status = ChatStatus.active
        chat.last_activity_at = datetime.now(timezone.utc)
    else:
        chat = Chat(
            telegram_chat_id=data.telegram_chat_id,
            title=data.title,
            username=data.username,
            member_count=data.member_count,
            bot_added_by_user_id=user.id,
            owner_user_id=user.id,
            connected_at=datetime.now(timezone.utc),
        )
        db.add(chat)
        await db.flush()

        # Создать дефолтные настройки
        settings = ChatSettings(chat_id=chat.id)
        db.add(settings)

        # Создать Free подписку
        from models.subscription import Subscription
        sub = Subscription(chat_id=chat.id, started_at=datetime.now(timezone.utc))
        db.add(sub)

        # Добавить пользователя как owner
        from models.chat import ChatMember, ChatMemberRole
        member = ChatMember(
            chat_id=chat.id,
            user_id=user.id,
            role=ChatMemberRole.owner,
            granted_at=datetime.now(timezone.utc),
            can_ban=True, can_mute=True, can_warn=True,
            can_edit_welcome=True, can_edit_rules=True,
            can_manage_protection=True, can_manage_triggers=True,
            can_view_logs=True, can_view_stats=True,
        )
        db.add(member)

    await db.commit()
    await db.refresh(chat)
    return chat


@router.patch("/{chat_id}/activity")
async def update_activity(chat_id: int, db: AsyncSession = Depends(get_db)):
    """Обновить last_activity_at для чата."""
    await db.execute(
        update(Chat)
        .where(Chat.id == chat_id)
        .values(last_activity_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"ok": True}
