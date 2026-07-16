from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.user import User
from app.models.webhook import WEBHOOK_EVENT_TYPES, Webhook, WebhookDeliveryLog
from app.schemas.webhook import CreateWebhookRequest, WebhookCreatedOut, WebhookDeliveryLogOut, WebhookOut
from app.services.webhooks import generate_webhook_secret

router = APIRouter(prefix="/admin/webhooks", tags=["webhooks"], dependencies=[Depends(require_role("admin"))])


@router.get("", response_model=list[WebhookOut])
def list_webhooks(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[WebhookOut]:
    webhooks = (
        db.query(Webhook)
        .filter(Webhook.organization_id == admin.organization_id)
        .order_by(Webhook.created_at.desc())
        .all()
    )
    return [WebhookOut.model_validate(w) for w in webhooks]


@router.post("", response_model=WebhookCreatedOut, status_code=status.HTTP_201_CREATED)
def create_webhook(
    payload: CreateWebhookRequest, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> WebhookCreatedOut:
    invalid = set(payload.event_types) - set(WEBHOOK_EVENT_TYPES)
    if invalid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unknown event type(s): {', '.join(sorted(invalid))}. Valid types: {', '.join(WEBHOOK_EVENT_TYPES)}",
        )
    if not payload.url.startswith("https://"):
        # Not just a style preference — the signature header this app sends is
        # useless as proof of authenticity if the request itself isn't encrypted.
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Webhook URL must use https://")

    secret = generate_webhook_secret()
    webhook = Webhook(
        organization_id=admin.organization_id,
        url=payload.url,
        secret=secret,
        event_types=",".join(payload.event_types),
        created_by_user_id=admin.id,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return WebhookCreatedOut(
        id=webhook.id, url=webhook.url, event_types=webhook.event_types, is_active=webhook.is_active,
        created_at=webhook.created_at, secret=secret,
    )


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryLogOut])
def list_webhook_deliveries(
    webhook_id: str, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> list[WebhookDeliveryLogOut]:
    webhook = db.get(Webhook, webhook_id)
    if webhook is None or webhook.organization_id != admin.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Webhook not found")

    logs = (
        db.query(WebhookDeliveryLog)
        .filter(WebhookDeliveryLog.webhook_id == webhook_id)
        .order_by(WebhookDeliveryLog.created_at.desc())
        .limit(50)
        .all()
    )
    return [WebhookDeliveryLogOut.model_validate(log) for log in logs]


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(webhook_id: str, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> None:
    webhook = db.get(Webhook, webhook_id)
    if webhook is None or webhook.organization_id != admin.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Webhook not found")
    webhook.is_active = False
    db.commit()
