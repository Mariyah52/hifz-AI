from datetime import datetime
from typing import Literal

from app.schemas.base import CamelModel


class PaceOut(CamelModel):
    expected_seconds_range: tuple[float, float]
    actual_seconds: float
    within_expected_range: bool


MistakeType = Literal["missing", "extra", "substituted"]
AnalysisStatus = Literal["not_analyzed", "completed", "failed"]


class PracticeMistakeOut(CamelModel):
    mistake_type: MistakeType
    ayah_number: int | None
    reference_word: str | None
    transcribed_word: str | None


class PracticeAttemptOut(CamelModel):
    id: str
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    recorded_at: datetime
    duration_seconds: float
    status: str
    audio_url: str | None = None
    pace: PaceOut

    # Phase 14 — recitation analysis. `analysis_status` is 'not_analyzed'
    # until explicitly requested (POST .../analyze); pronunciation/fluency
    # scores are deliberately absent from this model entirely — this app
    # never reports a number it can't actually compute (see
    # services/arabic_text.py for exactly what word-diffing can and can't
    # tell you).
    analysis_status: AnalysisStatus = "not_analyzed"
    analysis_error: str | None = None
    transcribed_text: str | None = None
    matched_word_count: int | None = None
    total_word_count: int | None = None
    mistakes: list[PracticeMistakeOut] = []


class PracticeAttemptCreate(CamelModel):
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    duration_seconds: float
    expected_min_seconds: float
    expected_max_seconds: float
    # Phase 26: a client-generated UUID so a queued offline write, synced
    # later (possibly retried if the sync itself gets interrupted), never
    # creates a duplicate attempt — see services/idempotency.py.
    client_mutation_id: str | None = None
