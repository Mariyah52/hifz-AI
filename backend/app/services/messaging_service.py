from sqlalchemy.orm import Session

from app.models.classroom import ClassRoom, ParentChildLink
from app.models.communication import Announcement, Conversation, DirectMessage, Homework
from app.models.user import ParentProfile, StudentProfile, TeacherProfile, User, utcnow


class MessagingError(Exception):
    pass


def _teacher_classes(db: Session, teacher_id: str) -> list[str]:
    return [c.id for c in db.query(ClassRoom).filter(ClassRoom.teacher_id == teacher_id).all()]


def can_message(db: Session, user_a: User, user_b: User) -> bool:
    """
    Messaging is only allowed between a teacher and a student/parent with
    a real relationship to one of that teacher's classes — not between
    any two arbitrary accounts in the organization. One side must be a
    teacher; the other a student in one of their classes, or a parent
    linked to a student in one of their classes.
    """
    teacher_user, other_user = (user_a, user_b) if user_a.role == "teacher" else (user_b, user_a)
    if teacher_user.role != "teacher" or other_user.role not in ("student", "parent"):
        return False
    if teacher_user.organization_id != other_user.organization_id:
        return False

    teacher = db.query(TeacherProfile).filter(TeacherProfile.user_id == teacher_user.id).first()
    if teacher is None:
        return False
    class_ids = set(_teacher_classes(db, teacher.id))
    if not class_ids:
        return False

    if other_user.role == "student":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == other_user.id).first()
        return student is not None and student.class_id in class_ids

    parent = db.query(ParentProfile).filter(ParentProfile.user_id == other_user.id).first()
    if parent is None:
        return False
    linked_student_ids = [
        link.student_id for link in db.query(ParentChildLink).filter(ParentChildLink.parent_id == parent.id).all()
    ]
    linked_students = db.query(StudentProfile).filter(StudentProfile.id.in_(linked_student_ids)).all()
    return any(s.class_id in class_ids for s in linked_students)


def get_or_create_conversation(db: Session, user_a_id: str, user_b_id: str) -> Conversation:
    ordered = sorted([user_a_id, user_b_id])
    existing = (
        db.query(Conversation)
        .filter(Conversation.user_a_id == ordered[0], Conversation.user_b_id == ordered[1])
        .first()
    )
    if existing:
        return existing

    conversation = Conversation(user_a_id=ordered[0], user_b_id=ordered[1])
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations_for_user(db: Session, user_id: str) -> list[Conversation]:
    return (
        db.query(Conversation)
        .filter((Conversation.user_a_id == user_id) | (Conversation.user_b_id == user_id))
        .order_by(Conversation.created_at.desc())
        .all()
    )


def other_participant_id(conversation: Conversation, user_id: str) -> str:
    return conversation.user_b_id if conversation.user_a_id == user_id else conversation.user_a_id


def get_messages(db: Session, conversation_id: str) -> list[DirectMessage]:
    return (
        db.query(DirectMessage)
        .filter(DirectMessage.conversation_id == conversation_id)
        .order_by(DirectMessage.created_at.asc())
        .all()
    )


def send_message(
    db: Session,
    conversation_id: str,
    sender_user_id: str,
    content: str | None,
    attachment_url: str | None = None,
    attachment_type: str | None = None,
) -> DirectMessage:
    message = DirectMessage(
        conversation_id=conversation_id, sender_user_id=sender_user_id, content=content,
        attachment_url=attachment_url, attachment_type=attachment_type,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def mark_conversation_read(db: Session, conversation_id: str, reader_user_id: str) -> None:
    db.query(DirectMessage).filter(
        DirectMessage.conversation_id == conversation_id,
        DirectMessage.sender_user_id != reader_user_id,
        DirectMessage.read_at.is_(None),
    ).update({"read_at": utcnow()})
    db.commit()


def create_announcement(
    db: Session, organization_id: str, author_user_id: str, title: str, content: str, class_id: str | None
) -> Announcement:
    announcement = Announcement(
        organization_id=organization_id, author_user_id=author_user_id, title=title, content=content, class_id=class_id
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


def get_announcements_for_class_ids(db: Session, organization_id: str, class_ids: list[str]) -> list[Announcement]:
    """Institution-wide announcements (class_id is null) plus any posted to the given classes."""
    query = db.query(Announcement).filter(Announcement.organization_id == organization_id)
    if class_ids:
        query = query.filter((Announcement.class_id.is_(None)) | (Announcement.class_id.in_(class_ids)))
    else:
        query = query.filter(Announcement.class_id.is_(None))
    return query.order_by(Announcement.created_at.desc()).all()


def create_homework(db: Session, class_id: str, teacher_id: str, title: str, description: str, due_date) -> Homework:
    homework = Homework(
        class_id=class_id, created_by_teacher_id=teacher_id, title=title, description=description, due_date=due_date
    )
    db.add(homework)
    db.commit()
    db.refresh(homework)
    return homework


def get_homework_for_class_ids(db: Session, class_ids: list[str]) -> list[Homework]:
    if not class_ids:
        return []
    return db.query(Homework).filter(Homework.class_id.in_(class_ids)).order_by(Homework.due_date.asc()).all()
