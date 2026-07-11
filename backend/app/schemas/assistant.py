from datetime import datetime
from typing import Literal

from app.schemas.base import CamelModel

ChatRole = Literal["user", "assistant"]


class ChatMessageOut(CamelModel):
    id: str
    role: ChatRole
    content: str
    tools_called: list[str]
    created_at: datetime


class SendMessageRequest(CamelModel):
    message: str
