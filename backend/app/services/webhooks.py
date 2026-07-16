import hashlib
import hmac
import json
import secrets

import httpx
from sqlalchemy.orm import Session

from app.models.webhook import Webhook, WebhookDeliveryLog

"""
Outbound webhook dispatch — real HTTP delivery with HMAC-SHA256 request
signing (the same scheme Stripe/GitHub use), but a genuinely stated
limitation: delivery is synchronous, best-effort, single-attempt.

There is no retry queue, no exponential backoff, and no dead-letter
handling here. If the receiving URL is down or slow, this call blocks
for up to REQUEST_TIMEOUT_SECONDS and then gives up — it does not retry
later. A production webhook system needs a real task queue (Celery,
an APScheduler-driven retry job, or similar) to be trustworthy; this is
a first real step (actual signed HTTP delivery to a real URL), not that
system. Every caller invokes dispatch_event() via FastAPI's
BackgroundTasks specifically so a slow/dead receiving endpoint can never
make the *triggering* API request itself slow or fail.
"""

REQUEST_TIMEOUT_SECONDS = 5.0
RESPONSE_SNIPPET_MAX_CHARS = 300


def generate_webhook_secret() -> str:
    return f"whsec_{secrets.token_urlsafe(32)}"


def _sign_payload(secret: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()


def _deliver_one(db: Session, webhook: Webhook, event_type: str, payload: dict) -> None:
    body = {"eventType": event_type, "data": payload}
    raw_body = json.dumps(body).encode("utf-8")
    signature = _sign_payload(webhook.secret, raw_body)

    success = False
    status_code: int | None = None
    response_snippet: str | None = None

    try:
        response = httpx.post(
            webhook.url,
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-HifzAI-Signature": signature,
                "X-HifzAI-Event": event_type,
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        status_code = response.status_code
        success = 200 <= response.status_code < 300
        response_snippet = response.text[:RESPONSE_SNIPPET_MAX_CHARS]
    except httpx.HTTPError as exc:
        response_snippet = str(exc)[:RESPONSE_SNIPPET_MAX_CHARS]

    db.add(WebhookDeliveryLog(
        webhook_id=webhook.id, event_type=event_type, success=success,
        status_code=status_code, response_snippet=response_snippet,
    ))
    db.commit()


def dispatch_event(db: Session, organization_id: str, event_type: str, payload: dict) -> None:
    """
    Sends `payload` to every active webhook this organization has
    subscribed to `event_type`. Intended to be called via FastAPI's
    BackgroundTasks (`background_tasks.add_task(dispatch_event, ...)`),
    never awaited directly inside a request handler — see module
    docstring for why.
    """
    webhooks = (
        db.query(Webhook)
        .filter(Webhook.organization_id == organization_id, Webhook.is_active.is_(True))
        .all()
    )
    for webhook in webhooks:
        if webhook.subscribes_to(event_type):
            _deliver_one(db, webhook, event_type, payload)
