from datetime import timedelta

from app.models.user import StudentProfile, today
from app.services.streak import record_activity_today


def _fresh_student(**overrides) -> StudentProfile:
    defaults = dict(
        id="stu_test", user_id="u_test", class_id=None,
        current_streak=0, longest_streak=0, last_active_date=None, freezes_available=2,
    )
    defaults.update(overrides)
    return StudentProfile(**defaults)


def test_first_ever_activity_starts_streak_at_one():
    student = _fresh_student()
    record_activity_today(student)
    assert student.current_streak == 1
    assert student.longest_streak == 1
    assert student.last_active_date == today()


def test_activity_on_consecutive_day_continues_streak():
    student = _fresh_student(current_streak=5, longest_streak=5, last_active_date=today() - timedelta(days=1))
    record_activity_today(student)
    assert student.current_streak == 6
    assert student.longest_streak == 6


def test_activity_after_a_gap_resets_streak_to_one():
    student = _fresh_student(current_streak=10, longest_streak=10, last_active_date=today() - timedelta(days=3))
    record_activity_today(student)
    assert student.current_streak == 1
    assert student.longest_streak == 10


def test_activity_already_recorded_today_is_a_no_op():
    student = _fresh_student(current_streak=4, longest_streak=4, last_active_date=today())
    record_activity_today(student)
    assert student.current_streak == 4
    assert student.longest_streak == 4


def test_longest_streak_only_ever_increases():
    student = _fresh_student(current_streak=0, longest_streak=15, last_active_date=None)
    record_activity_today(student)
    assert student.current_streak == 1
    assert student.longest_streak == 15
