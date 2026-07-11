from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow


class PracticeAttemptAnalysis(Base):
    """
    Result of running Phase 14's recitation analysis on a practice
    attempt's uploaded audio: transcribe it (Whisper), then word-diff the
    transcription against the real ayah text for that attempt's range
    (fetched live, same as everywhere else in this app — see
    `services/quran_text.py`). See `services/recitation_analysis.py` for
    exactly what this can and can't detect — short version: missing/
    extra/substituted *words*, not Tajweed correctness.
    """

    __tablename__ = "practice_attempt_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("pan"))
    attempt_id: Mapped[str] = mapped_column(ForeignKey("practice_attempts.id"), unique=True, index=True)

    status: Mapped[str] = mapped_column(String)  # 'completed' | 'failed'
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    transcribed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_word_count: Mapped[int] = mapped_column(Integer, default=0)
    matched_word_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    mistakes: Mapped[list["PracticeMistakeRow"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", order_by="PracticeMistakeRow.position"
    )


class PracticeMistakeRow(Base):
    __tablename__ = "practice_mistakes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("pmk"))
    analysis_id: Mapped[str] = mapped_column(ForeignKey("practice_attempt_analyses.id"), index=True)

    position: Mapped[int] = mapped_column(Integer)  # word index within the reference range, for ordering
    mistake_type: Mapped[str] = mapped_column(String)  # 'missing' | 'extra' | 'substituted'
    ayah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null only for 'extra'
    reference_word: Mapped[str | None] = mapped_column(String, nullable=True)
    transcribed_word: Mapped[str | None] = mapped_column(String, nullable=True)

    analysis: Mapped["PracticeAttemptAnalysis"] = relationship(back_populates="mistakes")
