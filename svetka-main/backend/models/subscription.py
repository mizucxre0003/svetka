import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class SubscriptionPlan(str, enum.Enum):
    free = "free"
    trial = "trial"
    pro = "pro"


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False, unique=True)
    plan: Mapped[SubscriptionPlan] = mapped_column(SAEnum(SubscriptionPlan, native_enum=False, length=20), default=SubscriptionPlan.free)
    status: Mapped[SubscriptionStatus] = mapped_column(SAEnum(SubscriptionStatus, native_enum=False, length=20), default=SubscriptionStatus.active)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    granted_by: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "admin" or user id

    chat: Mapped["Chat"] = relationship("Chat", back_populates="subscription")
