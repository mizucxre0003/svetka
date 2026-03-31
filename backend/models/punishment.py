import enum
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class PunishmentType(str, enum.Enum):
    ban = "ban"
    mute = "mute"
    kick = "kick"


class PunishmentStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"


class Punishment(Base):
    __tablename__ = "punishments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    issued_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    type: Mapped[PunishmentType] = mapped_column(SAEnum(PunishmentType, native_enum=False, length=20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PunishmentStatus] = mapped_column(SAEnum(PunishmentStatus, native_enum=False, length=20), default=PunishmentStatus.active)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    issued_by: Mapped["User"] = relationship("User", foreign_keys=[issued_by_user_id])
