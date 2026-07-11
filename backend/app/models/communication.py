from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow


class Conversation(Base):
    """
    A conversation is always between two specific users — no group
    threads. `user_a_id`/`user_b_id` are stored in a canonical order
    (lexicographically smaller id first) so the same pair always maps to
    the same row regardless of who initiates, enforced by the unique
    constraint below plus get_or_create_conversation()'s own ordering.
    """

    __tablename__ = "conversations"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_conversation_pair"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("conv2"))
    user_a_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    user_b_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DirectMessage(Base):
    """
    `content` is nullable because a message can be attachment-only (e.g.
    just a voice note). Voice notes are audio *file uploads* — reusing
    the same multipart upload path Phase 10 built for practice-attempt
    recordings — not a dedicated in-message recorder; Practice Mode's
    live `useRecorder` wasn't duplicated here to keep this phase's scope
    contained. "Files" reuses the same storage for any attachment type.
    """

    __tablename__ = "direct_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("dmsg"))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_url: Mapped[str | None] = mapped_column(String, nullable=True)
    attachment_type: Mapped[str | None] = mapped_column(String, nullable=True)  # 'audio' | 'file'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Announcement(Base):
    """`class_id` null means institution-wide (admin-only); set means posted to one class by its teacher."""

    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("ann"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    class_id: Mapped[str | None] = mapped_column(ForeignKey("classes.id"), nullable=True, index=True)
    author_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    author: Mapped["User"] = relationship()  # noqa: F821


class Homework(Base):
    __tablename__ = "homework"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("hw"))
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    created_by_teacher_id: Mapped[str] = mapped_column(ForeignKey("teacher_profiles.id"))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
