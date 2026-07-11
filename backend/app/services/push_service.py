import json
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models.notification import PushSubscription

logger = logging.getLogger(__name__)


def send_push_to_user(db: Session, user_id: str, title: str, body: str) -> None:
    """
    Best-effort: sends a Web Push to every subscription this user has
    registered (they may have more than one browser/device). Silently
    does nothing if VAPID keys aren't configured or the user has no
    subscription — this is deliberately never a hard failure, since a
    push-delivery problem should never block the in-app notification
    that already succeeded (see notification_service.create_notification,
    the only real caller of this).
    """
    if not settings.vapid_private_key or not settings.vapid_public_key:
        return

    subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    if not subscriptions:
        return

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.warning("pywebpush isn't installed — cannot send Web Push notifications.")
        return

    payload = json.dumps({"title": title, "body": body})

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh_key, "auth": subscription.auth_key},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_admin_email}"},
            )
        except WebPushException as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code in (404, 410):
                # Subscription is gone (browser unsubscribed, storage cleared,
                # etc.) — clean it up rather than retrying it forever.
                db.delete(subscription)
                db.commit()
            else:
                logger.warning("Web Push send failed for subscription %s: %s", subscription.id, exc)
