from app.schemas.base import CamelModel


class WeakSurahOut(CamelModel):
    surah_number: int
    surah_name: str
    accuracy: float
    attempt_count: int


class WeakJuzOut(CamelModel):
    juz: int
    accuracy: float
    attempt_count: int


class WeakPageOut(CamelModel):
    page: int
    accuracy: float
    attempt_count: int


class ForgottenAyahOut(CamelModel):
    surah_number: int
    surah_name: str
    ayah_number: int
    accuracy: float
    missed_count: int
    attempt_count: int


class AdvancedAnalyticsOut(CamelModel):
    """
    Every field here is computed from real recorded rows (TestResult,
    ReviewSchedule, StudentProfile.longest_streak) — see
    `services/analytics.py` for the exact formulas, especially
    `confidence_score`, which is a documented weighted blend of two real
    measured signals, not a trained model's output.
    """

    overall_accuracy: float
    weakest_surah: WeakSurahOut | None
    weakest_juz: WeakJuzOut | None
    weakest_pages: list[WeakPageOut]
    most_forgotten_ayah: ForgottenAyahOut | None
    longest_streak: int
    average_revision_time_seconds: float | None
    retention_rate: float | None
    confidence_score: float | None
