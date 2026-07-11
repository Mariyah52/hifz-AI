from sqlalchemy.orm import Session

from app.models.feedback import TeacherFeedback
from app.models.lesson import Sabaq
from app.models.practice import PracticeAttempt
from app.models.test import TestSession
from app.models.user import StudentProfile
from app.schemas.lesson import SabaqOut
from app.schemas.practice import PaceOut, PracticeAttemptOut, PracticeMistakeOut
from app.schemas.teacher import StudentDetailOut, StudentOut, TeacherFeedbackOut
from app.schemas.test import TestMistakeOut, TestResultOut, TestSessionOut
from app.schemas.user import StreakInfo


def get_todays_sabaq(db: Session, student_id: str) -> Sabaq | None:
    return (
        db.query(Sabaq)
        .filter(Sabaq.student_id == student_id)
        .order_by(Sabaq.created_at.desc())
        .first()
    )


def get_recent_sabaqs(db: Session, student_id: str, limit: int = 5, exclude_id: str | None = None) -> list[Sabaq]:
    query = db.query(Sabaq).filter(Sabaq.student_id == student_id)
    if exclude_id:
        query = query.filter(Sabaq.id != exclude_id)
    return query.order_by(Sabaq.created_at.desc()).limit(limit).all()


def to_streak_info(student: StudentProfile) -> StreakInfo:
    return StreakInfo(
        current_streak=student.current_streak,
        longest_streak=student.longest_streak,
        last_active_date=student.last_active_date,
        freezes_available=student.freezes_available,
    )


def to_student_out(student: StudentProfile, todays_sabaq: Sabaq | None) -> StudentOut:
    return StudentOut(
        id=student.id,
        user_id=student.user_id,
        name=student.user.name,
        class_id=student.class_id,
        current_streak=student.current_streak,
        todays_sabaq=SabaqOut.model_validate(todays_sabaq) if todays_sabaq else None,
    )


def to_practice_attempt_out(attempt: PracticeAttempt) -> PracticeAttemptOut:
    analysis = attempt.analysis

    return PracticeAttemptOut(
        id=attempt.id,
        surah_number=attempt.surah_number,
        surah_name=attempt.surah_name,
        from_ayah=attempt.from_ayah,
        to_ayah=attempt.to_ayah,
        recorded_at=attempt.recorded_at,
        duration_seconds=attempt.duration_seconds,
        status=attempt.status,
        audio_url=attempt.audio_url,
        pace=PaceOut(
            expected_seconds_range=(attempt.expected_min_seconds, attempt.expected_max_seconds),
            actual_seconds=attempt.duration_seconds,
            within_expected_range=attempt.within_expected_range,
        ),
        analysis_status=(analysis.status if analysis else "not_analyzed"),
        analysis_error=(analysis.error_message if analysis else None),
        transcribed_text=(analysis.transcribed_text if analysis else None),
        matched_word_count=(analysis.matched_word_count if analysis else None),
        total_word_count=(analysis.reference_word_count if analysis else None),
        mistakes=(
            [
                PracticeMistakeOut(
                    mistake_type=m.mistake_type,
                    ayah_number=m.ayah_number,
                    reference_word=m.reference_word,
                    transcribed_word=m.transcribed_word,
                )
                for m in analysis.mistakes
            ]
            if analysis and analysis.status == "completed"
            else []
        ),
    )


def to_test_session_out(session: TestSession) -> TestSessionOut:
    return TestSessionOut(
        id=session.id,
        surah_number=session.surah_number,
        surah_name=session.surah_name,
        from_ayah=session.from_ayah,
        to_ayah=session.to_ayah,
        completed_at=session.completed_at,
        score_percent=session.score_percent,
        audio_url=session.audio_url,
        analysis_status=session.analysis_status,
        analysis_error=session.analysis_error,
        matched_word_count=sum(r.matched_word_count for r in session.results),
        total_word_count=sum(r.total_word_count for r in session.results),
        results=[
            TestResultOut(
                ayah_number=r.ayah_number,
                mark=r.mark,
                matched_word_count=r.matched_word_count,
                total_word_count=r.total_word_count,
            )
            for r in session.results
        ],
        mistakes=[
            TestMistakeOut(
                mistake_type=m.mistake_type,
                ayah_number=m.ayah_number,
                reference_word=m.reference_word,
                transcribed_word=m.transcribed_word,
            )
            for m in session.mistakes
        ],
    )


def to_feedback_out(feedback: TeacherFeedback) -> TeacherFeedbackOut:
    return TeacherFeedbackOut(
        id=feedback.id, student_id=feedback.student_id, note=feedback.note, created_at=feedback.created_at
    )


def build_student_detail(db: Session, student: StudentProfile) -> StudentDetailOut:
    todays_sabaq = get_todays_sabaq(db, student.id)
    attempts = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.student_id == student.id)
        .order_by(PracticeAttempt.recorded_at.desc())
        .limit(10)
        .all()
    )
    sessions = (
        db.query(TestSession)
        .filter(TestSession.student_id == student.id)
        .order_by(TestSession.completed_at.desc())
        .limit(10)
        .all()
    )
    feedback = (
        db.query(TeacherFeedback)
        .filter(TeacherFeedback.student_id == student.id)
        .order_by(TeacherFeedback.created_at.desc())
        .all()
    )

    return StudentDetailOut(
        id=student.id,
        user_id=student.user_id,
        name=student.user.name,
        class_id=student.class_id,
        current_streak=student.current_streak,
        todays_sabaq=SabaqOut.model_validate(todays_sabaq) if todays_sabaq else None,
        recent_practice_attempts=[to_practice_attempt_out(a) for a in attempts],
        recent_test_sessions=[to_test_session_out(s) for s in sessions],
        feedback=[to_feedback_out(f) for f in feedback],
    )


# derive_sabqi/derive_manzil (the Phase 10 heuristic placeholders) were
# retired in Phase 13 — real SM-2 spaced-repetition scheduling now lives
# in app/services/spaced_repetition.py (get_dashboard_reviews et al.).
