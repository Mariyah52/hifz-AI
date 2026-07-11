from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow


class Notification(Base):
    """
    One row per in-app notification, for any role (student, teacher,
    parent, admin) — not student-only, unlike most of this app's other
    tables. Generated either directly from a real action (a teacher
    leaving feedback or assigning a Sabaq) or by the scheduled jobs in
    `app/scheduler.py` (overdue reviews, streak-at-risk, weekly parent
    digest) — never invented content with no real event behind it.
    """

    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("ntf"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)

    notification_type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(Text)
    related_id: Mapped[str | None] = mapped_column(String, nullable=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class PushSubscription(Base):
    """
    A browser's Web Push subscription (from `PushManager.subscribe()`),
    one row per (user, browser). `endpoint` is effectively unique per
    browser/device, so re-subscribing the same browser updates its own
    row rather than accumulating duplicates.
    """

    __tablename__ = "push_subscriptions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("psub"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)

    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh_key: Mapped[str] = mapped_column(String)
    auth_key: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
