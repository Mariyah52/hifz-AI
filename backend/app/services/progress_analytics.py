from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.practice import PracticeAttempt
from app.models.test import TestResult, TestSession
from app.models.user import StudentProfile, today
from app.schemas.progress import DailyActivity, ProgressSummary

TOTAL_AYAH_COUNT = 6236


def _distinct_correct_ayah_count(db: Session, student_id: str) -> int:
    rows = (
        db.query(TestSession.surah_number, TestResult.ayah_number)
        .join(TestResult, TestResult.session_id == TestSession.id)
        .filter(TestSession.student_id == student_id, TestResult.mark == "correct")
        .distinct()
        .all()
    )
    return len(rows)


def _build_daily_activity(db: Session, student_id: str, days: int) -> list[DailyActivity]:
    start_date = today() - timedelta(days=days - 1)

    buckets: dict[date, dict] = {
        start_date + timedelta(days=i): {"practice_count": 0, "test_count": 0, "test_scores": []}
        for i in range(days)
    }

    attempts = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.student_id == student_id, PracticeAttempt.recorded_at >= start_date)
        .all()
    )
    for attempt in attempts:
        key = attempt.recorded_at.date()
        if key in buckets:
            buckets[key]["practice_count"] += 1

    sessions = (
        db.query(TestSession)
        .filter(TestSession.student_id == student_id, TestSession.completed_at >= start_date)
        .all()
    )
    for session in sessions:
        key = session.completed_at.date()
        if key in buckets:
            buckets[key]["test_count"] += 1
            buckets[key]["test_scores"].append(session.score_percent)

    result = []
    for day, bucket in sorted(buckets.items()):
        scores = bucket["test_scores"]
        result.append(
            DailyActivity(
                date=day.isoformat(),
                practice_count=bucket["practice_count"],
                test_count=bucket["test_count"],
                test_average_score=round(sum(scores) / len(scores)) if scores else None,
            )
        )
    return result


def build_progress_summary(db: Session, student: StudentProfile) -> ProgressSummary:
    total_practice_attempts = (
        db.query(PracticeAttempt).filter(PracticeAttempt.student_id == student.id).count()
    )
    sessions = db.query(TestSession).filter(TestSession.student_id == student.id).all()
    total_test_sessions = len(sessions)
    memorized_ayah_count = _distinct_correct_ayah_count(db, student.id)

    return ProgressSummary(
        memorized_ayah_count=memorized_ayah_count,
        total_ayah_count=TOTAL_AYAH_COUNT,
        completion_percent=round((memorized_ayah_count / TOTAL_AYAH_COUNT) * 1000) / 10,
        current_streak=student.current_streak,
        longest_streak=student.longest_streak,
        total_practice_attempts=total_practice_attempts,
        total_test_sessions=total_test_sessions,
        overall_average_test_score=(
            round(sum(s.score_percent for s in sessions) / len(sessions)) if sessions else None
        ),
        weekly_activity=_build_daily_activity(db, student.id, 7),
        monthly_activity=_build_daily_activity(db, student.id, 30),
    )
