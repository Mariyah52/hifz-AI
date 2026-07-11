from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow


class Certificate(Base):
    """
    `type` is one of 'surah_completion' | 'juz_completion' (both
    auto-detected, lazily, same self-healing "check on every GET" pattern
    Phase 15's achievements established) or 'attendance' | 'competition'
    (both require a human judgment call — a teacher/admin issues these
    explicitly, see services/certificate_service.py). `issued_by_teacher_id`
    is null for the auto-detected types.

    The PDF itself is never stored — it's rendered on demand from this
    row's data plus the organization's real branding, so regenerating
    it always reflects the org's current name/logo/colors.
    """

    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("cert"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    detail: Mapped[str] = mapped_column(Text)
    issued_by_teacher_id: Mapped[str | None] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    student: Mapped["StudentProfile"] = relationship()  # noqa: F821
    issued_by_teacher: Mapped["TeacherProfile | None"] = relationship()  # noqa: F821
