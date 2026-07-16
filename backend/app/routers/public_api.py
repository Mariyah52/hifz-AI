import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_api_key, require_api_scope
from app.models.api_access import ApiKey
from app.models.classroom import ClassRoom
from app.models.external_records import ExternalAttendanceRecord, ExternalGradeRecord
from app.models.organization import Organization
from app.models.user import StudentProfile, User
from app.rate_limit import limiter
from app.schemas.api_access import (
    AttendanceRecordOut,
    CreateAttendanceRequest,
    CreatedStudentOut,
    CreateGradeRequest,
    CreateStudentRequest,
    GradeRecordOut,
    PublicClassOut,
    PublicStudentOut,
    UpdateStudentRequest,
)
from app.schemas.progress import ProgressSummary
from app.security import hash_password
from app.services.progress_analytics import build_progress_summary
from app.services.tenancy import PlanLimitExceeded, enforce_plan_limit
from app.services.webhooks import dispatch_event

router = APIRouter(prefix="/v1", tags=["public-api"])

"""
Phase 30: the actual external-facing API — a school's own ERP, a
mosque's systems, or an LMS authenticate with an `X-API-Key` header
(issued and revocable from the Admin Portal's Developer API page)
instead of a student/teacher/admin login. Every read endpoint here is
scoped to the key's own organization via `get_api_key` — the same
tenant-boundary discipline Phase 18 established for the admin router,
just keyed off an API key's organization instead of a logged-in user's.

Phase 31 adds real write endpoints, gated behind `require_api_scope`
("write") on top of `get_api_key` — a key issued before this phase (or
deliberately kept read-only) gets a 403, not silent write access. See
ApiKey.scopes and deps.require_api_scope.
"""


def _generate_temporary_password() -> str:
    return secrets.token_urlsafe(12)


@router.get("/students", response_model=list[PublicStudentOut])
@limiter.limit("60/minute")
def list_students(
    request: Request, api_key: ApiKey = Depends(get_api_key), db: Session = Depends(get_db)
) -> list[PublicStudentOut]:
    students = (
        db.query(StudentProfile)
        .join(User, User.id == StudentProfile.user_id)
        .filter(User.organization_id == api_key.organization_id)
        .all()
    )
    class_names = {
        c.id: c.name
        for c in db.query(ClassRoom).filter(ClassRoom.organization_id == api_key.organization_id).all()
    }
    return [
        PublicStudentOut(
            id=s.id,
            name=s.user.name,
            class_name=class_names.get(s.class_id) if s.class_id else None,
            current_streak=s.current_streak,
            longest_streak=s.longest_streak,
        )
        for s in students
    ]


@router.get("/students/{student_id}/progress", response_model=ProgressSummary)
@limiter.limit("60/minute")
def get_student_progress(
    request: Request,
    student_id: str,
    api_key: ApiKey = Depends(get_api_key),
    db: Session = Depends(get_db),
) -> ProgressSummary:
    """Reuses Phase 6/21's exact `build_progress_summary` — an ERP sees the same real numbers the student's own Progress page shows, no parallel computation."""
    student = db.get(StudentProfile, student_id)
    if student is None or student.user.organization_id != api_key.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found in this organization")
    return build_progress_summary(db, student)


@router.get("/classes", response_model=list[PublicClassOut])
@limiter.limit("60/minute")
def list_classes(
    request: Request, api_key: ApiKey = Depends(get_api_key), db: Session = Depends(get_db)
) -> list[PublicClassOut]:
    classes = db.query(ClassRoom).filter(ClassRoom.organization_id == api_key.organization_id).all()
    out = []
    for c in classes:
        student_count = db.query(StudentProfile).filter(StudentProfile.class_id == c.id).count()
        out.append(
            PublicClassOut(
                id=c.id, name=c.name, teacher_name=c.teacher.user.name if c.teacher else None,
                student_count=student_count,
            )
        )
    return out


# --- Write endpoints (require 'write' scope) -----------------------------


def _get_own_student(db: Session, api_key: ApiKey, student_id: str) -> StudentProfile:
    student = db.get(StudentProfile, student_id)
    if student is None or student.user.organization_id != api_key.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found in this organization")
    return student


