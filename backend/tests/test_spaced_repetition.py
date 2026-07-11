from datetime import timedelta

from app.models.review import ReviewSchedule
from app.models.user import today
from app.services.spaced_repetition import apply_sm2, score_to_quality


def _new_schedule() -> ReviewSchedule:
    return ReviewSchedule(
        sabaq_id="sbq_test", student_id="stu_test",
        repetition_number=0, ease_factor=2.5, interval_days=0, due_date=today(),
    )


def test_score_to_quality_buckets():
    assert score_to_quality(100) == 5
    assert score_to_quality(95) == 5
    assert score_to_quality(94) == 4
    assert score_to_quality(80) == 4
    assert score_to_quality(79) == 3
    assert score_to_quality(60) == 3
    assert score_to_quality(59) == 2
    assert score_to_quality(40) == 2
    assert score_to_quality(39) == 1
    assert score_to_quality(20) == 1
    assert score_to_quality(19) == 0
    assert score_to_quality(0) == 0


def test_first_successful_review_sets_one_day_interval():
    schedule = _new_schedule()
    apply_sm2(schedule, quality=4)
    assert schedule.repetition_number == 1
    assert schedule.interval_days == 1
    assert schedule.due_date == today() + timedelta(days=1)
    assert schedule.last_reviewed_date == today()


def test_second_successful_review_sets_six_day_interval():
    schedule = _new_schedule()
    apply_sm2(schedule, quality=4)
    apply_sm2(schedule, quality=4)
    assert schedule.repetition_number == 2
    assert schedule.interval_days == 6


def test_third_successful_review_multiplies_by_ease_factor():
    schedule = _new_schedule()
    apply_sm2(schedule, quality=4)
    apply_sm2(schedule, quality=4)
    ease_before = schedule.ease_factor
    apply_sm2(schedule, quality=4)
    assert schedule.repetition_number == 3
    assert schedule.interval_days == round(6 * ease_before)


def test_failing_quality_resets_repetitions_and_interval():
    schedule = _new_schedule()
    apply_sm2(schedule, quality=4)
    apply_sm2(schedule, quality=4)
    assert schedule.repetition_number == 2

    apply_sm2(schedule, quality=1)
    assert schedule.repetition_number == 0
    assert schedule.interval_days == 1
    assert schedule.due_date == today() + timedelta(days=1)


def test_ease_factor_never_drops_below_minimum():
    schedule = _new_schedule()
    for _ in range(20):
        apply_sm2(schedule, quality=0)
    assert schedule.ease_factor >= 1.3


def test_ease_factor_increases_with_perfect_scores():
    schedule = _new_schedule()
    ease_start = schedule.ease_factor
    apply_sm2(schedule, quality=5)
    assert schedule.ease_factor > ease_start
