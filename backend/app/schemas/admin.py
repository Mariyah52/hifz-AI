from datetime import datetime

from app.schemas.base import CamelModel
from app.schemas.teacher import StudentOut


class TeacherOut(CamelModel):
    id: str
    name: str
    class_ids: list[str]


class ClassSummaryOut(CamelModel):
    id: str
    name: str
    teacher_name: str | None
    student_count: int
    average_streak: int


class AdminAnalyticsOut(CamelModel):
    total_students: int
    total_teachers: int
    total_classes: int
    total_feedback_given: int
    total_sabaqs_assigned: int
    average_test_score: float | None
    students_needing_attention: list[StudentOut]


class CreateClassRequest(CamelModel):
    name: str
    teacher_id: str | None = None


class AssignClassRequest(CamelModel):
    class_id: str


class AuditLogEntryOut(CamelModel):
    id: str
    user_email: str | None
    action: str
    ip_address: str | None
    detail: str | None
    created_at: datetime
