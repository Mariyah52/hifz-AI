import logging
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models.classroom import ParentChildLink
from app.models.user import ParentProfile, StudentProfile
from app.services.email_service import send_email
from app.services.notification_service import already_notified_today, create_notification
from app.services.progress_analytics import build_progress_summary
from app.services.spaced_repetition import get_due_reviews

logger = logging.getLogger(__name__)


def run_daily_engagement_check() -> None:
    """
    Runs once daily: for every student, checks two real conditions and
    creates an in-app notification (+ best-effort push) for each that's
    true today and not already notified today (see
    notification_service.already_notified_today — the dedup guard that
    keeps this from spamming the same notification on every run).
    """
    db = SessionLocal()
    try:
        students = db.query(StudentProfile).all()
        today = date.today()
        for student in students:
            due = get_due_reviews(db, student.id)
            if due and not already_notified_today(db, student.user_id, "reviews_due"):
                create_notification(
                    db, student.user_id, "reviews_due", "Reviews waiting",
                    f"You have {len(due)} Sabaq{'s' if len(due) != 1 else ''} due for review.",
                )

            streak_at_risk = (
                student.current_streak > 0
                and student.last_active_date != today
                and not already_notified_today(db, student.user_id, "streak_at_risk")
            )
            if streak_at_risk:
                create_notification(
                    db, student.user_id, "streak_at_risk", "Your streak is at risk",
                    f"You haven't recorded any activity today — your {student.current_streak}-day "
                    "streak resets at midnight.",
                )
    finally:
        db.close()


def run_weekly_parent_digest() -> None:
    """Real summary, composed from the same data the Parent Portal itself shows — nothing invented."""
    db = SessionLocal()
    try:
        links = db.query(ParentChildLink).all()
        for link in links:
            parent = db.get(ParentProfile, link.parent_id)
            student = db.get(StudentProfile, link.student_id)
            if parent is None or student is None:
                continue

            progress = build_progress_summary(db, student)
            practice_this_week = sum(d.practice_count for d in progress.weekly_activity)
            tests_this_week = sum(d.test_count for d in progress.weekly_activity)
            due = get_due_reviews(db, student.id)

            body = (
                f"{student.user.name}'s week: {practice_this_week} practice session(s), "
                f"{tests_this_week} test(s), current streak {student.current_streak} days, "
                f"{len(due)} review(s) due."
            )
            create_notification(
                db, parent.user_id, "parent_weekly_digest", f"{student.user.name}'s weekly report", body
            )
            send_email(parent.user.email, f"HifzAI weekly report: {student.user.name}", body)
    finally:
        db.close()


_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    """
    In-process, single-server scheduling (APScheduler's `BackgroundScheduler`)
    — appropriate for this app's current scale (one server, no distributed
    job queue). Running more than one instance of this app in parallel
    would run these jobs multiple times each; a real horizontally-scaled
    deployment would want a proper job queue (Celery/RQ + a broker)
    instead of this. Documented here rather than glossed over.
    """
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(run_daily_engagement_check, CronTrigger(hour=20, minute=0), id="daily_engagement_check")
    _scheduler.add_job(
        run_weekly_parent_digest, CronTrigger(day_of_week="sun", hour=18, minute=0), id="weekly_parent_digest"
    )
    _scheduler.start()
    logger.info("Scheduler started: daily engagement check (20:00 UTC), weekly parent digest (Sun 18:00 UTC).")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
