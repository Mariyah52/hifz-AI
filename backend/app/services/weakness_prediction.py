from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.lesson import Sabaq
from app.models.review import ReviewSchedule
from app.models.user import today

"""
Weakness Prediction — v1, a documented heuristic, not a trained model.

Consistent with this project's stated principle (see product docs, §2):
never present an invented or approximate number as if it were measured
fact. This module is explicit about which one it is.

What this actually computes: SM-2 (spaced_repetition.py) already decides
*when* a Sabaq becomes due, calibrated so recall probability is ~90% at
the due date. This module re-expresses that same schedule as a forgetting
RISK curve, and lets you ask for it *before* the due date arrives, not
just a binary "due or not". It is the SM-2 forgetting-curve math relabeled
as a forward-looking risk score, not a model trained on this app's own
students' actual forgetting patterns — that would need a real corpus of
per-student retention outcomes over time, which doesn't exist yet (see
spaced_repetition.py's own note on why FSRS was rejected for the same
reason). Revisit this as a genuinely trained model once that data exists.

The curve: retention is modeled as an exponential decay that equals ~90%
exactly at `due_date` (matching SM-2's own target), and keeps decaying
after that if the item goes unreviewed. A lower ease_factor (an item the
student has repeatedly needed to relearn) decays faster than a high one,
since ease_factor is already SM-2's own signal for "how well this student
holds this material."
"""

# SM-2 calibrates each interval to ~90% retention at the due date.
_TARGET_RETENTION_AT_DUE = 0.9

# Bounds so a brand-new item (interval_days == 0, not yet reviewed even
# once) doesn't produce a division-by-zero or a meaningless spike.
_MIN_EFFECTIVE_INTERVAL_DAYS = 1.0


@dataclass
class WeaknessPrediction:
    sabaq_id: str
    surah_number: int
    from_ayah: int
    to_ayah: int
    days_since_last_review: int
    days_until_due: int  # negative if already overdue
    forgetting_risk_percent: float  # 0-100, higher = more likely forgotten
    ease_factor: float
    basis: str = "sm2_decay_heuristic_v1"  # explicit, not "ai_predicted"


def _estimate_forgetting_risk(
    days_since_last_review: float, interval_days: float, ease_factor: float
) -> float:
    """
    Returns a 0.0-1.0 forgetting risk (1 - estimated retention).

    Derivation: solve `retention(t) = exp(-k * t)` for k such that
    retention(interval_days) == _TARGET_RETENTION_AT_DUE, i.e.
    k = -ln(0.9) / interval_days. A weaker ease_factor scales k up
    (faster decay) since low ease means this student needed more
    relearning attempts on this material historically.
    """
    import math

    effective_interval = max(interval_days, _MIN_EFFECTIVE_INTERVAL_DAYS)
    base_k = -math.log(_TARGET_RETENTION_AT_DUE) / effective_interval

    # ease_factor ranges [1.3, ~2.5+]; 2.5 is SM-2's default/neutral value.
    # Below 2.5, scale decay rate up (forgets faster); above, scale down.
    ease_multiplier = 2.5 / max(ease_factor, 1.3)
    k = base_k * ease_multiplier

    retention = math.exp(-k * max(days_since_last_review, 0.0))
    return round((1.0 - retention) * 100, 1)


def predict_weakness(db: Session, student_id: str) -> list[WeaknessPrediction]:
    """
    Forgetting-risk estimate for every Sabaq currently in SM-2 rotation for
    this student — including ones not due yet, unlike get_due_reviews()
    which only returns items already due. Sorted highest-risk first, so
    the frontend can surface "you're at risk of forgetting X soon" ahead
    of the due date, not just on it.
    """
    rows = (
        db.query(ReviewSchedule, Sabaq)
        .join(Sabaq, Sabaq.id == ReviewSchedule.sabaq_id)
        .filter(ReviewSchedule.student_id == student_id)
        .all()
    )

    predictions: list[WeaknessPrediction] = []
    for schedule, sabaq in rows:
        reference_date = schedule.last_reviewed_date or sabaq.assigned_date
        days_since = (today() - reference_date).days
        days_until_due = (schedule.due_date - today()).days

        risk = _estimate_forgetting_risk(
            days_since_last_review=days_since,
            interval_days=max(schedule.interval_days, _MIN_EFFECTIVE_INTERVAL_DAYS),
            ease_factor=schedule.ease_factor,
        )

        predictions.append(
            WeaknessPrediction(
                sabaq_id=sabaq.id,
                surah_number=sabaq.surah_number,
                from_ayah=sabaq.from_ayah,
                to_ayah=sabaq.to_ayah,
                days_since_last_review=days_since,
                days_until_due=days_until_due,
                forgetting_risk_percent=risk,
                ease_factor=round(schedule.ease_factor, 2),
            )
        )

    predictions.sort(key=lambda p: p.forgetting_risk_percent, reverse=True)
    return predictions
