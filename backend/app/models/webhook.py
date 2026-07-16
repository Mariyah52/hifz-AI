from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow

# Real, currently-dispatched event types — see services/webhooks.py's
# dispatch_event() call sites for exactly where each one fires. Kept as
# a plain tuple, not a DB enum, so adding a new event type later is a
# one-line change here plus one new call site, not a migration.
WEBHOOK_EVENT_TYPES = ("sabaq.completed", "certificate.issued", "student.created")


class Webhook(Base):
    """
    One row per URL an organization wants HifzAI to POST real events to.
    `secret` is stored in plaintext (not hashed) — unlike an API key,
    where only the *presenter* ever needs the raw value, here HifzAI
    itself (the sender) needs the raw secret on every single delivery to
    compute an HMAC-SHA256 signature the receiver can verify. See
    services/webhooks.py for the signing scheme.

    `event_types` is a comma-separated subset of WEBHOOK_EVENT_TYPES —
    same convention as ApiKey.scopes and ChatMessage.tools_called.
    """

    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("wh"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    url: Mapped[str] = mapped_column(String)
    secret: Mapped[str] = mapped_column(String)
    event_types: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def subscribes_to(self, event_type: str) -> bool:
        return event_type in (e.strip() for e in self.event_types.split(","))


class WebhookDeliveryLog(Base):
    """
    A short delivery history per webhook — enough for an admin to see
    "is this actually working" (last N attempts, success/failure, status
    code) without needing real external log aggregation. Not a queue or
    a retry mechanism — see services/webhooks.py's docstring for that
    real, stated limitation.
    """

    __tablename__ = "webhook_delivery_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("whlog"))
    webhook_id: Mapped[str] = mapped_column(ForeignKey("webhooks.id"), index=True)
    event_type: Mapped[str] = mapped_column(String)
    success: Mapped[bool] = mapped_column(Boolean)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_snippet: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    webhook: Mapped["Webhook"] = relationship()
