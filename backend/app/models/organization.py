from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow

# Plan limits are explicit numbers stored per-organization (not just
# derived from `plan` on every check) so a specific org could get a
# custom limit later (e.g. a negotiated enterprise deal) without a schema
# change — the plan name is descriptive, the numeric limits are what's
# actually enforced.
PLAN_DEFAULTS = {
    "free": {"max_students": 30, "max_teachers": 5},
    "pro": {"max_students": 500, "max_teachers": 50},
}


class Organization(Base):
    """
    One row per institution using this app. Every `User` belongs to
    exactly one organization (Phase 18) — this is the tenant boundary
    every multi-user query in this app now has to respect. See
    `services/tenancy.py` for the actual scoping helpers and
    `routers/auth.py` for how an organization gets created (an admin
    signing up creates one; everyone else joins an existing one by slug).

    Real, enforced: student/teacher counts are checked against
    `max_students`/`max_teachers` at registration. NOT built: actual
    billing/payment collection — upgrading `plan` today is a manual
    database update, not a checkout flow. That's a deliberate scope cut,
    not an oversight — see the root README's Phase 18 notes.
    """

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("org"))
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    plan: Mapped[str] = mapped_column(String, default="free")
    max_students: Mapped[int] = mapped_column(Integer, default=PLAN_DEFAULTS["free"]["max_students"])
    max_teachers: Mapped[int] = mapped_column(Integer, default=PLAN_DEFAULTS["free"]["max_teachers"])
    primary_color: Mapped[str | None] = mapped_column(String, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
