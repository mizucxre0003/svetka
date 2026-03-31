import enum
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Integer,
    ForeignKey, Enum as SAEnum, JSON, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class TariffPlan(str, enum.Enum):
    free = "free"
    trial = "trial"
    pro = "pro"


class ChatStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    bot_added_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    tariff: Mapped[TariffPlan] = mapped_column(SAEnum(TariffPlan, native_enum=False, length=20), default=TariffPlan.free)
    status: Mapped[ChatStatus] = mapped_column(SAEnum(ChatStatus, native_enum=False, length=20), default=ChatStatus.active)

    # Relationships
    settings: Mapped["ChatSettings"] = relationship("ChatSettings", back_populates="chat", uselist=False, lazy="selectin")
    members: Mapped[list["ChatMember"]] = relationship("ChatMember", back_populates="chat")
    logs: Mapped[list["Log"]] = relationship("Log", back_populates="chat")
    notes: Mapped[list["InternalNote"]] = relationship("InternalNote", back_populates="chat")
    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="chat", uselist=False)


class ChatMemberRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    moderator = "moderator"
    member = "member"


class ChatMember(Base):
    __tablename__ = "chat_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    role: Mapped[ChatMemberRole] = mapped_column(SAEnum(ChatMemberRole, native_enum=False, length=20), default=ChatMemberRole.member)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    granted_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Rights
    can_ban: Mapped[bool] = mapped_column(Boolean, default=False)
    can_mute: Mapped[bool] = mapped_column(Boolean, default=False)
    can_warn: Mapped[bool] = mapped_column(Boolean, default=False)
    can_edit_welcome: Mapped[bool] = mapped_column(Boolean, default=False)
    can_edit_rules: Mapped[bool] = mapped_column(Boolean, default=False)
    can_manage_protection: Mapped[bool] = mapped_column(Boolean, default=False)
    can_manage_triggers: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_logs: Mapped[bool] = mapped_column(Boolean, default=False)
    can_view_stats: Mapped[bool] = mapped_column(Boolean, default=False)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="members")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class ChatSettings(Base):
    __tablename__ = "chat_settings"

    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), primary_key=True)

    # Welcome / Rules
    welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    welcome_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    welcome_buttons: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    welcome_delete_after: Mapped[int | None] = mapped_column(Integer, nullable=True)  # seconds
    rules_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    rules_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Anti-flood
    anti_flood_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_flood_limit: Mapped[int] = mapped_column(Integer, default=5)
    anti_flood_interval: Mapped[int] = mapped_column(Integer, default=5)  # seconds
    anti_flood_action: Mapped[str] = mapped_column(String(20), default="mute")

    # Anti-links
    anti_links_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_links_action: Mapped[str] = mapped_column(String(20), default="delete")

    # Stop words
    stop_words_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    stop_words_list: Mapped[list | None] = mapped_column(JSON, nullable=True)
    stop_words_action: Mapped[str] = mapped_column(String(20), default="delete")

    # Repeat filter
    repeat_filter_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    repeat_filter_sensitivity: Mapped[float] = mapped_column(default=0.8)

    # Caps filter
    caps_filter_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    caps_filter_threshold: Mapped[float] = mapped_column(default=0.7)
    caps_filter_min_length: Mapped[int] = mapped_column(Integer, default=10)

    # Triggers
    triggers_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Logs
    logs_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Moderation
    default_warn_limit: Mapped[int] = mapped_column(Integer, default=3)
    warn_limit_action: Mapped[str] = mapped_column(String(20), default="mute")
    default_mute_duration: Mapped[int] = mapped_column(Integer, default=3600)  # seconds

    chat: Mapped["Chat"] = relationship("Chat", back_populates="settings")
