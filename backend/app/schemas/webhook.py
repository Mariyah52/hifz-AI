from datetime import datetime

from app.schemas.base import CamelModel


class CreateWebhookRequest(CamelModel):
    url: str
    event_types: list[str]  # subset of WEBHOOK_EVENT_TYPES — validated in the router


class WebhookOut(CamelModel):
    id: str
    url: str
    event_types: str
    is_active: bool
    created_at: datetime


class WebhookCreatedOut(WebhookOut):
    """Returned only once — the one moment the raw signing secret is visible. See models/webhook.py's docstring for why it can't just be hashed like an API key."""

    secret: str


class WebhookDeliveryLogOut(CamelModel):
    id: str
    event_type: str
    success: bool
    status_code: int | None
    response_snippet: str | None
    created_at: datetime
