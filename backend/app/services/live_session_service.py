from sqlalchemy.orm import Session

from app.models.classroom import ClassRoom
from app.models.live_session import LiveSession, LiveSessionMistake, LiveSessionParticipant
from app.models.user import TeacherProfile, utcnow
from app.schemas.live_session import (
    LiveSessionMistakeOut,
    LiveSessionOut,
    LiveSessionParticipantOut,
    LiveSessionReportOut,
)


class LiveSessionError(Exception):
    pass


def get_active_session_for_class(db: Session, class_id: str) -> LiveSession | None:
    return (
        db.query(LiveSession)
        .filter(LiveSession.class_id == class_id, LiveSession.status == "live")
        .order_by(LiveSession.started_at.desc())
        .first()
    )


def start_session(db: Session, teacher: TeacherProfile, class_id: str) -> LiveSession:
    class_room = db.get(ClassRoom, class_id)
    if class_room is None or class_room.teacher_id != teacher.id:
        raise LiveSessionError("You can only start a session for your own class.")
    if get_active_session_for_class(db, class_id) is not None:
        raise LiveSessionError("This class already has a live session running.")

    session = LiveSession(class_id=class_id, teacher_id=teacher.id, status="live")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def end_session(db: Session, session: LiveSession) -> LiveSession:
    session.status = "ended"
    session.ended_at = utcnow()
    db.query(LiveSessionParticipant).filter(
        LiveSessionParticipant.session_id == session.id, LiveSessionParticipant.left_at.is_(None)
    ).update({"left_at": utcnow()})
    db.commit()
    db.refresh(session)
    return session


def record_join(db: Session, session_id: str, student_id: str) -> LiveSessionParticipant:
    participant = LiveSessionParticipant(session_id=session_id, student_id=student_id)
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def record_leave(db: Session, session_id: str, student_id: str) -> None:
    participant = (
        db.query(LiveSessionParticipant)
        .filter(
            LiveSessionParticipant.session_id == session_id,
            LiveSessionParticipant.student_id == student_id,
            LiveSessionParticipant.left_at.is_(None),
        )
        .order_by(LiveSessionParticipant.joined_at.desc())
        .first()
    )
    if participant is not None:
        participant.left_at = utcnow()
        db.commit()


def record_mistake(
    db: Session, session_id: str, student_id: str, mark_type: str, note: str | None
) -> LiveSessionMistake:
    mistake = LiveSessionMistake(session_id=session_id, student_id=student_id, mark_type=mark_type, note=note)
    db.add(mistake)
    db.commit()
    db.refresh(mistake)
    return mistake


def to_session_out(session: LiveSession) -> LiveSessionOut:
    return LiveSessionOut(
        id=session.id,
        class_id=session.class_id,
        class_name=session.class_room.name,
        teacher_name=session.teacher.user.name,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )


def build_report(db: Session, session: LiveSession) -> LiveSessionReportOut:
    participants = (
        db.query(LiveSessionParticipant)
        .filter(LiveSessionParticipant.session_id == session.id)
        .order_by(LiveSessionParticipant.joined_at.asc())
        .all()
    )
    mistakes = (
        db.query(LiveSessionMistake)
        .filter(LiveSessionMistake.session_id == session.id)
        .order_by(LiveSessionMistake.created_at.asc())
        .all()
    )

    participant_out = []
    for p in participants:
        left = p.left_at or (session.ended_at if session.status == "ended" else None)
        duration = (left - p.joined_at).total_seconds() if left else None
        participant_out.append(
            LiveSessionParticipantOut(
                student_id=p.student_id,
                student_name=p.student.user.name,
                joined_at=p.joined_at,
                left_at=p.left_at,
                duration_seconds=duration,
            )
        )

    mistake_out = [
        LiveSessionMistakeOut(
            student_id=m.student_id,
            student_name=m.student.user.name,
            mark_type=m.mark_type,
            note=m.note,
            created_at=m.created_at,
        )
        for m in mistakes
    ]

    return LiveSessionReportOut(session=to_session_out(session), participants=participant_out, mistakes=mistake_out)
