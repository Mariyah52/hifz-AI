from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow


class PracticeAttempt(Base):
    """
    One recorded Practice Mode attempt. `audio_url` is set only if the
    student's browser actually uploaded the recording (see
    `routers/me.py`) — this is the real storage Phase 7's README flagged
    as missing ("this app never persists recorded audio blobs past the
    browser session ... real recording review needs Phase 10's storage").
    It's still just local disk under `MEDIA_ROOT`, not S3/CDN-backed, so
    treat it as a first real step rather than production-grade storage.
    """

    __tablename__ = "practice_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("pa"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)

    surah_number: Mapped[int] = mapped_column(Integer)
    surah_name: Mapped[str] = mapped_column(String)
    from_ayah: Mapped[int] = mapped_column(Integer)
    to_ayah: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    duration_seconds: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default="recorded")

    expected_min_seconds: Mapped[float] = mapped_column(Float)
    expected_max_seconds: Mapped[float] = mapped_column(Float)
    within_expected_range: Mapped[bool] = mapped_column(Boolean)

    audio_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Phase 26: set only when this row was created via the offline sync
    # queue — lets a retried sync recognize "already did this" instead of
    # creating a duplicate. Null for attempts saved while online normally.
    client_mutation_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)

    # Phase 14 — set only once /analyze has been run at least once.
    analysis: Mapped["PracticeAttemptAnalysis | None"] = relationship(
        uselist=False, cascade="all, delete-orphan"
    )
