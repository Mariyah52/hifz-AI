from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.classroom import ClassRoom, ParentChildLink
from app.models.communication import Conversation
from app.models.user import ParentProfile, StudentProfile, TeacherProfile, User
from app.schemas.communication import (
    AnnouncementOut,
    ConversationOut,
    DirectMessageOut,
    HomeworkOut,
    StartConversationRequest,
)
from app.services.media import AttachmentError, save_message_attachment
from app.services.messaging_service import (
    can_message,
    get_announcements_for_class_ids,
    get_homework_for_class_ids,
    get_messages,
    get_or_create_conversation,
    list_conversations_for_user,
    mark_conversation_read,
    other_participant_id,
    send_message,
)

router = APIRouter(prefix="/me", tags=["communication"])


def _my_class_ids(db: Session, user: User) -> list[str]:
    """
    The classes relevant to this user for announcements/homework: a
    teacher's own classes, a student's own class, or a parent's linked
    children's classes. Empty for admin (they see org-wide only here —
    the Admin Portal has its own institution-level views).
    """
    if user.role == "teacher":
        teacher = db.query(TeacherProfile).filter(TeacherProfile.user_id == user.id).first()
        if teacher is None:
            return []
        return [c.id for c in db.query(ClassRoom).filter(ClassRoom.teacher_id == teacher.id).all()]

    if user.role == "student":
        student = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        return [student.class_id] if student and student.class_id else []

    if user.role == "parent":
        parent = db.query(ParentProfile).filter(ParentProfile.user_id == user.id).first()
        if parent is None:
            return []
        links = db.query(ParentChildLink).filter(ParentChildLink.parent_id == parent.id).all()
        students = db.query(StudentProfile).filter(StudentProfile.id.in_([link.student_id for link in links])).all()
        return [s.class_id for s in students if s.class_id]

    return []


def _get_own_conversation(db: Session, user: User, conversation_id: str) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or user.id not in (conversation.user_a_id, conversation.user_b_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return conversation


@router.get("/conversations", response_model=list[ConversationOut])
def list_my_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ConversationOut]:
    conversations = list_conversations_for_user(db, user.id)
    out = []
    for conv in conversations:
        other_id = other_participant_id(conv, user.id)
        other_user = db.get(User, other_id)
        if other_user is None:
            continue
        messages = get_messages(db, conv.id)
        last = messages[-1] if messages else None
        unread = sum(1 for m in messages if m.sender_user_id != user.id and m.read_at is None)
        out.append(
            ConversationOut(
                id=conv.id, other_user_id=other_user.id, other_user_name=other_user.name,
                other_user_role=other_user.role,
                last_message_preview=(last.content or "Attachment") if last else None,
                last_message_at=last.created_at if last else None,
                unread_count=unread,
            )
        )
    return out


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def start_conversation(
    payload: StartConversationRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ConversationOut:
    other_user = db.get(User, payload.other_user_id)
    if other_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if not can_message(db, user, other_user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can't message this person.")

    conversation = get_or_create_conversation(db, user.id, other_user.id)
    return ConversationOut(
        id=conversation.id, other_user_id=other_user.id, other_user_name=other_user.name,
        other_user_role=other_user.role, last_message_preview=None, last_message_at=None, unread_count=0,
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[DirectMessageOut])
def list_conversation_messages(
    conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[DirectMessageOut]:
    conversation = _get_own_conversation(db, user, conversation_id)
    mark_conversation_read(db, conversation.id, user.id)
    return [DirectMessageOut.model_validate(m) for m in get_messages(db, conversation.id)]


@router.post(
    "/conversations/{conversation_id}/messages", response_model=DirectMessageOut, status_code=status.HTTP_201_CREATED
)
async def post_conversation_message(
    conversation_id: str,
    content: str | None = Form(None),
    attachment: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DirectMessageOut:
    conversation = _get_own_conversation(db, user, conversation_id)

    if not content and attachment is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A message needs text or an attachment.")

    attachment_url = None
    attachment_type = None
    if attachment is not None:
        try:
            attachment_url, attachment_type = await save_message_attachment(attachment, conversation.id)
        except AttachmentError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    message = send_message(db, conversation.id, user.id, content, attachment_url, attachment_type)
    return DirectMessageOut.model_validate(message)


@router.get("/announcements", response_model=list[AnnouncementOut])
def list_my_announcements(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[AnnouncementOut]:
    class_ids = _my_class_ids(db, user)
    announcements = get_announcements_for_class_ids(db, user.organization_id, class_ids)
    class_names = {c.id: c.name for c in db.query(ClassRoom).filter(ClassRoom.id.in_(class_ids)).all()}
    return [
        AnnouncementOut(
            id=a.id, class_id=a.class_id, class_name=class_names.get(a.class_id) if a.class_id else None,
            author_name=a.author.name, title=a.title, content=a.content, created_at=a.created_at,
        )
        for a in announcements
    ]


@router.get("/homework", response_model=list[HomeworkOut])
def list_my_homework(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[HomeworkOut]:
    class_ids = _my_class_ids(db, user)
    homework = get_homework_for_class_ids(db, class_ids)
    class_names = {c.id: c.name for c in db.query(ClassRoom).filter(ClassRoom.id.in_(class_ids)).all()}
    return [
        HomeworkOut(
            id=h.id, class_id=h.class_id, class_name=class_names.get(h.class_id, ""),
            title=h.title, description=h.description, due_date=h.due_date, created_at=h.created_at,
        )
        for h in homework
    ]
