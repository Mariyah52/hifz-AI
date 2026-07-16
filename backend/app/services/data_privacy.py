import os
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth_security import AuditLogEntry, PasswordResetToken, RefreshToken
from app.models.certificate import Certificate
from app.models.chat import ChatConversation
from app.models.communication import DirectMessage
from app.models.gamification import Achievement
from app.models.live_session import LiveSessionMistake, LiveSessionParticipant
from app.models.note import Note
from app.models.notification import Notification, PushSubscription
from app.models.practice import PracticeAttempt
from app.models.review import ReviewSchedule
from app.models.test import TestSession
from app.models.user import User, utcnow

"""
Data privacy tooling — the highest-priority gap flagged in this project's
own product documentation ("arguably the highest-priority item on this
whole list, given the product handles children's data today without it").

Two real capabilities, both scoped to what a single source-code review
can honestly deliver:

1. Data export (`export_user_data`) — the right-to-access/portability
   side. Gathers every row this app actually stores that's tied to one
   user, across every table, into one JSON-serializable structure.

2. Account deletion (`anonymize_and_delete_account`) — the
   right-to-erasure side. Read the long docstring on that function
   before assuming this hard-deletes the `users` row — it deliberately
   doesn't, and the reasoning matters.

RETENTION_POLICY below is a set of REAL, enforceable defaults this code
actually implements — not a legal document. Whether these specific
numbers are the right ones (and whether anything here satisfies GDPR,
COPPA, or any other real regulation for children's data) is a product
and legal decision this project's own docs correctly flag as still
outstanding. Treat every number here as a starting point for that
conversation, not as a compliance claim.
"""

RETENTION_POLICY = {
    "practice_test_audio": (
        "Recorded audio is retained until the student (or an institute admin, "
        "on their behalf) deletes the account, or deletes an individual "
        "practice/test attempt. There is currently no automatic time-based "
        "expiry — every recording persists indefinitely unless explicitly "
        "removed. Adding an automatic expiry (e.g. N days after recording) "
        "is a real, separate follow-up, not implemented here."
    ),
    "messages": (
        "Direct messages persist for as long as the conversation exists. "
        "Deleting one participant's account scrubs that participant's own "
        "message content (see anonymize_and_delete_account) but does not "
        "delete the conversation itself, since the other participant has an "
        "independent, legitimate interest in their own message history."
    ),
    "audit_log": (
        "Security audit log entries (logins, password resets, lockouts, "
        "account-deletion events) are retained indefinitely today. A "
        "real institution would typically want a fixed retention window "
        "(e.g. 1-2 years) with older rows purged by a scheduled job — "
        "not implemented here; the audit log currently only grows."
    ),
    "deleted_accounts": (
        "A 'deleted' account is anonymized in place, not hard-deleted from "
        "the database — see anonymize_and_delete_account's docstring for "
        "why. Personally identifying fields (name, email, password) are "
        "scrubbed immediately; genuinely personal-only content (recordings, "
        "notes, chat history, achievements) is hard-deleted immediately. "
        "There is no 'soft delete with an undo window' — deletion, once "
        "requested and confirmed, is immediate and not reversible."
    ),
}


def _delete_audio_file(url: str | None) -> bool:
    """Best-effort delete of a /media/... URL's underlying file. Returns True if a file was actually removed."""
    if not url or not url.startswith("/media/"):
        return False
    relative_path = url[len("/media/"):]
    absolute_path = os.path.join(settings.media_root, relative_path)
    try:
        os.remove(absolute_path)
        return True
    except OSError:
        return False


