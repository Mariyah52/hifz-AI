from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_teacher_profile
from app.models.classroom import ClassRoom
from app.models.feedback import TeacherFeedback
from app.models.certificate import Certificate
from app.models.lesson import Sabaq
from app.models.live_session import LiveSession
from app.models.organization import Organization
from app.models.user import StudentProfile, TeacherProfile
from app.schemas.certificate import CertificateOut, IssueCertificateRequest
from app.schemas.communication import AnnouncementOut, CreateAnnouncementRequest, CreateHomeworkRequest, HomeworkOut
from app.schemas.lesson import AssignSabaqRequest, SabaqOut
from app.schemas.live_session import LiveSessionOut, LiveSessionReportOut, StartLiveSessionRequest
from app.schemas.teacher import AddFeedbackRequest, StudentDetailOut, StudentOut, TeacherClassOut, TeacherFeedbackOut
from app.services.notification_service import create_notification
from app.services.certificate_service import issue_certificate, render_certificate_pdf
from app.services.messaging_service import create_announcement, create_homework
from app.services.live_session_service import (
    LiveSessionError,
    build_report,
    end_session,
    start_session,
    to_session_out,
)
from app.services.student_view import build_student_detail, get_todays_sabaq, to_feedback_out, to_student_out

router = APIRouter(prefix="/teacher", tags=["teacher"])


def _students_for_teacher(db: Session, teacher: TeacherProfile) -> list[StudentProfile]:
    """
    Real class-scoped roster: a teacher only sees students enrolled in a
    class they teach. This replaces Phase 7's flat mock roster (which
    showed every mock student to whichever teacher was viewing) with an
    actual multi-tenant boundary, now that real accounts and classes exist.
    """
    class_ids = [c.id for c in db.query(ClassRoom).filter(ClassRoom.teacher_id == teacher.id).all()]
    if not class_ids:
        return []
    return db.query(StudentProfile).filter(StudentProfile.class_id.in_(class_ids)).all()


def _get_student_in_scope(db: Session, teacher: TeacherProfile, student_id: str) -> StudentProfile:
    student = db.get(StudentProfile, student_id)
    allowed_ids = {s.id for s in _students_for_teacher(db, teacher)}
    if student is None or student.id not in allowed_ids:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found in your classes")
    return student


@router.get("/roster", response_model=list[StudentOut])
def get_roster(
    teacher: TeacherProfile = Depends(get_current_teacher_profile), db: Session = Depends(get_db)
) -> list[StudentOut]:
    students = _students_for_teacher(db, teacher)
    return [to_student_out(s, get_todays_sabaq(db, s.id)) for s in students]


@router.get("/classes", response_model=list[TeacherClassOut])
def get_my_classes(
    teacher: TeacherProfile = Depends(get_current_teacher_profile), db: Session = Depends(get_db)
) -> list[TeacherClassOut]:
    classes = db.query(ClassRoom).filter(ClassRoom.teacher_id == teacher.id).all()
    return [TeacherClassOut(id=c.id, name=c.name) for c in classes]


@router.get("/students/{student_id}", response_model=StudentDetailOut)
def get_student_detail(
    student_id: str,
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db),
) -> StudentDetailOut:
    student = _get_student_in_scope(db, teacher, student_id)
    return build_student_detail(db, student)


@router.post("/students/{student_id}/sabaq", response_model=SabaqOut, status_code=status.HTTP_201_CREATED)
def assign_sabaq(
    student_id: str,
    payload: AssignSabaqRequest,
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db),
) -> SabaqOut:
    student = _get_student_in_scope(db, teacher, student_id)
    sabaq = Sabaq(
        student_id=student.id,
        surah_number=payload.surah_number,
        surah_name=payload.surah_name,
        from_ayah=payload.from_ayah,
        to_ayah=payload.to_ayah,
        status="not_started",
    )
    db.add(sabaq)
    db.commit()
    db.refresh(sabaq)

    create_notification(
        db, student.user_id, "sabaq_assigned", "New Sabaq assigned",
        f"{payload.surah_name} {payload.from_ayah}-{payload.to_ayah}",
        related_id=sabaq.id,
    )

    return SabaqOut.model_validate(sabaq)


@router.post(
    "/students/{student_id}/feedback", response_model=TeacherFeedbackOut, status_code=status.HTTP_201_CREATED
)
def add_feedback(
    student_id: str,
    payload: AddFeedbackRequest,
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db),
) -> TeacherFeedbackOut:
    student = _get_student_in_scope(db, teacher, student_id)
    feedback = TeacherFeedback(student_id=student.id, teacher_id=teacher.id, note=payload.note)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    create_notification(
        db, student.user_id, "teacher_feedback", "New feedback from your teacher",
        payload.note, related_id=feedback.id,
    )

    return to_feedback_out(feedback)


@router.post("/live-sessions", response_model=LiveSessionOut, status_code=status.HTTP_201_CREATED)
def create_live_session(
    payload: StartLiveSessionRequest,
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db),
) -> LiveSessionOut:
    try:
        session = start_session(db, teacher, payload.class_id)
    except LiveSessionError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return to_session_out(session)


