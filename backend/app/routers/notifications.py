from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationOut, PushSubscriptionCreate, VapidPublicKeyOut
from app.services.notification_service import (
    get_notifications,
    get_unread_count,
    mark_all_read,
    mark_read,
    remove_push_subscription,
    upsert_push_subscription,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[NotificationOut]:
    return [NotificationOut.model_validate(n) for n in get_notifications(db, user.id)]


@router.get("/unread-count", response_model=int)
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> int:
    return get_unread_count(db, user.id)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> NotificationOut:
    notification = mark_read(db, user.id, notification_id)
    if notification is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return NotificationOut.model_validate(notification)


@router.post("/read-all", response_model=int)
def mark_all_notifications_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> int:
    return mark_all_read(db, user.id)


@router.get("/vapid-public-key", response_model=VapidPublicKeyOut)
def get_vapid_public_key() -> VapidPublicKeyOut:
    return VapidPublicKeyOut(public_key=settings.vapid_public_key)


@router.post("/push-subscription", status_code=status.HTTP_204_NO_CONTENT)
def create_push_subscription(
    payload: PushSubscriptionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    upsert_push_subscription(db, user.id, payload.endpoint, payload.p256dh_key, payload.auth_key)


@router.delete("/push-subscription", status_code=status.HTTP_204_NO_CONTENT)
def delete_push_subscription(
    endpoint: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> None:
    remove_push_subscription(db, user.id, endpoint)