@router.post("/students", response_model=CreatedStudentOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_student(
    request: Request,
    payload: CreateStudentRequest,
    background_tasks: BackgroundTasks,
    api_key: ApiKey = Depends(require_api_scope("write")),
    db: Session = Depends(get_db),
) -> CreatedStudentOut:
    """
    Creates a real student account, same underlying User + StudentProfile
    rows /auth/register creates — an LMS-provisioned student can log into
    HifzAI directly with the returned temporary password (and should be
    prompted to change it; this API doesn't force that itself, since
    there's no forced-password-change flow built anywhere in this app yet).
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    organization = db.get(Organization, api_key.organization_id)
    try:
        enforce_plan_limit(db, organization, "student")
    except PlanLimitExceeded as exc:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, str(exc)) from exc

    if payload.class_id is not None:
        class_room = db.get(ClassRoom, payload.class_id)
        if class_room is None or class_room.organization_id != api_key.organization_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "classId does not exist in this organization")

    temporary_password = _generate_temporary_password()
    user = User(
        organization_id=api_key.organization_id,
        email=payload.email,
        hashed_password=hash_password(temporary_password),
        name=payload.name,
        role="student",
    )
    db.add(user)
    db.flush()
    student = StudentProfile(user_id=user.id, class_id=payload.class_id)
    db.add(student)
    db.commit()
    db.refresh(user)

    background_tasks.add_task(
        dispatch_event, db, api_key.organization_id, "student.created",
        {"studentId": student.id, "name": user.name, "classId": payload.class_id},
    )

    return CreatedStudentOut(id=student.id, email=user.email, name=user.name, temporary_password=temporary_password)


@router.patch("/students/{student_id}", response_model=PublicStudentOut)
@limiter.limit("60/minute")
def update_student(
    request: Request,
    student_id: str,
    payload: UpdateStudentRequest,
    api_key: ApiKey = Depends(require_api_scope("write")),
    db: Session = Depends(get_db),
) -> PublicStudentOut:
    student = _get_own_student(db, api_key, student_id)

    if payload.name is not None:
        student.user.name = payload.name
    if payload.class_id is not None:
        class_room = db.get(ClassRoom, payload.class_id)
        if class_room is None or class_room.organization_id != api_key.organization_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "classId does not exist in this organization")
        student.class_id = payload.class_id

    db.commit()
    db.refresh(student)
    class_name = student.class_.name if student.class_id and student.class_ else None
    return PublicStudentOut(
        id=student.id, name=student.user.name, class_name=class_name,
        current_streak=student.current_streak, longest_streak=student.longest_streak,
    )


@router.post(
    "/students/{student_id}/attendance", response_model=AttendanceRecordOut, status_code=status.HTTP_201_CREATED
)
@limiter.limit("120/minute")
def push_attendance(
    request: Request,
    student_id: str,
    payload: CreateAttendanceRequest,
    api_key: ApiKey = Depends(require_api_scope("write")),
    db: Session = Depends(get_db),
) -> AttendanceRecordOut:
    """
    Records an attendance event an external LMS/ERP reports for this
    student. Deliberately stored separately from this app's own real,
    automatic LiveSessionParticipant attendance — see
    models/external_records.py's docstring for why conflating the two
    would be misleading, not simplifying.
    """
    student = _get_own_student(db, api_key, student_id)
    record = ExternalAttendanceRecord(
        student_id=student.id, api_key_id=api_key.id, session_date=payload.session_date,
        status=payload.status, source_label=payload.source_label, note=payload.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return AttendanceRecordOut(
        id=record.id, student_id=record.student_id, session_date=record.session_date,
        status=record.status, source_label=record.source_label, note=record.note,
        created_at=record.created_at,
    )


@router.post("/students/{student_id}/grades", response_model=GradeRecordOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("120/minute")
def push_grade(
    request: Request,
    student_id: str,
    payload: CreateGradeRequest,
    api_key: ApiKey = Depends(require_api_scope("write")),
    db: Session = Depends(get_db),
) -> GradeRecordOut:
    """Same provenance reasoning as push_attendance — a grade an external system reports, kept separate from this app's own real TestSession scores."""
    student = _get_own_student(db, api_key, student_id)
    record = ExternalGradeRecord(
        student_id=student.id, api_key_id=api_key.id, label=payload.label, score=payload.score,
        max_score=payload.max_score, recorded_date=payload.recorded_date, note=payload.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return GradeRecordOut(
        id=record.id, student_id=record.student_id, label=record.label, score=record.score,
        max_score=record.max_score, recorded_date=record.recorded_date, note=record.note,
        created_at=record.created_at,
    )
