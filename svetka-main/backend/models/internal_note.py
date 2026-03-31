from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class InternalNote(Base):
    __tablename__ = "internal_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)  # "admin" или имя
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    chat: Mapped["Chat"] = relationship("Chat", back_populates="notes")
