from datetime import timedelta

from app.models.lesson import Sabaq
from app.models.review import ReviewSchedule
from app.models.user import today
from app.services.weakness_prediction import _estimate_forgetting_risk, predict_weakness
from tests.conftest import make_student


def test_risk_is_near_zero_immediately_after_review():
    risk = _estimate_forgetting_risk(days_since_last_review=0, interval_days=6, ease_factor=2.5)
    assert risk < 5.0


def test_risk_is_near_target_at_due_date():
    # At exactly interval_days elapsed, SM-2's own target is ~90% retention,
    # i.e. ~10% forgetting risk.
    risk = _estimate_forgetting_risk(days_since_last_review=6, interval_days=6, ease_factor=2.5)
    assert 8.0 <= risk <= 12.0


def test_risk_increases_with_time_since_review():
    early = _estimate_forgetting_risk(days_since_last_review=2, interval_days=6, ease_factor=2.5)
    late = _estimate_forgetting_risk(days_since_last_review=10, interval_days=6, ease_factor=2.5)
    assert late > early


def test_lower_ease_factor_increases_risk_at_same_elapsed_time():
    weak_item = _estimate_forgetting_risk(days_since_last_review=6, interval_days=6, ease_factor=1.3)
    strong_item = _estimate_forgetting_risk(days_since_last_review=6, interval_days=6, ease_factor=2.8)
    assert weak_item > strong_item


def test_zero_interval_does_not_crash(db_session):
    # Guards the _MIN_EFFECTIVE_INTERVAL_DAYS floor for brand-new items.
    risk = _estimate_forgetting_risk(days_since_last_review=0, interval_days=0, ease_factor=2.5)
    assert 0.0 <= risk <= 100.0


def test_predict_weakness_sorts_highest_risk_first(db_session):
    student = make_student(db_session)

    sabaq_weak = Sabaq(
        id="sbq_weak", student_id=student.id, surah_number=67, surah_name="Al-Mulk",
        from_ayah=1, to_ayah=10, status="completed", assigned_date=today() - timedelta(days=30),
    )
    sabaq_strong = Sabaq(
        id="sbq_strong", student_id=student.id, surah_number=36, surah_name="Ya-Sin",
        from_ayah=1, to_ayah=10, status="completed", assigned_date=today() - timedelta(days=30),
    )
    db_session.add_all([sabaq_weak, sabaq_strong])
    db_session.flush()

    weak_schedule = ReviewSchedule(
        sabaq_id="sbq_weak", student_id=student.id,
        repetition_number=1, ease_factor=1.3, interval_days=6,
        due_date=today() - timedelta(days=5),
        last_reviewed_date=today() - timedelta(days=11),
    )
    strong_schedule = ReviewSchedule(
        sabaq_id="sbq_strong", student_id=student.id,
        repetition_number=3, ease_factor=2.8, interval_days=20,
        due_date=today() + timedelta(days=15),
        last_reviewed_date=today() - timedelta(days=5),
    )
    db_session.add_all([weak_schedule, strong_schedule])
    db_session.flush()

    predictions = predict_weakness(db_session, student.id)
    assert len(predictions) == 2
    assert predictions[0].sabaq_id == "sbq_weak"
    assert predictions[0].forgetting_risk_percent > predictions[1].forgetting_risk_percent
    assert predictions[0].basis == "sm2_decay_heuristic_v1"
