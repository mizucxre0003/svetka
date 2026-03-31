import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class WarningStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"


class Warning(Base):
    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    issued_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status: Mapped[WarningStatus] = mapped_column(SAEnum(WarningStatus), default=WarningStatus.active)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    issued_by: Mapped["User"] = relationship("User", foreign_keys=[issued_by_user_id])