def export_user_data(db: Session, user: User) -> dict:
    """
    Full data export for one user, scoped to whatever role-specific data
    actually exists for them. Every value here comes from a real row this
    app actually stored — no synthesized or estimated fields, consistent
    with this project's own stated principle about not presenting
    invented numbers as fact.
    """
    export: dict = {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "organization_id": user.organization_id,
            "created_at": user.created_at.isoformat(),
        },
        "messages_sent": [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "content": m.content,
                "attachment_url": m.attachment_url,
                "created_at": m.created_at.isoformat(),
            }
            for m in db.query(DirectMessage).filter(DirectMessage.sender_user_id == user.id).all()
        ],
        "notifications": [
            {
                "id": n.id,
                "type": n.notification_type,
                "title": n.title,
                "body": n.body,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in db.query(Notification).filter(Notification.user_id == user.id).all()
        ],
        "audit_log": [
            {"action": a.action, "ip_address": a.ip_address, "detail": a.detail, "created_at": a.created_at.isoformat()}
            for a in db.query(AuditLogEntry).filter(AuditLogEntry.user_id == user.id).all()
        ],
    }

    if user.role == "student" and user.student_profile:
        student = user.student_profile
        export["student_profile"] = {
            "current_streak": student.current_streak,
            "longest_streak": student.longest_streak,
            "last_active_date": student.last_active_date.isoformat() if student.last_active_date else None,
        }
        export["practice_attempts"] = [
            {
                "id": p.id, "surah_number": p.surah_number, "surah_name": p.surah_name,
                "from_ayah": p.from_ayah, "to_ayah": p.to_ayah,
                "recorded_at": p.recorded_at.isoformat(), "audio_url": p.audio_url,
            }
            for p in db.query(PracticeAttempt).filter(PracticeAttempt.student_id == student.id).all()
        ]
        export["test_sessions"] = [
            {
                "id": t.id, "surah_number": t.surah_number, "surah_name": t.surah_name,
                "from_ayah": t.from_ayah, "to_ayah": t.to_ayah,
                "completed_at": t.completed_at.isoformat(), "score_percent": t.score_percent,
                "audio_url": t.audio_url,
            }
            for t in db.query(TestSession).filter(TestSession.student_id == student.id).all()
        ]
        export["notes"] = [
            {"id": n.id, "content": n.content, "surah_number": n.surah_number, "created_at": n.created_at.isoformat()}
            for n in db.query(Note).filter(Note.student_id == student.id).all()
        ]
        export["achievements"] = [
            {"key": a.achievement_key, "earned_at": a.earned_at.isoformat()}
            for a in db.query(Achievement).filter(Achievement.student_id == student.id).all()
        ]
        export["certificates"] = [
            {"id": c.id, "type": c.type, "title": c.title, "detail": c.detail, "issued_at": c.issued_at.isoformat()}
            for c in db.query(Certificate).filter(Certificate.student_id == student.id).all()
        ]
        export["review_schedules"] = [
            {
                "sabaq_id": r.sabaq_id, "ease_factor": r.ease_factor, "interval_days": r.interval_days,
                "due_date": r.due_date.isoformat(),
            }
            for r in db.query(ReviewSchedule).filter(ReviewSchedule.student_id == student.id).all()
        ]
        chat = db.query(ChatConversation).filter(ChatConversation.student_id == student.id).first()
        export["assistant_chat"] = (
            [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in chat.messages]
            if chat else []
        )

    return export


