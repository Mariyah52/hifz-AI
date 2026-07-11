from datetime import date
from typing import Literal

from app.schemas.base import CamelModel
from app.schemas.lesson import SabaqOut

UserRole = Literal["student", "teacher", "parent", "admin"]


class UserOut(CamelModel):
    id: str
    name: str
    role: UserRole
    class_id: str | None = None


class StreakInfo(CamelModel):
    current_streak: int
    longest_streak: int
    last_active_date: date | None
    freezes_available: int


class SabqiReviewOut(CamelModel):
    """A due review of a recently-completed Sabaq — see spaced_repetition.py."""

    id: str
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    status: Literal["not_started", "in_progress", "completed"]
    score: int | None = None


class ManzilReviewOut(CamelModel):
    """
    A due review of an older/more-established Sabaq. Through Phase 12 this
    was juz-shaped (a rotating older portion, picked by a heuristic). As of
    Phase 13 it's real per-Sabaq spaced-repetition state instead — same
    shape as SabqiReviewOut, distinguished from it only by which due item
    the SM-2 schedule picked (see `spaced_repetition.get_dashboard_reviews`).
    The frontend still derives a "Juz N" label for display from this
    Sabaq's surah/ayah, using its own already-verified juz-boundary lookup
    — no juz data needed here.
    """

    id: str
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    status: Literal["not_started", "in_progress", "completed"]
    score: int | None = None


class DashboardSummary(CamelModel):
    user: UserOut
    streak: StreakInfo
    todays_sabaq: SabaqOut | None
    todays_sabqi: SabqiReviewOut | None
    todays_manzil: ManzilReviewOut | None
    recent_sabaqs: list[SabaqOut]
    juz_progress: float
    overall_accuracy: float
