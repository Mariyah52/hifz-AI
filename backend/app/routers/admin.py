from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.auth_security import AuditLogEntry
from app.models.classroom import ClassRoom
from app.models.feedback import TeacherFeedback
from app.models.organization import Organization
from app.models.test import TestSession
from app.models.user import StudentProfile, TeacherProfile, User
from app.schemas.admin import (
    AdminAnalyticsOut,
    AssignClassRequest,
    AuditLogEntryOut,
    ClassSummaryOut,
    CreateClassRequest,
    TeacherOut,
)
from app.schemas.communication import AnnouncementOut, CreateAnnouncementRequest
from app.schemas.organization import OrganizationAdminOut, UpdateOrganizationRequest
from app.schemas.teacher import StudentOut
from app.services.messaging_service import create_announcement
from app.services.student_view import get_todays_sabaq, to_student_out
from app.services.tenancy import count_users_by_role

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])


def _students_in_org(db: Session, organization_id: str) -> list[StudentProfile]:
    """Every query below is scoped to the requesting admin's own organization_id — the tenant boundary."""
    return (
        db.query(StudentProfile)
        .join(User, User.id == StudentProfile.user_id)
        .filter(User.organization_id == organization_id)
        .all()
    )


@router.get("/teachers", response_model=list[TeacherOut])
def list_teachers(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[TeacherOut]:
    teachers = (
        db.query(TeacherProfile)
        .join(User, User.id == TeacherProfile.user_id)
        .filter(User.organization_id == admin.organization_id)
        .all()
    )
    return [TeacherOut(id=t.id, name=t.user.name, class_ids=[c.id for c in t.classes]) for t in teachers]


@router.get("/classes", response_model=list[ClassSummaryOut])
def list_classes(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[ClassSummaryOut]:
    classes = db.query(ClassRoom).filter(ClassRoom.organization_id == admin.organization_id).all()
    out = []
    for c in classes:
        students = db.query(StudentProfile).filter(StudentProfile.class_id == c.id).all()
        average_streak = round(sum(s.current_streak for s in students) / len(students)) if students else 0
        out.append(
            ClassSummaryOut(
                id=c.id,
                name=c.name,
                teacher_name=c.teacher.user.name if c.teacher else None,
                student_count=len(students),
                average_streak=average_streak,
            )
        )
    return out


@router.get("/students", response_model=list[StudentOut])
def list_all_students(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[StudentOut]:
    students = _students_in_org(db, admin.organization_id)
    return [to_student_out(s, get_todays_sabaq(db, s.id)) for s in students]


@router.get("/analytics", response_model=AdminAnalyticsOut)
def get_analytics(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> AdminAnalyticsOut:
    students = _students_in_org(db, admin.organization_id)
    student_ids = {s.id for s in students}

    total_teachers = count_users_by_role(db, admin.organization_id, "teacher")
    total_classes = db.query(ClassRoom).filter(ClassRoom.organization_id == admin.organization_id).count()

    total_feedback_given = db.query(TeacherFeedback).filter(TeacherFeedback.student_id.in_(student_ids)).count()
    total_sabaqs_assigned = sum(1 for s in students if get_todays_sabaq(db, s.id) is not None)

    sessions = db.query(TestSession).filter(TestSession.student_id.in_(student_ids)).all()
    average_test_score = round(sum(s.score_percent for s in sessions) / len(sessions)) if sessions else None

    students_needing_attention = [s for s in students if s.current_streak == 0]

    return AdminAnalyticsOut(
        total_students=len(students),
        total_teachers=total_teachers,
        total_classes=total_classes,
        total_feedback_given=total_feedback_given,
        total_sabaqs_assigned=total_sabaqs_assigned,
        average_test_score=average_test_score,
        students_needing_attention=[
            to_student_out(s, get_todays_sabaq(db, s.id)) for s in students_needing_attention
        ],
    )


@router.post("/classes", response_model=ClassSummaryOut, status_code=status.HTTP_201_CREATED)
def create_class(
    payload: CreateClassRequest, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> ClassSummaryOut:
    if payload.teacher_id:
        teacher = db.get(TeacherProfile, payload.teacher_id)
        # A teacher can only be assigned to a class in their OWN organization.
        if teacher is None or teacher.user.organization_id != admin.organization_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "teacher_id does not exist in this organization")

    class_room = ClassRoom(name=payload.name, teacher_id=payload.teacher_id, organization_id=admin.organization_id)
    db.add(class_room)
    db.commit()
    db.refresh(class_room)
    return ClassSummaryOut(
        id=class_room.id,
        name=class_room.name,
        teacher_name=class_room.teacher.user.name if class_room.teacher else None,
        student_count=0,
        average_streak=0,
    )


@router.post("/students/{student_id}/class", response_model=StudentOut)
def assign_student_class(
    student_id: str,
    payload: AssignClassRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> StudentOut:
    student = db.get(StudentProfile, student_id)
    if student is None or student.user.organization_id != admin.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found in this organization")

    class_room = db.get(ClassRoom, payload.class_id)
    if class_room is None or class_room.organization_id != admin.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found in this organization")

    student.class_id = payload.class_id
    db.commit()
    db.refresh(student)
    return to_student_out(student, get_todays_sabaq(db, student.id))


@router.get("/audit-log", response_model=list[AuditLogEntryOut])
def list_audit_log(
    limit: int = 100, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> list[AuditLogEntryOut]:
    """
    The security audit trail from Phase 17, scoped to this admin's own
    organization (Phase 18) — every row here corresponds to a real event
    `services/auth_security.py` logged for a user in this org at the time
    it happened, not reconstructed after the fact and not visible across
    tenant boundaries.
    """
    org_user_ids = {u.id for u in db.query(User).filter(User.organization_id == admin.organization_id).all()}
    entries = (
        db.query(AuditLogEntry)
        .filter(AuditLogEntry.user_id.in_(org_user_ids))
        .order_by(AuditLogEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    user_emails = {
        u.id: u.email for u in db.query(User).filter(User.id.in_({e.user_id for e in entries if e.user_id})).all()
    }
    return [
        AuditLogEntryOut(
            id=e.id,
            user_email=user_emails.get(e.user_id) if e.user_id else None,
            action=e.action,
            ip_address=e.ip_address,
            detail=e.detail,
            created_at=e.created_at,
        )
        for e in entries
    ]


@router.get("/organization", response_model=OrganizationAdminOut)
def get_my_organization(
    admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> OrganizationAdminOut:
    organization = db.get(Organization, admin.organization_id)
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")

    return OrganizationAdminOut(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        plan=organization.plan,
        max_students=organization.max_students,
        max_teachers=organization.max_teachers,
        current_student_count=count_users_by_role(db, organization.id, "student"),
        current_teacher_count=count_users_by_role(db, organization.id, "teacher"),
        primary_color=organization.primary_color,
        logo_url=organization.logo_url,
    )


@router.patch("/organization", response_model=OrganizationAdminOut)
def update_my_organization(
    payload: UpdateOrganizationRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> OrganizationAdminOut:
    """Name/branding only — plan and seat limits aren't editable here (no self-serve billing; see README)."""
    organization = db.get(Organization, admin.organization_id)
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found")

    if payload.name is not None:
        organization.name = payload.name
    if payload.primary_color is not None:
        organization.primary_color = payload.primary_color
    if payload.logo_url is not None:
        organization.logo_url = payload.logo_url

    db.commit()
    db.refresh(organization)
    return OrganizationAdminOut(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        plan=organization.plan,
        max_students=organization.max_students,
        max_teachers=organization.max_teachers,
        current_student_count=count_users_by_role(db, organization.id, "student"),
        current_teacher_count=count_users_by_role(db, organization.id, "teacher"),
        primary_color=organization.primary_color,
        logo_url=organization.logo_url,
    )


@router.post("/announcements", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def post_institution_announcement(
    payload: CreateAnnouncementRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> AnnouncementOut:
    """Institution-wide only — an admin posting to one specific class isn't supported here; that's a teacher's job."""
    announcement = create_announcement(db, admin.organization_id, admin.id, payload.title, payload.content, None)
    return AnnouncementOut(
        id=announcement.id, class_id=None, class_name=None, author_name=admin.name,
        title=announcement.title, content=announcement.content, created_at=announcement.created_at,
    )