def _get_own_session(db: Session, teacher: TeacherProfile, session_id: str) -> LiveSession:
    session = db.get(LiveSession, session_id)
    if session is None or session.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Live session not found")
    return session


@router.get("/live-sessions/active", response_model=LiveSessionOut | None)
def get_my_active_session(
    teacher: TeacherProfile = Depends(get_current_teacher_profile), db: Session = Depends(get_db)
) -> LiveSessionOut | None:
    session = (
        db.query(LiveSession)
        .filter(LiveSession.teacher_id == teacher.id, LiveSession.status == "live")
        .order_by(LiveSession.started_at.desc())
        .first()
    )
    return to_session_out(session) if session else None


@router.post("/live-sessions/{session_id}/end", response_model=LiveSessionReportOut)
def end_live_session(
    session_id: str, teacher: TeacherProfile = Depends(get_current_teacher_profile), db: Session = Depends(get_db)
) -> LiveSessionReportOut:
    session = _get_own_session(db, teacher, session_id)
    ended = end_session(db, session)
    return build_report(db, ended)


@router.get("/live-sessions/{session_id}/report", response_model=LiveSessionReportOut)
def get_live_session_report(
    session_id: str, teacher: TeacherProfile = Depends(get_current_teacher_profile), db: Session = Depends(get_db)
) -> LiveSessionReportOut:
    session = _get_own_session(db, teacher, session_id)
    return build_report(db, session)


@router.post(
    "/students/{student_id}/certificates", response_model=CertificateOut, status_code=status.HTTP_201_CREATED
)
def issue_student_certificate(
    student_id: str,
    payload: IssueCertificateRequest,
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db),
) -> CertificateOut:
    """
    Attendance and competition certificates need a human judgment call
    (which milestone, which standing) — unlike surah/juz completion,
    which are auto-detected. See services/certificate_service.py.
    """
    student = _get_student_in_scope(db, teacher, student_id)
    certificate = issue_certificate(db, student.id, payload.type, payload.title, payload.detail, teacher.id)
    return CertificateOut(
        id=certificate.id, type=certificate.type, title=certificate.title, detail=certificate.detail,
        issued_by_teacher_name=teacher.user.name, issued_at=certificate.issued_at,
    )


@router.get("/students/{student_id}/certificates", response_model=list[CertificateOut])
def list_student_certificates(
    student_id: str, teacher: TeacherProfile = Depends(get_current_teacher_profile), db: Session = Depends(get_db)
) -> list[CertificateOut]:
    student = _get_student_in_scope(db, teacher, student_id)
    certificates = (
        db.query(Certificate).filter(Certificate.student_id == student.id).order_by(Certificate.issued_at.desc()).all()
    )
    return [
        CertificateOut(
            id=c.id, type=c.type, title=c.title, detail=c.detail,
            issued_by_teacher_name=c.issued_by_teacher.user.name if c.issued_by_teacher else None,
            issued_at=c.issued_at,
        )
        for c in certificates
    ]


@router.get("/certificates/{certificate_id}/pdf")
async def get_student_certificate_pdf(
    certificate_id: str, teacher: TeacherProfile = Depends(get_current_teacher_profile), db: Session = Depends(get_db)
) -> Response:
    certificate = db.get(Certificate, certificate_id)
    if certificate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificate not found")
    student = _get_student_in_scope(db, teacher, certificate.student_id)

    organization = db.get(Organization, student.user.organization_id)
    pdf_bytes = await render_certificate_pdf(certificate, student.user.name, organization)
    return Response(content=pdf_bytes, media_type="application/pdf")


def _get_own_class(db: Session, teacher: TeacherProfile, class_id: str) -> ClassRoom:
    class_room = db.get(ClassRoom, class_id)
    if class_room is None or class_room.teacher_id != teacher.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    return class_room


@router.post("/announcements", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def post_announcement(
    payload: CreateAnnouncementRequest,
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db),
) -> AnnouncementOut:
    if not payload.class_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Teachers post to one of their own classes, not institution-wide.")
    class_room = _get_own_class(db, teacher, payload.class_id)
    announcement = create_announcement(
        db, teacher.user.organization_id, teacher.user_id, payload.title, payload.content, class_room.id
    )
    return AnnouncementOut(
        id=announcement.id, class_id=class_room.id, class_name=class_room.name,
        author_name=teacher.user.name, title=announcement.title, content=announcement.content,
        created_at=announcement.created_at,
    )


@router.post("/homework", response_model=HomeworkOut, status_code=status.HTTP_201_CREATED)
def post_homework(
    payload: CreateHomeworkRequest,
    teacher: TeacherProfile = Depends(get_current_teacher_profile),
    db: Session = Depends(get_db),
) -> HomeworkOut:
    class_room = _get_own_class(db, teacher, payload.class_id)
    homework = create_homework(db, class_room.id, teacher.id, payload.title, payload.description, payload.due_date)
    return HomeworkOut(
        id=homework.id, class_id=class_room.id, class_name=class_room.name,
        title=homework.title, description=homework.description, due_date=homework.due_date,
        created_at=homework.created_at,
    )
