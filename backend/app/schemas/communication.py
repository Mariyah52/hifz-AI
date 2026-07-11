from datetime import date, datetime
from typing import Literal

from app.schemas.base import CamelModel


class ConversationOut(CamelModel):
    id: str
    other_user_id: str
    other_user_name: str
    other_user_role: str
    last_message_preview: str | None
    last_message_at: datetime | None
    unread_count: int


class DirectMessageOut(CamelModel):
    id: str
    sender_user_id: str
    content: str | None
    attachment_url: str | None
    attachment_type: Literal["audio", "file"] | None
    created_at: datetime
    read_at: datetime | None


class StartConversationRequest(CamelModel):
    other_user_id: str


class AnnouncementOut(CamelModel):
    id: str
    class_id: str | None
    class_name: str | None
    author_name: str
    title: str
    content: str
    created_at: datetime


class CreateAnnouncementRequest(CamelModel):
    title: str
    content: str
    class_id: str | None = None


class HomeworkOut(CamelModel):
    id: str
    class_id: str
    class_name: str
    title: str
    description: str
    due_date: date
    created_at: datetime


class CreateHomeworkRequest(CamelModel):
    class_id: str
    title: str
    description: str
    due_date: date
