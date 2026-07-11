from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow


class ChatConversation(Base):
    """
    One ongoing conversation per student — deliberately not a multi-thread
    inbox (no conversation list UI was built). Every message a student
    sends appends to this single thread.
    """

    __tablename__ = "chat_conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("conv"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("cmsg"))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("chat_conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String)  # 'user' | 'assistant'
    content: Mapped[str] = mapped_column(Text)
    # Comma-separated tool names actually called to produce this reply —
    # empty for user messages and for assistant replies that didn't need
    # to look anything up (e.g. a general tajweed explanation).
    tools_called: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    conversation: Mapped["ChatConversation"] = relationship(back_populates="messages")
