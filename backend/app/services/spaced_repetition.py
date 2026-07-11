from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.lesson import Sabaq
from app.models.review import ReviewSchedule
from app.models.test import TestSession
from app.models.user import StudentProfile, today

"""
SM-2 (SuperMemo-2), not FSRS. FSRS is more accurate in principle, but it's
fit from a large corpus of real review-outcome logs — this app has none
yet, and fitting FSRS parameters on a cold-start dataset of a handful of
seeded demo reviews would just be guessing dressed up as machine learning.
SM-2 is a fixed, published, deterministic algorithm that needs no training
data to be correct, which makes it the honest choice here. Revisiting FSRS
once there's a real corpus of review history is a reasonable future step,
not a compromise made permanently.

Review-item granularity is one Sabaq (a surah/ayah-range assignment) —
the same unit the rest of the app already organizes around, not
individual ayahs. That's coarser than some spaced-repetition systems use,
but building and displaying separate schedules for every one of ~6,236
ayahs is disproportionate to what this phase needs, and Sabaqs already
group ayahs the way a student and teacher actually think about them.

Grading input: an SM-2 "quality" score (0-5) derived from a real signal
already recorded — the self-marked score_percent of a Test Mode session
covering the same surah/ayah range as a completed Sabaq — not a new
grading UI invented for this feature.
"""


def score_to_quality(score_percent: int) -> int:
    if score_percent >= 95:
        return 5
    if score_percent >= 80:
        return 4
    if score_percent >= 60:
        return 3
    if score_percent >= 40:
        return 2
    if score_percent >= 20:
        return 1
    return 0


def apply_sm2(schedule: ReviewSchedule, quality: int) -> None:
    """Mutates `schedule` in place per the classic SM-2 update rule."""
    if quality < 3:
        schedule.repetition_number = 0
        schedule.interval_days = 1
    else:
        if schedule.repetition_number == 0:
            schedule.interval_days = 1
        elif schedule.repetition_number == 1:
            schedule.interval_days = 6
        else:
            schedule.interval_days = round(schedule.interval_days * schedule.ease_factor)
        schedule.repetition_number += 1

    schedule.ease_factor = max(
        1.3,
        schedule.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )
    schedule.last_reviewed_date = today()
    schedule.last_quality = quality
    schedule.due_date = today() + timedelta(days=schedule.interval_days)


def get_or_create_schedule(db: Session, sabaq: Sabaq) -> ReviewSchedule:
    existing = db.query(ReviewSchedule).filter(ReviewSchedule.sabaq_id == sabaq.id).first()
    if existing:
        return existing

    schedule = ReviewSchedule(sabaq_id=sabaq.id, student_id=sabaq.student_id, due_date=today())
    db.add(schedule)
    db.flush()
    return schedule


def _ayah_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start) + 1)


def find_matching_completed_sabaq(
    db: Session, student_id: str, surah_number: int, from_ayah: int, to_ayah: int
) -> Sabaq | None:
    """
    A Test Mode session doesn't carry a `sabaq_id` — a student can test
    themselves on any range. This finds the completed Sabaq (if any) that
    session was most plausibly reviewing: same surah, greatest ayah-range
    overlap, ties broken by the most recently assigned matching Sabaq.
    """
    candidates = (
        db.query(Sabaq)
        .filter(Sabaq.student_id == student_id, Sabaq.surah_number == surah_number, Sabaq.status == "completed")
        .all()
    )
    scored = [
        (sabaq, _ayah_overlap(sabaq.from_ayah, sabaq.to_ayah, from_ayah, to_ayah)) for sabaq in candidates
    ]
    scored = [pair for pair in scored if pair[1] > 0]
    if not scored:
        return None

    scored.sort(key=lambda pair: (pair[1], pair[0].assigned_date), reverse=True)
    return scored[0][0]


def record_test_result(db: Session, student: StudentProfile, test_session: TestSession) -> ReviewSchedule | None:
    """
    Called right after a Test Mode session is saved (see routers/me.py).
    Returns None (and updates nothing) if the tested range doesn't match
    any of the student's completed Sabaqs — not every test session is a
    graded review of prior memorization, and this doesn't invent a match
    where there isn't a real one.
    """
    sabaq = find_matching_completed_sabaq(
        db, student.id, test_session.surah_number, test_session.from_ayah, test_session.to_ayah
    )
    if sabaq is None:
        return None

    schedule = get_or_create_schedule(db, sabaq)
    apply_sm2(schedule, score_to_quality(test_session.score_percent))
    db.add(schedule)
    return schedule


def get_due_reviews(db: Session, student_id: str) -> list[tuple[Sabaq, ReviewSchedule]]:
    """Everything due today or overdue, most overdue first."""
    rows = (
        db.query(ReviewSchedule, Sabaq)
        .join(Sabaq, Sabaq.id == ReviewSchedule.sabaq_id)
        .filter(ReviewSchedule.student_id == student_id, ReviewSchedule.due_date <= today())
        .order_by(ReviewSchedule.due_date.asc())
        .all()
    )
    return [(sabaq, schedule) for schedule, sabaq in rows]


def get_dashboard_reviews(
    db: Session, student_id: str
) -> tuple[tuple[Sabaq, ReviewSchedule] | None, tuple[Sabaq, ReviewSchedule] | None]:
    """
    Picks two due items for the Dashboard's traditional Sabaq/Sabqi/Manzil
    layout: "Sabqi" (recent review) is the due item from the most recently
    assigned Sabaq; "Manzil" (distant review) is the due item from the
    oldest. If there's only one due item, or none, the unfilled slot is
    genuinely None — an honest empty state rather than a fabricated one,
    unlike the Phase 10 heuristic this replaces.
    """
    due = get_due_reviews(db, student_id)
    if not due:
        return None, None

    by_recency = sorted(due, key=lambda pair: pair[0].assigned_date, reverse=True)
    sabqi = by_recency[0]
    manzil = by_recency[-1] if len(by_recency) > 1 else None
    return sabqi, manzil
