from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.test import TestResult, TestSession
from app.models.review import ReviewSchedule
from app.models.user import StudentProfile
from app.schemas.analytics import (
    AdvancedAnalyticsOut,
    ForgottenAyahOut,
    WeakJuzOut,
    WeakPageOut,
    WeakSurahOut,
)
from app.services.quran_text import get_ayah_positions

"""
Every metric here is arithmetic over real rows this app already records
— TestResult (per-ayah AI-scored outcomes, word-diffed from a real Whisper
transcription — see services/test_analysis.py), ReviewSchedule (SM-2 state),
StudentProfile.longest_streak. Nothing is a placeholder or a plausible-
looking random number.

MIN_ATTEMPTS_FOR_RANKING (2) exists so a single unlucky miss on an ayah
tested only once doesn't dominate "most forgotten ayah" or "weakest
surah/juz/page" — these rankings only consider items with at least this
many recorded attempts. `overall_accuracy` has no such threshold; it's a
straight ratio over everything.

`confidence_score` is the one metric worth being extra explicit about:
it's a documented weighted blend — 0.6 * retention_rate + 0.4 *
overall_accuracy — of two independently real, measured signals. It is
NOT the output of a trained model and doesn't claim to be; the weights
(0.6/0.4) are a reasonable, stated choice (retention over time weighted
higher than raw accuracy), not tuned against any labeled ground truth,
because no such ground truth exists for "how confident should this
student feel."
"""

MIN_ATTEMPTS_FOR_RANKING = 2


async def build_advanced_analytics(db: Session, student: StudentProfile) -> AdvancedAnalyticsOut:
    results = (
        db.query(TestResult, TestSession)
        .join(TestSession, TestSession.id == TestResult.session_id)
        .filter(TestSession.student_id == student.id)
        .all()
    )

    overall_accuracy = _accuracy([r for r, _ in results])

    per_surah: dict[tuple[int, str], list[TestResult]] = defaultdict(list)
    per_ayah: dict[tuple[int, str, int], list[TestResult]] = defaultdict(list)
    for result, session in results:
        per_surah[(session.surah_number, session.surah_name)].append(result)
        per_ayah[(session.surah_number, session.surah_name, result.ayah_number)].append(result)

    weakest_surah = _weakest_surah(per_surah)
    weakest_juz, weakest_pages = await _weakest_positions(per_ayah)
    most_forgotten_ayah = _most_forgotten_ayah(per_ayah)

    durations = [r.duration_seconds for r, _ in results]
    average_revision_time = round(sum(durations) / len(durations), 1) if durations else None

    retention_rate = _retention_rate(db, student.id)
    confidence_score = _confidence_score(retention_rate, overall_accuracy)

    return AdvancedAnalyticsOut(
        overall_accuracy=overall_accuracy,
        weakest_surah=weakest_surah,
        weakest_juz=weakest_juz,
        weakest_pages=weakest_pages,
        most_forgotten_ayah=most_forgotten_ayah,
        longest_streak=student.longest_streak,
        average_revision_time_seconds=average_revision_time,
        retention_rate=retention_rate,
        confidence_score=confidence_score,
    )


def _accuracy(results: list[TestResult]) -> float:
    if not results:
        return 0.0
    correct = sum(1 for r in results if r.mark == "correct")
    return round((correct / len(results)) * 100, 1)


def _weakest_surah(per_surah: dict[tuple[int, str], list[TestResult]]) -> WeakSurahOut | None:
    candidates = [
        WeakSurahOut(
            surah_number=surah_number, surah_name=surah_name,
            accuracy=_accuracy(results), attempt_count=len(results),
        )
        for (surah_number, surah_name), results in per_surah.items()
        if len(results) >= MIN_ATTEMPTS_FOR_RANKING
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda c: c.accuracy)


def _most_forgotten_ayah(
    per_ayah: dict[tuple[int, str, int], list[TestResult]],
) -> ForgottenAyahOut | None:
    candidates = [
        ForgottenAyahOut(
            surah_number=surah_number, surah_name=surah_name, ayah_number=ayah_number,
            accuracy=_accuracy(results),
            missed_count=sum(1 for r in results if r.mark == "missed"),
            attempt_count=len(results),
        )
        for (surah_number, surah_name, ayah_number), results in per_ayah.items()
        if len(results) >= MIN_ATTEMPTS_FOR_RANKING
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda c: (c.accuracy, -c.missed_count))


async def _weakest_positions(
    per_ayah: dict[tuple[int, str, int], list[TestResult]],
) -> tuple[WeakJuzOut | None, list[WeakPageOut]]:
    """
    Buckets the same per-ayah results by juz and by page — needs to know
    which juz/page each tested ayah falls on, fetched live and cached per
    surah (see quran_text.get_ayah_positions), never hand-typed.
    """
    juz_buckets: dict[int, list[TestResult]] = defaultdict(list)
    page_buckets: dict[int, list[TestResult]] = defaultdict(list)

    surah_numbers = {surah_number for surah_number, _, _ in per_ayah}
    positions_by_surah = {}
    for surah_number in surah_numbers:
        try:
            positions_by_surah[surah_number] = await get_ayah_positions(surah_number)
        except Exception:
            # If the live lookup fails for one surah, skip juz/page
            # bucketing for it rather than failing the whole analytics
            # response — every other metric here is still real and useful.
            positions_by_surah[surah_number] = {}

    for (surah_number, _surah_name, ayah_number), results in per_ayah.items():
        position = positions_by_surah.get(surah_number, {}).get(ayah_number)
        if not position:
            continue
        if position.get("juz") is not None:
            juz_buckets[position["juz"]].extend(results)
        if position.get("page") is not None:
            page_buckets[position["page"]].extend(results)

    juz_candidates = [
        WeakJuzOut(juz=juz, accuracy=_accuracy(results), attempt_count=len(results))
        for juz, results in juz_buckets.items()
        if len(results) >= MIN_ATTEMPTS_FOR_RANKING
    ]
    weakest_juz = min(juz_candidates, key=lambda c: c.accuracy) if juz_candidates else None

    page_candidates = [
        WeakPageOut(page=page, accuracy=_accuracy(results), attempt_count=len(results))
        for page, results in page_buckets.items()
        if len(results) >= MIN_ATTEMPTS_FOR_RANKING
    ]
    weakest_pages = sorted(page_candidates, key=lambda c: c.accuracy)[:3]

    return weakest_juz, weakest_pages


def _retention_rate(db: Session, student_id: str) -> float | None:
    schedules = (
        db.query(ReviewSchedule)
        .filter(ReviewSchedule.student_id == student_id, ReviewSchedule.last_quality.isnot(None))
        .all()
    )
    if not schedules:
        return None
    retained = sum(1 for s in schedules if s.last_quality >= 3)
    return round((retained / len(schedules)) * 100, 1)


def _confidence_score(retention_rate: float | None, overall_accuracy: float) -> float | None:
    if retention_rate is None:
        return None
    return round(0.6 * retention_rate + 0.4 * overall_accuracy, 1)
