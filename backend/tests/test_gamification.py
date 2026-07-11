from app.models.lesson import Sabaq
from app.models.practice import PracticeAttempt
from app.models.test import TestSession
from app.models.user import today
from app.services.gamification import (
    XP_PER_COMPLETED_SABAQ,
    XP_PER_LEVEL,
    XP_PER_PRACTICE_ATTEMPT,
    check_and_award_achievements,
    compute_xp,
    level_for_xp,
)
from tests.conftest import make_student


def test_level_for_xp_boundaries():
    assert level_for_xp(0).level == 1
    assert level_for_xp(XP_PER_LEVEL - 1).level == 1
    assert level_for_xp(XP_PER_LEVEL).level == 2
    assert level_for_xp(XP_PER_LEVEL * 3).level == 4


def test_level_for_xp_tracks_remaining_xp_correctly():
    info = level_for_xp(50)
    assert info.xp_into_level == 50
    assert info.xp_to_next_level == XP_PER_LEVEL - 50


def test_compute_xp_from_practice_attempts_only(db_session):
    student = make_student(db_session, email="a@example.com")
    for _ in range(3):
        db_session.add(
            PracticeAttempt(
                student_id=student.id, surah_number=1, surah_name="Al-Fatihah", from_ayah=1, to_ayah=7,
                duration_seconds=30, expected_min_seconds=20, expected_max_seconds=40,
                within_expected_range=True,
            )
        )
    db_session.flush()

    xp = compute_xp(db_session, student)
    assert xp.from_practice == 3 * XP_PER_PRACTICE_ATTEMPT
    assert xp.total == xp.from_practice


def test_compute_xp_includes_completed_sabaqs_and_streak(db_session):
    student = make_student(db_session, email="b@example.com")
    student.longest_streak = 10
    db_session.add(
        Sabaq(
            student_id=student.id, surah_number=1, surah_name="Al-Fatihah",
            from_ayah=1, to_ayah=7, assigned_date=today(), status="completed", score=90,
        )
    )
    db_session.flush()

    xp = compute_xp(db_session, student)
    assert xp.from_sabaqs == XP_PER_COMPLETED_SABAQ
    assert xp.from_streak == 10 * 2  # XP_PER_STREAK_DAY
    assert xp.total == xp.from_sabaqs + xp.from_streak


def test_achievement_first_sabaq_awarded_once_completed(db_session):
    student = make_student(db_session, email="c@example.com")
    newly_earned = check_and_award_achievements(db_session, student)
    assert "first_sabaq" not in {a.achievement_key for a in newly_earned}

    db_session.add(
        Sabaq(
            student_id=student.id, surah_number=1, surah_name="Al-Fatihah",
            from_ayah=1, to_ayah=7, assigned_date=today(), status="completed", score=90,
        )
    )
    db_session.flush()

    newly_earned = check_and_award_achievements(db_session, student)
    assert "first_sabaq" in {a.achievement_key for a in newly_earned}

    newly_earned_again = check_and_award_achievements(db_session, student)
    assert newly_earned_again == []


def test_achievement_perfect_test_requires_a_100_percent_session(db_session):
    student = make_student(db_session, email="d@example.com")
    db_session.add(
        TestSession(
            student_id=student.id, surah_number=1, surah_name="Al-Fatihah",
            from_ayah=1, to_ayah=7, score_percent=80,
        )
    )
    db_session.flush()

    newly_earned = check_and_award_achievements(db_session, student)
    keys = {a.achievement_key for a in newly_earned}
    assert "first_test" in keys
    assert "perfect_test" not in keys

    db_session.add(
        TestSession(
            student_id=student.id, surah_number=1, surah_name="Al-Fatihah",
            from_ayah=1, to_ayah=7, score_percent=100,
        )
    )
    db_session.flush()

    newly_earned = check_and_award_achievements(db_session, student)
    assert "perfect_test" in {a.achievement_key for a in newly_earned}


def test_achievement_streak_thresholds(db_session):
    student = make_student(db_session, email="e@example.com")
    student.longest_streak = 7
    newly_earned = check_and_award_achievements(db_session, student)
    keys = {a.achievement_key for a in newly_earned}
    assert "streak_7" in keys
    assert "streak_30" not in keys
