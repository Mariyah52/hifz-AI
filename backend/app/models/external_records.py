from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow

# Real, deliberately open string — an external LMS's own status vocabulary
# ("present"/"absent"/"late"/"excused" is the common shape, but this app
# doesn't own that vocabulary, so it isn't enforced as a DB enum). The
# public API schema documents the conventional values without rejecting
# an LMS's own equivalent term.
ATTENDANCE_STATUSES = ("present", "absent", "late", "excused")


class ExternalAttendanceRecord(Base):
    """
    One attendance event pushed in by an external LMS/ERP via the
    write-enabled Public API (Phase 31). Deliberately a separate table
    from `LiveSessionParticipant` — this app's own real, automatic
    attendance for its own live classes — rather than writing into that
    table directly: an external system's attendance is a different
    source of truth with different provenance (which API key pushed it,
    when), and conflating the two would make it impossible to tell
    "the student joined a HifzAI live class" from "an external system
    says this happened."
    """

    __tablename__ = "external_attendance_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("extatt"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    api_key_id: Mapped[str] = mapped_column(ForeignKey("api_keys.id"))

    session_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String)
    source_label: Mapped[str | None] = mapped_column(String, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExternalGradeRecord(Base):
    """Same provenance reasoning as ExternalAttendanceRecord — a grade an external LMS reports, kept separate from this app's own real TestSession scores."""

    __tablename__ = "external_grade_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("extgrade"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    api_key_id: Mapped[str] = mapped_column(ForeignKey("api_keys.id"))

    label: Mapped[str] = mapped_column(String)
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float)
    recorded_date: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
