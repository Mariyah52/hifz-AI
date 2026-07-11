from datetime import datetime
from typing import Literal

from app.schemas.base import CamelModel

AyahMark = Literal["correct", "missed"]
MistakeType = Literal["missing", "extra", "substituted"]
AnalysisStatus = Literal["completed", "failed"]


class TestMistakeOut(CamelModel):
    mistake_type: MistakeType
    ayah_number: int | None
    reference_word: str | None
    transcribed_word: str | None


class TestResultOut(CamelModel):
    ayah_number: int
    mark: AyahMark
    matched_word_count: int
    total_word_count: int


class QuizTestSessionCreate(CamelModel):
    """
    For Test Modes' multiple-choice/recognition questions (Phase 22) —
    already objectively graded client-side from the generated question's
    known correct answer. No audio, so this is kept separate from the
    recitation endpoint below (which always uploads and AI-analyzes audio).
    """

    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    is_correct: bool


class TestSessionOut(CamelModel):
    id: str
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    completed_at: datetime
    results: list[TestResultOut]
    score_percent: int
    audio_url: str | None
    analysis_status: AnalysisStatus
    analysis_error: str | None
    matched_word_count: int
    total_word_count: int
    mistakes: list[TestMistakeOut]
