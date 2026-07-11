from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow


class TeacherFeedback(Base):
    __tablename__ = "teacher_feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("fb"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    teacher_id: Mapped[str | None] = mapped_column(ForeignKey("teacher_profiles.id"), nullable=True)

    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
