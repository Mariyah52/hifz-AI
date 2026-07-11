from app.models.review import ReviewSchedule
from app.models.test import TestResult, TestSession
from app.models.user import today
from app.services.analytics import (
    _accuracy,
    _confidence_score,
    _most_forgotten_ayah,
    _retention_rate,
    _weakest_surah,
)
from tests.conftest import make_student


def _result(mark: str) -> TestResult:
    return TestResult(ayah_number=1, mark=mark, matched_word_count=8 if mark == "correct" else 5, total_word_count=8)


def test_accuracy_empty_is_zero():
    assert _accuracy([]) == 0.0


def test_accuracy_computes_correct_ratio():
    results = [_result("correct"), _result("correct"), _result("missed"), _result("correct")]
    assert _accuracy(results) == 75.0


def test_weakest_surah_requires_minimum_attempts():
    per_surah = {
        (1, "Al-Fatihah"): [_result("missed")],
        (2, "Al-Baqarah"): [_result("correct"), _result("missed")],
    }
    weakest = _weakest_surah(per_surah)
    assert weakest is not None
    assert weakest.surah_number == 2


def test_weakest_surah_picks_lowest_accuracy():
    per_surah = {
        (1, "Al-Fatihah"): [_result("correct"), _result("correct")],
        (2, "Al-Baqarah"): [_result("missed"), _result("missed")],
    }
    weakest = _weakest_surah(per_surah)
    assert weakest.surah_number == 2
    assert weakest.accuracy == 0.0


def test_weakest_surah_none_when_no_surah_has_enough_attempts():
    per_surah = {(1, "Al-Fatihah"): [_result("missed")]}
    assert _weakest_surah(per_surah) is None


def test_most_forgotten_ayah_picks_lowest_accuracy_with_min_attempts():
    per_ayah = {
        (2, "Al-Baqarah", 5): [_result("correct"), _result("correct")],
        (2, "Al-Baqarah", 255): [_result("missed"), _result("missed"), _result("correct")],
    }
    forgotten = _most_forgotten_ayah(per_ayah)
    assert forgotten.ayah_number == 255
    assert forgotten.missed_count == 2


def test_retention_rate_none_when_nothing_reviewed(db_session):
    student = make_student(db_session, email="ret1@example.com")
    assert _retention_rate(db_session, student.id) is None


def test_retention_rate_computes_percentage_with_quality_at_least_3(db_session):
    student = make_student(db_session, email="ret2@example.com")
    db_session.add_all(
        [
            ReviewSchedule(sabaq_id="sbq_a", student_id=student.id, due_date=today(), last_quality=4),
            ReviewSchedule(sabaq_id="sbq_b", student_id=student.id, due_date=today(), last_quality=2),
            ReviewSchedule(sabaq_id="sbq_c", student_id=student.id, due_date=today(), last_quality=5),
            ReviewSchedule(sabaq_id="sbq_d", student_id=student.id, due_date=today(), last_quality=None),
        ]
    )
    db_session.flush()

    rate = _retention_rate(db_session, student.id)
    assert rate == round(2 / 3 * 100, 1)


def test_confidence_score_none_without_retention_rate():
    assert _confidence_score(None, 90.0) is None


def test_confidence_score_is_documented_weighted_blend():
    score = _confidence_score(retention_rate=80.0, overall_accuracy=90.0)
    assert score == round(0.6 * 80.0 + 0.4 * 90.0, 1)


def test_accuracy_end_to_end_from_real_rows(db_session):
    student = make_student(db_session, email="acc@example.com")
    session = TestSession(
        student_id=student.id, surah_number=1, surah_name="Al-Fatihah", from_ayah=1, to_ayah=3, score_percent=67,
    )
    db_session.add(session)
    db_session.flush()
    db_session.add_all(
        [
            TestResult(session_id=session.id, ayah_number=1, mark="correct", matched_word_count=5, total_word_count=5),
            TestResult(session_id=session.id, ayah_number=2, mark="correct", matched_word_count=6, total_word_count=6),
            TestResult(session_id=session.id, ayah_number=3, mark="missed", matched_word_count=4, total_word_count=7),
        ]
    )
    db_session.flush()

    results = db_session.query(TestResult).filter(TestResult.session_id == session.id).all()
    assert _accuracy(results) == round(2 / 3 * 100, 1)
