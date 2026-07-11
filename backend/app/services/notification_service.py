from sqlalchemy.orm import Session

from app.models.notification import Notification, PushSubscription
from app.models.user import utcnow
from app.services.push_service import send_push_to_user


def create_notification(
    db: Session,
    user_id: str,
    notification_type: str,
    title: str,
    body: str,
    related_id: str | None = None,
    push: bool = True,
) -> Notification:
    """
    Creates the in-app notification (always) and best-effort attempts a
    Web Push send if the user has a registered subscription and the
    server has VAPID keys configured (`push_service.send_push_to_user`
    silently no-ops otherwise — see its docstring). One function so every
    call site — event-driven or from the scheduled jobs — gets both for free.
    """
    notification = Notification(
        user_id=user_id, notification_type=notification_type, title=title, body=body, related_id=related_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    if push:
        send_push_to_user(db, user_id, title, body)

    return notification


def already_notified_today(db: Session, user_id: str, notification_type: str) -> bool:
    """
    Dedup guard for the scheduled jobs (see scheduler.py) — without this,
    a daily job re-running (or restarting mid-day) would spam the same
    "streak at risk" notification repeatedly instead of once per day.
    """
    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.notification_type == notification_type,
            Notification.created_at >= today_start,
        )
        .first()
        is not None
    )


def get_notifications(db: Session, user_id: str, limit: int = 50) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def get_unread_count(db: Session, user_id: str) -> int:
    return db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read.is_(False)).count()


def mark_read(db: Session, user_id: str, notification_id: str) -> Notification | None:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        return None
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: str) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return updated


def upsert_push_subscription(
    db: Session, user_id: str, endpoint: str, p256dh_key: str, auth_key: str
) -> PushSubscription:
    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if existing:
        existing.user_id = user_id
        existing.p256dh_key = p256dh_key
        existing.auth_key = auth_key
        db.commit()
        db.refresh(existing)
        return existing

    subscription = PushSubscription(user_id=user_id, endpoint=endpoint, p256dh_key=p256dh_key, auth_key=auth_key)
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def remove_push_subscription(db: Session, user_id: str, endpoint: str) -> None:
    db.query(PushSubscription).filter(
        PushSubscription.user_id == user_id, PushSubscription.endpoint == endpoint
    ).delete()
    db.commit()
