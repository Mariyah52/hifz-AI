from app.models.lesson import Sabaq
from app.models.user import TeacherProfile
from app.services.certificate_service import _covered_ayahs, issue_certificate
from tests.conftest import make_student, make_user


def _sabaq(from_ayah, to_ayah):
    return Sabaq(
        student_id="stu_x", surah_number=1, surah_name="Al-Fatihah",
        from_ayah=from_ayah, to_ayah=to_ayah, assigned_date=None, status="completed",
    )


def test_covered_ayahs_unions_ranges():
    sabaqs = [_sabaq(1, 3), _sabaq(5, 7)]
    assert _covered_ayahs(sabaqs) == {1, 2, 3, 5, 6, 7}


def test_covered_ayahs_handles_overlap():
    sabaqs = [_sabaq(1, 5), _sabaq(3, 7)]
    assert _covered_ayahs(sabaqs) == set(range(1, 8))


def test_covered_ayahs_full_surah_coverage():
    sabaqs = [_sabaq(1, 4), _sabaq(5, 7)]
    assert _covered_ayahs(sabaqs) >= set(range(1, 8))


def test_issue_certificate_records_teacher_as_issuer(db_session):
    student = make_student(db_session, email="certstudent@example.com")
    teacher_user = make_user(db_session, email="certteacher@example.com", role="teacher")
    teacher = TeacherProfile(user_id=teacher_user.id)
    db_session.add(teacher)
    db_session.flush()

    cert = issue_certificate(
        db_session, student.id, "attendance", "5 Live Classes Attended",
        "Attended 5 live class sessions.", teacher.id,
    )

    assert cert.type == "attendance"
    assert cert.issued_by_teacher_id == teacher.id
