from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow


class TestSession(Base):
    __tablename__ = "test_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("ts"))
    student_id: Mapped[str] = mapped_column(ForeignKey("student_profiles.id"), index=True)

    surah_number: Mapped[int] = mapped_column(Integer)
    surah_name: Mapped[str] = mapped_column(String)
    from_ayah: Mapped[int] = mapped_column(Integer)
    to_ayah: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    score_percent: Mapped[int] = mapped_column(Integer)

    # One continuous recording across the whole ayah range (replaces the
    # old per-ayah listen/recite/reveal loop) — analyzed the same way
    # Practice Mode analyzes a PracticeAttempt: Whisper transcription,
    # word-diffed against the real reference text for from_ayah..to_ayah.
    audio_url: Mapped[str | None] = mapped_column(String, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String, default="completed")  # 'completed' | 'failed'
    analysis_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Phase 26: same idempotency purpose as PracticeAttempt.client_mutation_id.
    client_mutation_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)

    results: Mapped[list["TestResult"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="TestResult.ayah_number"
    )
    mistakes: Mapped[list["TestMistakeRow"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="TestMistakeRow.position"
    )


class TestResult(Base):
    """
    Per-ayah outcome — AI-derived from the session's one Whisper transcript
    word-diffed against the real reference text (see
    `services/test_analysis.py`), not student self-marking. `mark` stays
    'correct'/'missed' for backward compatibility with older reads, backed
    now by `matched_word_count`/`total_word_count` for the real tally.
    """

    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("tr"))
    session_id: Mapped[str] = mapped_column(ForeignKey("test_sessions.id"), index=True)

    ayah_number: Mapped[int] = mapped_column(Integer)
    mark: Mapped[str] = mapped_column(String)  # 'correct' | 'missed'
    matched_word_count: Mapped[int] = mapped_column(Integer, default=0)
    total_word_count: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped["TestSession"] = relationship(back_populates="results")


class TestMistakeRow(Base):
    """Mirrors `PracticeMistakeRow` exactly — see that model for the field meanings."""

    __tablename__ = "test_mistakes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("tmk"))
    session_id: Mapped[str] = mapped_column(ForeignKey("test_sessions.id"), index=True)

    position: Mapped[int] = mapped_column(Integer)  # word index within the reference range, for ordering
    mistake_type: Mapped[str] = mapped_column(String)  # 'missing' | 'extra' | 'substituted'
    ayah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)  # null only for 'extra'
    reference_word: Mapped[str | None] = mapped_column(String, nullable=True)
    transcribed_word: Mapped[str | None] = mapped_column(String, nullable=True)

    session: Mapped["TestSession"] = relationship(back_populates="mistakes")
