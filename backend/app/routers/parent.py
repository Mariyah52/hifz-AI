from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_parent_profile
from app.models.classroom import ParentChildLink
from app.models.feedback import TeacherFeedback
from app.models.user import ParentProfile, StudentProfile
from app.schemas.lesson import SabaqOut
from app.schemas.parent import ChildOverviewOut
from app.schemas.teacher import StudentOut
from app.services.progress_analytics import build_progress_summary
from app.services.student_view import (
    get_recent_sabaqs,
    get_todays_sabaq,
    to_feedback_out,
    to_streak_info,
    to_student_out,
)

router = APIRouter(prefix="/parent", tags=["parent"])


def _linked_children(db: Session, parent: ParentProfile) -> list[StudentProfile]:
    links = db.query(ParentChildLink).filter(ParentChildLink.parent_id == parent.id).all()
    student_ids = [link.student_id for link in links]
    if not student_ids:
        return []
    return db.query(StudentProfile).filter(StudentProfile.id.in_(student_ids)).all()


def _get_child_in_scope(db: Session, parent: ParentProfile, student_id: str) -> StudentProfile:
    allowed_ids = {s.id for s in _linked_children(db, parent)}
    if student_id not in allowed_ids:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No linked child with that id")
    return db.get(StudentProfile, student_id)


@router.get("/children", response_model=list[StudentOut])
def list_children(
    parent: ParentProfile = Depends(get_current_parent_profile), db: Session = Depends(get_db)
) -> list[StudentOut]:
    """
    The real version of Phase 8's hardcoded `LINKED_CHILD_STUDENT_ID` — a
    parent can now be linked to any number of real students via
    `ParentChildLink`, set up at registration or by an admin, instead of
    the frontend always pointing at the same mock `stu_1`.
    """
    children = _linked_children(db, parent)
    return [to_student_out(s, get_todays_sabaq(db, s.id)) for s in children]


@router.get("/children/{student_id}/overview", response_model=ChildOverviewOut)
def get_child_overview(
    student_id: str,
    parent: ParentProfile = Depends(get_current_parent_profile),
    db: Session = Depends(get_db),
) -> ChildOverviewOut:
    student = _get_child_in_scope(db, parent, student_id)
    todays_sabaq = get_todays_sabaq(db, student.id)
    recent = get_recent_sabaqs(db, student.id, limit=5, exclude_id=todays_sabaq.id if todays_sabaq else None)
    progress = build_progress_summary(db, student)
    feedback = (
        db.query(TeacherFeedback)
        .filter(TeacherFeedback.student_id == student.id)
        .order_by(TeacherFeedback.created_at.desc())
        .all()
    )

    return ChildOverviewOut(
        student_id=student.id,
        name=student.user.name,
        class_id=student.class_id,
        streak=to_streak_info(student),
        todays_sabaq=SabaqOut.model_validate(todays_sabaq) if todays_sabaq else None,
        recent_sabaqs=[SabaqOut.model_validate(s) for s in recent],
        progress=progress,
        feedback=[to_feedback_out(f) for f in feedback],
    )
