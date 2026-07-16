from datetime import date, datetime

from app.schemas.base import CamelModel


class ApiKeyOut(CamelModel):
    id: str
    name: str
    key_prefix: str
    scopes: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class ApiKeyCreatedOut(ApiKeyOut):
    """
    Returned only once, from the create endpoint — the one and only
    moment the raw key is ever visible anywhere, client or server. Every
    other read of an API key (the list endpoint) returns `ApiKeyOut`,
    which has no `api_key` field at all.
    """

    api_key: str


class CreateApiKeyRequest(CamelModel):
    name: str
    # Defaults to read-only. Pass "read,write" explicitly to issue a key
    # that can also call the /v1 write endpoints — see
    # deps.require_api_scope and services/api_key_service.create_api_key.
    scopes: str = "read"


# --- Public integration API (/v1) response shapes -----------------------


class PublicStudentOut(CamelModel):
    id: str
    name: str
    class_name: str | None
    current_streak: int
    longest_streak: int


class PublicClassOut(CamelModel):
    id: str
    name: str
    teacher_name: str | None
    student_count: int


# --- Phase 31: write endpoints (require an API key with 'write' scope) --


class CreateStudentRequest(CamelModel):
    email: str
    name: str
    class_id: str | None = None


class CreatedStudentOut(CamelModel):
    """
    Returned only once, from the create endpoint — the one and only
    moment the temporary password is visible anywhere, same "shown once"
    principle as ApiKeyCreatedOut. The external LMS is expected to relay
    this to the student (or their guardian) directly; HifzAI itself
    never emails it.
    """

    id: str
    email: str
    name: str
    temporary_password: str


class UpdateStudentRequest(CamelModel):
    name: str | None = None
    class_id: str | None = None


class CreateAttendanceRequest(CamelModel):
    session_date: date
    status: str  # conventionally one of ATTENDANCE_STATUSES; see external_records.py
    source_label: str | None = None
    note: str | None = None


class AttendanceRecordOut(CamelModel):
    id: str
    student_id: str
    session_date: date
    status: str
    source_label: str | None
    note: str | None
    created_at: datetime


class CreateGradeRequest(CamelModel):
    label: str
    score: float
    max_score: float
    recorded_date: date
    note: str | None = None


class GradeRecordOut(CamelModel):
    id: str
    student_id: str
    label: str
    score: float
    max_score: float
    recorded_date: date
    note: str | None
    created_at: datetime
