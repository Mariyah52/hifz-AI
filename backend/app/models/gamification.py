from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow


class Achievement(Base):
    """
    One row per (student, achievement_key) the student has ever earned.
    `earned_at` is when this row was first created — i.e. the first time
    `services/gamification.py` checked and found the criterion already
    true, not necessarily the exact historical moment it became true
    (for data that predates this phase, e.g. seeded demo history, that
    moment is "the first time anyone opened Gamification after Phase 15
    shipped," which is an honest thing to be upfront about rather than
    inventing a false-precision backdated timestamp).

    Achievement rules only ever look at monotonically non-decreasing
    facts (longest_streak, total counts) specifically so nothing here can
    ever be un-earned by later, unrelated activity.
    """

    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("ach"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    achievement_key: Mapped[str] = mapped_column(String, index=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
