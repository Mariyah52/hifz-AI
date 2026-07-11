from datetime import datetime

from app.schemas.base import CamelModel


class NotificationOut(CamelModel):
    id: str
    notification_type: str
    title: str
    body: str
    related_id: str | None
    is_read: bool
    created_at: datetime


class PushSubscriptionCreate(CamelModel):
    endpoint: str
    p256dh_key: str
    auth_key: str


class VapidPublicKeyOut(CamelModel):
    public_key: str | None  # null when push isn't configured server-side
