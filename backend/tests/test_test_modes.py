import pytest

from app.models.lesson import Sabaq
from app.models.user import today
from app.services.test_modes import NoContentAvailable, _completed_sabaqs, _pick_sabaq
from tests.conftest import make_student


def test_pick_sabaq_raises_when_no_completed_sabaqs(db_session):
    student = make_student(db_session, email="nosabaq@example.com")
    with pytest.raises(NoContentAvailable):
        _pick_sabaq(db_session, student.id, surah_number=None)


def test_pick_sabaq_ignores_in_progress_sabaqs(db_session):
    student = make_student(db_session, email="inprogress@example.com")
    db_session.add(
        Sabaq(
            student_id=student.id, surah_number=1, surah_name="Al-Fatihah",
            from_ayah=1, to_ayah=7, assigned_date=today(), status="in_progress",
        )
    )
    db_session.flush()
    with pytest.raises(NoContentAvailable):
        _pick_sabaq(db_session, student.id, surah_number=None)


def test_pick_sabaq_returns_a_completed_sabaq(db_session):
    student = make_student(db_session, email="completed@example.com")
    sabaq = Sabaq(
        student_id=student.id, surah_number=2, surah_name="Al-Baqarah",
        from_ayah=1, to_ayah=10, assigned_date=today(), status="completed", score=90,
    )
    db_session.add(sabaq)
    db_session.flush()

    picked = _pick_sabaq(db_session, student.id, surah_number=None)
    assert picked.id == sabaq.id


def test_pick_sabaq_filters_by_surah_number(db_session):
    student = make_student(db_session, email="filtered@example.com")
    db_session.add_all(
        [
            Sabaq(
                student_id=student.id, surah_number=1, surah_name="Al-Fatihah",
                from_ayah=1, to_ayah=7, assigned_date=today(), status="completed",
            ),
            Sabaq(
                student_id=student.id, surah_number=2, surah_name="Al-Baqarah",
                from_ayah=1, to_ayah=5, assigned_date=today(), status="completed",
            ),
        ]
    )
    db_session.flush()

    picked = _pick_sabaq(db_session, student.id, surah_number=2)
    assert picked.surah_number == 2


def test_completed_sabaqs_only_returns_this_students_own(db_session):
    student_a = make_student(db_session, email="a-modes@example.com")
    student_b = make_student(db_session, email="b-modes@example.com")
    db_session.add_all(
        [
            Sabaq(
                student_id=student_a.id, surah_number=1, surah_name="Al-Fatihah",
                from_ayah=1, to_ayah=7, assigned_date=today(), status="completed",
            ),
            Sabaq(
                student_id=student_b.id, surah_number=1, surah_name="Al-Fatihah",
                from_ayah=1, to_ayah=7, assigned_date=today(), status="completed",
            ),
        ]
    )
    db_session.flush()

    assert len(_completed_sabaqs(db_session, student_a.id)) == 1
