from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_api_key
from app.models.api_access import ApiKey
from app.models.classroom import ClassRoom
from app.models.user import StudentProfile, User
from app.rate_limit import limiter
from app.schemas.api_access import PublicClassOut, PublicStudentOut
from app.schemas.progress import ProgressSummary
from app.services.progress_analytics import build_progress_summary

router = APIRouter(prefix="/v1", tags=["public-api"])

"""
Phase 30: the actual external-facing API — a school's own ERP, a
mosque's systems, or an LMS authenticate with an `X-API-Key` header
(issued and revocable from the Admin Portal's Developer API page)
instead of a student/teacher/admin login. Every endpoint here is
read-only and scoped to the key's own organization via `get_api_key` —
the same tenant-boundary discipline Phase 18 established for the admin
router, just keyed off an API key's organization instead of a logged-in
user's. **No write endpoints exist yet** — an ERP pushing attendance or
grades back into HifzAI would be a real, separate, larger piece of work;
this phase's actual scope is read-only integration, stated as such
rather than implied to be more.
"""


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