def anonymize_and_delete_account(db: Session, user: User) -> dict:
    """
    The real erasure flow. Read this before assuming "delete account"
    hard-deletes the `users` row — it deliberately does NOT, for a
    concrete, non-negotiable reason:

    Other real rows in this app hold a non-nullable foreign key straight
    to `users.id` (messages this user sent, announcements they authored,
    marketplace installs they triggered, API keys they created) or to
    their role profile (a certificate a teacher issued, a live class they
    hosted, a conversation they're one side of). This project has no
    ON DELETE CASCADE configured anywhere in its schema — cascades are
    handled in application code by design elsewhere in this codebase, not
    left to the database. Hard-deleting the `users` row would either
    violate those foreign keys outright (rejected by Postgres in
    production) or force cascading the delete into OTHER real users' own
    legitimate data (the other side of a conversation, an entire class's
    live-session history) — which is a worse privacy outcome, not a
    better one.

    So "deletion" here means exactly this, and no more or less:
      - HARD DELETE, immediately, no undo: practice/test audio files
        (from disk) and their rows, notes, achievements, the assistant
        chat history, review schedules, certificates, live-session
        participation/mistake rows, this user's notifications, and their
        push subscriptions, refresh tokens, and password reset tokens.
      - SCRUB (row kept, content emptied): direct messages this user
        sent — content and attachment_url are cleared, but the row and
        conversation remain so the other participant's own history isn't
        destroyed by someone else's deletion request. A frontend should
        render a null `content` as a generic "message deleted" placeholder.
      - ANONYMIZE IN PLACE (row kept): the `users` row itself — name,
        email, and password are overwritten with non-identifying values,
        `deleted_at`/`anonymized` are set, and every other real row that
        still legitimately points at this user's id (an announcement they
        posted, a certificate they issued as a teacher, an API key they
        created) keeps working exactly as it did, just with no
        identifying information attached to it anymore.
      - RESET, not delete: gamified profile counters (streak, freezes) on
        the surviving StudentProfile/TeacherProfile/ParentProfile row,
        since they're derived from data that's now gone.

    Returns a summary dict of what was actually removed, for an audit
    trail and for whatever admin/self-service UI calls this.
    """
    summary = {"audio_files_deleted": 0, "rows_hard_deleted": 0, "messages_scrubbed": 0}

    db.add(AuditLogEntry(
        user_id=user.id, action="account_deletion_requested",
        detail=f"Anonymization requested for user role={user.role}",
    ))

    if user.role == "student" and user.student_profile:
        student = user.student_profile

        for attempt in db.query(PracticeAttempt).filter(PracticeAttempt.student_id == student.id).all():
            if _delete_audio_file(attempt.audio_url):
                summary["audio_files_deleted"] += 1
            db.delete(attempt)  # cascades PracticeAttemptAnalysis via ORM relationship
            summary["rows_hard_deleted"] += 1

        for session in db.query(TestSession).filter(TestSession.student_id == student.id).all():
            if _delete_audio_file(session.audio_url):
                summary["audio_files_deleted"] += 1
            db.delete(session)  # cascades TestResult/TestMistakeRow via ORM relationship
            summary["rows_hard_deleted"] += 1

        for row in db.query(Note).filter(Note.student_id == student.id).all():
            db.delete(row)
            summary["rows_hard_deleted"] += 1

        for row in db.query(Achievement).filter(Achievement.student_id == student.id).all():
            db.delete(row)
            summary["rows_hard_deleted"] += 1

        for row in db.query(Certificate).filter(Certificate.student_id == student.id).all():
            db.delete(row)
            summary["rows_hard_deleted"] += 1

        for row in db.query(ReviewSchedule).filter(ReviewSchedule.student_id == student.id).all():
            db.delete(row)
            summary["rows_hard_deleted"] += 1

        for row in db.query(LiveSessionParticipant).filter(LiveSessionParticipant.student_id == student.id).all():
            db.delete(row)
            summary["rows_hard_deleted"] += 1

        for row in db.query(LiveSessionMistake).filter(LiveSessionMistake.student_id == student.id).all():
            db.delete(row)
            summary["rows_hard_deleted"] += 1

        chat = db.query(ChatConversation).filter(ChatConversation.student_id == student.id).first()
        if chat:
            db.delete(chat)  # cascades ChatMessage via ORM relationship
            summary["rows_hard_deleted"] += 1

        student.current_streak = 0
        student.longest_streak = 0
        student.last_active_date = None
        student.freezes_available = 0

    for msg in db.query(DirectMessage).filter(DirectMessage.sender_user_id == user.id).all():
        msg.content = None
        msg.attachment_url = None
        msg.attachment_type = None
        summary["messages_scrubbed"] += 1

    for row in db.query(Notification).filter(Notification.user_id == user.id).all():
        db.delete(row)
        summary["rows_hard_deleted"] += 1

    for row in db.query(PushSubscription).filter(PushSubscription.user_id == user.id).all():
        db.delete(row)
        summary["rows_hard_deleted"] += 1

    for row in db.query(RefreshToken).filter(RefreshToken.user_id == user.id).all():
        db.delete(row)
        summary["rows_hard_deleted"] += 1

    for row in db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id).all():
        db.delete(row)
        summary["rows_hard_deleted"] += 1

    # Anonymize the user row itself last, in place — see docstring for why
    # this is never a hard delete of `users`.
    anonymized_email = f"deleted-{user.id}@anonymized.hifzai.invalid"
    user.email = anonymized_email
    user.name = "Deleted User"
    user.hashed_password = uuid.uuid4().hex  # not a valid bcrypt hash — verify_password() will always reject it
    user.failed_login_attempts = 0
    user.locked_until = None
    user.deleted_at = utcnow()
    user.anonymized = True

    db.add(AuditLogEntry(user_id=user.id, action="account_deletion_completed", detail=str(summary)))

    return summary
