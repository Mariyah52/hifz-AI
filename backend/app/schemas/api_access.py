from datetime import datetime

from app.schemas.base import CamelModel


class ApiKeyOut(CamelModel):
    id: str
    name: str
    key_prefix: str
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
