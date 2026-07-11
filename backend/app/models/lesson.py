from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, today, utcnow


class Sabaq(Base):
    """
    The day's assigned memorization portion for one student. A student can
    have many Sabaq rows over time; "today's Sabaq" is just the most
    recent one for that student (see `crud` helpers in the routers).
    """

    __tablename__ = "sabaqs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("sbq"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)

    surah_number: Mapped[int] = mapped_column(Integer)
    surah_name: Mapped[str] = mapped_column(String)
    from_ayah: Mapped[int] = mapped_column(Integer)
    to_ayah: Mapped[int] = mapped_column(Integer)
    assigned_date: Mapped[date] = mapped_column(Date, default=today)
    status: Mapped[str] = mapped_column(String, default="not_started")  # not_started|in_progress|completed
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
