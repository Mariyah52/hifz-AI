from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow


class ReviewSchedule(Base):
    """
    One row per Sabaq that has entered spaced-repetition rotation (i.e. a
    Sabaq the student has completed and is now revising periodically
    rather than actively memorizing). State is the classic SM-2 algorithm
    — see `app/services/spaced_repetition.py` for why SM-2 rather than
    FSRS, and for the actual scheduling logic; this model only holds the
    numbers SM-2 needs.

    `student_id` is denormalized here (also reachable via `sabaq.student_id`)
    purely so "all of this student's due reviews" is a single indexed query
    instead of a join through `sabaqs` on every dashboard/revision load.
    """

    __tablename__ = "review_schedules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("rev"))
    sabaq_id: Mapped[str] = mapped_column(ForeignKey("sabaqs.id"), unique=True, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)

    # SM-2 state
    repetition_number: Mapped[int] = mapped_column(Integer, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)

    due_date: Mapped[date] = mapped_column(Date)
    last_reviewed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Phase 21: the most recent SM-2 quality score (0-5) this schedule was
    # graded with — feeds the real "retention rate" analytics metric
    # (% of reviewed items whose last grading was a genuine recall, quality >= 3).
    last_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
