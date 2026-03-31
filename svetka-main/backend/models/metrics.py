from datetime import date, datetime, timezone
from sqlalchemy import String, DateTime, Date, Integer, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class CommandUsage(Base):
    __tablename__ = "command_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    command: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    messages_count: Mapped[int] = mapped_column(Integer, default=0)
    commands_count: Mapped[int] = mapped_column(Integer, default=0)
    moderation_actions_count: Mapped[int] = mapped_column(Integer, default=0)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0)
    mutes_count: Mapped[int] = mapped_column(Integer, default=0)
    bans_count: Mapped[int] = mapped_column(Integer, default=0)
    deleted_messages_count: Mapped[int] = mapped_column(Integer, default=0)
    mini_app_opens_count: Mapped[int] = mapped_column(Integer, default=0)
    active_users_count: Mapped[int] = mapped_column(Integer, default=0)
    protection_triggers_count: Mapped[int] = mapped_column(Integer, default=0)
