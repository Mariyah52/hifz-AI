from datetime import datetime

from app.schemas.base import CamelModel
from app.schemas.lesson import SabaqOut
from app.schemas.practice import PracticeAttemptOut
from app.schemas.test import TestSessionOut


class StudentOut(CamelModel):
    id: str
    user_id: str
    name: str
    class_id: str | None
    current_streak: int
    todays_sabaq: SabaqOut | None


class TeacherClassOut(CamelModel):
    id: str
    name: str


class TeacherFeedbackOut(CamelModel):
    id: str
    student_id: str
    note: str
    created_at: datetime


class StudentDetailOut(StudentOut):
    recent_practice_attempts: list[PracticeAttemptOut]
    recent_test_sessions: list[TestSessionOut]
    feedback: list[TeacherFeedbackOut]


class AddFeedbackRequest(CamelModel):
    note: str
