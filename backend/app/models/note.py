from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow


class Note(Base):
    """
    A student's own free-text note, optionally attached to a specific
    surah/ayah (e.g. "always forget the pause here"). Simple by design —
    this isn't a rich-text editor, just a real place to jot something down
    that syncs like everything else in Phase 26's offline queue.
    """

    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("note"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)

    content: Mapped[str] = mapped_column(Text)
    surah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ayah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    client_mutation_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
