from datetime import datetime
from typing import Literal

from app.schemas.base import CamelModel

MarkType = Literal["perfect", "hesitation", "mistake"]


class LiveSessionOut(CamelModel):
    id: str
    class_id: str
    class_name: str
    teacher_name: str
    status: str
    started_at: datetime
    ended_at: datetime | None


class LiveSessionParticipantOut(CamelModel):
    student_id: str
    student_name: str
    joined_at: datetime
    left_at: datetime | None
    duration_seconds: float | None


class LiveSessionMistakeOut(CamelModel):
    student_id: str
    student_name: str
    mark_type: MarkType
    note: str | None
    created_at: datetime


class LiveSessionReportOut(CamelModel):
    session: LiveSessionOut
    participants: list[LiveSessionParticipantOut]
    mistakes: list[LiveSessionMistakeOut]


class StartLiveSessionRequest(CamelModel):
    class_id: str
