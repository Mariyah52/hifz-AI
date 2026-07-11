from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_student_profile
from app.models.certificate import Certificate
from app.models.gamification import Achievement
from app.models.lesson import Sabaq
from app.models.note import Note
from app.models.organization import Organization
from app.models.practice import PracticeAttempt
from app.models.test import TestResult, TestSession
from app.models.user import StudentProfile
from app.schemas.lesson import SabaqOut
from app.schemas.note import NoteCreate, NoteOut
from app.schemas.practice import PracticeAttemptOut
from app.schemas.progress import ProgressSummary
from app.schemas.analytics import AdvancedAnalyticsOut
from app.schemas.gamification import AchievementOut, GamificationSummary, LeaderboardEntryOut
from app.schemas.review import DueReviewOut, ReviewScheduleOut
from app.schemas.test import QuizTestSessionCreate, TestSessionOut
from app.schemas.test_modes import GenerateTestRequest, GeneratedTestOut
from app.schemas.assistant import ChatMessageOut, SendMessageRequest
from app.schemas.certificate import CertificateOut
from app.schemas.live_session import LiveSessionOut
from app.schemas.user import DashboardSummary, ManzilReviewOut, SabqiReviewOut, UserOut
from app.services.analytics import build_advanced_analytics
from app.services.assistant_service import get_message_history, get_or_create_conversation, send_message, to_message_out
from app.services.certificate_service import check_and_award_certificates, render_certificate_pdf
from app.services.live_session_service import get_active_session_for_class, to_session_out
from app.services.gamification import (
    ACHIEVEMENT_DEFS,
    check_and_award_achievements,
    compute_xp,
    get_leaderboard,
    level_for_xp,
)
from app.services.media import save_audio_file, save_test_audio_file
from app.services.progress_analytics import build_progress_summary
from app.services.recitation_analysis import analyze_attempt
from app.services.test_analysis import analyze_test_session
from app.services.spaced_repetition import get_dashboard_reviews, get_due_reviews, record_test_result
from app.services.streak import record_activity_today
from app.services.test_modes import NoContentAvailable, generate_mixed_revision, generate_question
from app.services.student_view import (
    get_recent_sabaqs,
    get_todays_sabaq,
    to_practice_attempt_out,
    to_streak_info,
    to_test_session_out,
)

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> DashboardSummary:
    todays_sabaq = get_todays_sabaq(db, student.id)
    recent = get_recent_sabaqs(db, student.id, limit=6, exclude_id=todays_sabaq.id if todays_sabaq else None)
    progress = build_progress_summary(db, student)

    # Phase 13: Sabqi/Manzil are real SM-2-scheduled due reviews now, not a
    # heuristic derived from recent Sabaq history — see spaced_repetition.py.
    sabqi_pair, manzil_pair = get_dashboard_reviews(db, student.id)

    return DashboardSummary(
        user=UserOut(id=student.user.id, name=student.user.name, role="student", class_id=student.class_id),
        streak=to_streak_info(student),
        todays_sabaq=SabaqOut.model_validate(todays_sabaq) if todays_sabaq else None,
        todays_sabqi=_to_review_out(SabqiReviewOut, sabqi_pair),
        todays_manzil=_to_review_out(ManzilReviewOut, manzil_pair),
        recent_sabaqs=[SabaqOut.model_validate(s) for s in recent],
        # juz_progress and overall_accuracy are now driven by the same real
        # memorized-ayah/test-score signal Progress page uses, instead of
        # Phase 1's separate mock numbers.
        juz_progress=round((progress.completion_percent / 100) * 30, 1),
        overall_accuracy=progress.overall_average_test_score or 0,
    )


def _to_review_out(
    out_cls: type[SabqiReviewOut] | type[ManzilReviewOut], pair: tuple | None
) -> SabqiReviewOut | ManzilReviewOut | None:
    """`pair` is a (Sabaq, ReviewSchedule) tuple or None — see get_dashboard_reviews."""
    if pair is None:
        return None
    sabaq, _schedule = pair
    return out_cls(
        id=sabaq.id,
        surah_number=sabaq.surah_number,
        surah_name=sabaq.surah_name,
        from_ayah=sabaq.from_ayah,
        to_ayah=sabaq.to_ayah,
        status=sabaq.status,
        score=sabaq.score,
    )


@router.get("/progress", response_model=ProgressSummary)
def get_progress(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> ProgressSummary:
    return build_progress_summary(db, student)


@router.get("/analytics/advanced", response_model=AdvancedAnalyticsOut)
async def get_advanced_analytics(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> AdvancedAnalyticsOut:
    """
    Phase 21: weakest juz/surah/pages, most-forgotten ayah, retention
    rate, confidence score — all computed from real TestResult/
    ReviewSchedule rows. See services/analytics.py's module docstring for
    the exact formulas and thresholds, especially confidence_score, which
    is a documented weighted blend of two real signals, not a model output.
    """
    return await build_advanced_analytics(db, student)


@router.post("/tests/generate", response_model=GeneratedTestOut)
async def generate_test(
    payload: GenerateTestRequest,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> GeneratedTestOut:
    """
    Phase 22: generates one question (or, for 'mixed_revision', several)
    for the requested test mode, built from the student's own completed
    Sabaqs and real ayah/page/surah data — never a fabricated range or
    invented distractor. See services/test_modes.py's module docstring
    for the two interaction types every mode reduces to.
    """
    try:
        if payload.mode == "mixed_revision":
            questions = await generate_mixed_revision(db, student)
        else:
            questions = [await generate_question(db, student, payload.mode, payload.surah_number)]
    except NoContentAvailable as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return GeneratedTestOut(questions=questions)


@router.get("/assistant/messages", response_model=list[ChatMessageOut])
def list_assistant_messages(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> list[ChatMessageOut]:
    conversation = get_or_create_conversation(db, student)
    db.commit()
    return [to_message_out(m) for m in get_message_history(db, conversation)]


@router.post("/assistant/messages", response_model=ChatMessageOut)
async def post_assistant_message(
    payload: SendMessageRequest,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> ChatMessageOut:
    """
    Phase 24: the assistant answers questions about the student's own
    progress by calling real backend tools (see services/assistant_service.py
    for the system prompt and tool definitions) — it does not freelance
    about missed pages, streaks, or a "generated" revision schedule that
    isn't grounded in the real spaced-repetition data.
    """
    assistant_message = await send_message(db, student, payload.message)
    return to_message_out(assistant_message)


@router.get("/notes", response_model=list[NoteOut])
def list_notes(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> list[NoteOut]:
    notes = (
        db.query(Note)
        .filter(Note.student_id == student.id)
        .order_by(Note.created_at.desc())
        .all()
    )
    return [NoteOut.model_validate(n) for n in notes]


@router.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> NoteOut:
    if payload.client_mutation_id:
        existing = (
            db.query(Note)
            .filter(Note.student_id == student.id, Note.client_mutation_id == payload.client_mutation_id)
            .first()
        )
        if existing is not None:
            return NoteOut.model_validate(existing)

    note = Note(
        student_id=student.id,
        content=payload.content,
        surah_number=payload.surah_number,
        ayah_number=payload.ayah_number,
        client_mutation_id=payload.client_mutation_id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut.model_validate(note)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str, student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> None:
    note = db.get(Note, note_id)
    if note is None or note.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Note not found")
    db.delete(note)
    db.commit()


@router.get("/live-sessions/active", response_model=LiveSessionOut | None)
def get_my_class_active_session(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> LiveSessionOut | None:
    """Phase 25: lets the student's app show a 'join live class' prompt when their class actually has one running."""
    if student.class_id is None:
        return None
    session = get_active_session_for_class(db, student.class_id)
    return to_session_out(session) if session else None


@router.get("/certificates", response_model=list[CertificateOut])
async def list_my_certificates(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> list[CertificateOut]:
    """
    Phase 27: lazily checks for any newly-earned surah/juz completion
    certificates (same self-healing pattern as achievements) before
    returning the full list — nothing here is pre-computed and cached
    stale.
    """
    await check_and_award_certificates(db, student)
    certificates = (
        db.query(Certificate).filter(Certificate.student_id == student.id).order_by(Certificate.issued_at.desc()).all()
    )
    return [
        CertificateOut(
            id=c.id, type=c.type, title=c.title, detail=c.detail,
            issued_by_teacher_name=c.issued_by_teacher.user.name if c.issued_by_teacher else None,
            issued_at=c.issued_at,
        )
        for c in certificates
    ]


@router.get("/certificates/{certificate_id}/pdf")
async def get_my_certificate_pdf(
    certificate_id: str, student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> Response:
    certificate = db.get(Certificate, certificate_id)
    if certificate is None or certificate.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificate not found")

    organization = db.get(Organization, student.user.organization_id)
    pdf_bytes = await render_certificate_pdf(certificate, student.user.name, organization)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/practice-attempts", response_model=list[PracticeAttemptOut])
def list_practice_attempts(
    surah_number: int | None = None,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[PracticeAttemptOut]:
    query = db.query(PracticeAttempt).filter(PracticeAttempt.student_id == student.id)
    if surah_number is not None:
        query = query.filter(PracticeAttempt.surah_number == surah_number)
    attempts = query.order_by(PracticeAttempt.recorded_at.desc()).all()
    return [to_practice_attempt_out(a) for a in attempts]


@router.post("/practice-attempts", response_model=PracticeAttemptOut, status_code=status.HTTP_201_CREATED)
async def create_practice_attempt(
    surah_number: int = Form(...),
    surah_name: str = Form(...),
    from_ayah: int = Form(...),
    to_ayah: int = Form(...),
    duration_seconds: float = Form(...),
    expected_min_seconds: float = Form(...),
    expected_max_seconds: float = Form(...),
    client_mutation_id: str | None = Form(None),
    audio: UploadFile | None = File(None),
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> PracticeAttemptOut:
    if client_mutation_id:
        existing = (
            db.query(PracticeAttempt)
            .filter(
                PracticeAttempt.student_id == student.id,
                PracticeAttempt.client_mutation_id == client_mutation_id,
            )
            .first()
        )
        if existing is not None:
            return to_practice_attempt_out(existing)

    audio_url = await save_audio_file(audio, student.id) if audio is not None else None

    attempt = PracticeAttempt(
        student_id=student.id,
        surah_number=surah_number,
        surah_name=surah_name,
        from_ayah=from_ayah,
        to_ayah=to_ayah,
        duration_seconds=duration_seconds,
        status="recorded",
        expected_min_seconds=expected_min_seconds,
        expected_max_seconds=expected_max_seconds,
        within_expected_range=expected_min_seconds <= duration_seconds <= expected_max_seconds,
        audio_url=audio_url,
        client_mutation_id=client_mutation_id,
    )
    db.add(attempt)
    record_activity_today(student)
    db.add(student)
    db.commit()
    db.refresh(attempt)
    return to_practice_attempt_out(attempt)


@router.get("/test-sessions", response_model=list[TestSessionOut])
def list_test_sessions(
    surah_number: int | None = None,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[TestSessionOut]:
    query = db.query(TestSession).filter(TestSession.student_id == student.id)
    if surah_number is not None:
        query = query.filter(TestSession.surah_number == surah_number)
    sessions = query.order_by(TestSession.completed_at.desc()).all()
    return [to_test_session_out(s) for s in sessions]


@router.post("/test-sessions", response_model=TestSessionOut, status_code=status.HTTP_201_CREATED)
async def create_test_session(
    surah_number: int = Form(...),
    surah_name: str = Form(...),
    from_ayah: int = Form(...),
    to_ayah: int = Form(...),
    client_mutation_id: str | None = Form(None),
    audio: UploadFile = File(...),
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> TestSessionOut:
    """
    Test Mode's one continuous recording across from_ayah..to_ayah: saved
    immediately (so the recording is never lost even if analysis fails),
    then analyzed in the same request — Whisper transcription word-diffed
    against the real reference text, same pipeline Practice Mode uses (see
    `services/test_analysis.py`). Unlike Practice Mode, analysis isn't a
    separate manual step here: a test is meant to end with a real result,
    not a save-then-remember-to-analyze-later two-step.
    """
    if client_mutation_id:
        existing = (
            db.query(TestSession)
            .filter(
                TestSession.student_id == student.id,
                TestSession.client_mutation_id == client_mutation_id,
            )
            .first()
        )
        if existing is not None:
            # Phase 26: this exact offline-queued write already landed —
            # return the row that already exists instead of creating a
            # second one (a retried sync, not a new test session).
            return to_test_session_out(existing)

    audio_url = await save_test_audio_file(audio, student.id)

    session = TestSession(
        student_id=student.id,
        surah_number=surah_number,
        surah_name=surah_name,
        from_ayah=from_ayah,
        to_ayah=to_ayah,
        score_percent=0,
        audio_url=audio_url,
        client_mutation_id=client_mutation_id,
    )
    db.add(session)
    record_activity_today(student)
    db.add(student)
    db.commit()
    db.refresh(session)

    await analyze_test_session(db, session)

    # Phase 13: if this test happens to cover a completed Sabaq's range,
    # feed the score into that Sabaq's SM-2 schedule. Only meaningful once
    # analysis actually produced a real score. Runs after the test session
    # is safely committed so a scheduling hiccup never loses the result.
    if session.analysis_status == "completed":
        schedule = record_test_result(db, student, session)
        if schedule is not None:
            db.commit()

    return to_test_session_out(session)


@router.post("/test-sessions/quiz", response_model=TestSessionOut, status_code=status.HTTP_201_CREATED)
def create_quiz_test_session(
    payload: QuizTestSessionCreate,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> TestSessionOut:
    """Test Modes' multiple-choice/recognition questions — see QuizTestSessionCreate's docstring."""
    session = TestSession(
        student_id=student.id,
        surah_number=payload.surah_number,
        surah_name=payload.surah_name,
        from_ayah=payload.from_ayah,
        to_ayah=payload.to_ayah,
        score_percent=100 if payload.is_correct else 0,
        analysis_status="completed",
    )
    db.add(session)
    db.flush()
    db.add(
        TestResult(
            session_id=session.id,
            ayah_number=payload.from_ayah,
            mark="correct" if payload.is_correct else "missed",
            matched_word_count=1 if payload.is_correct else 0,
            total_word_count=1,
        )
    )
    record_activity_today(student)
    db.add(student)
    db.commit()
    db.refresh(session)

    schedule = record_test_result(db, student, session)
    if schedule is not None:
        db.commit()

    return to_test_session_out(session)


@router.post("/test-sessions/{session_id}/analyze", response_model=TestSessionOut)
async def retry_test_session_analysis(
    session_id: str,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> TestSessionOut:
    """Retries analysis for a session that failed the first time (e.g. no OPENAI_API_KEY configured yet) — same recording, no re-recording needed."""
    session = db.get(TestSession, session_id)
    if session is None or session.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test session not found")

    await analyze_test_session(db, session)

    if session.analysis_status == "completed":
        schedule = record_test_result(db, student, session)
        if schedule is not None:
            db.commit()

    return to_test_session_out(session)


@router.post("/sabaq/{sabaq_id}/status", response_model=SabaqOut)
def update_sabaq_status(
    sabaq_id: str,
    status_value: str,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> SabaqOut:
    """Lets a student mark their own Sabaq in_progress/completed as they work through it."""
    if status_value not in ("not_started", "in_progress", "completed"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")

    sabaq = db.get(Sabaq, sabaq_id)
    if sabaq is None or sabaq.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sabaq not found")

    sabaq.status = status_value
    db.commit()
    db.refresh(sabaq)
    return SabaqOut.model_validate(sabaq)


@router.post("/practice-attempts/{attempt_id}/analyze", response_model=PracticeAttemptOut)
async def analyze_practice_attempt(
    attempt_id: str,
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> PracticeAttemptOut:
    """
    Phase 14: transcribes the attempt's recording (Whisper) and word-diffs
    it against the real ayah text for this attempt's range. An explicit,
    on-demand action — not automatic on save — since it calls a paid
    external API and can take several seconds. See
    `services/arabic_text.py` for exactly what this can and can't detect.

    Never 500s on a transcription/API failure: the analysis row itself
    records `status='failed'` with a real error message (e.g. no API key
    configured), returned to the client like any other analysis result.
    """
    attempt = db.get(PracticeAttempt, attempt_id)
    if attempt is None or attempt.student_id != student.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Practice attempt not found")

    await analyze_attempt(db, attempt)
    db.refresh(attempt)
    return to_practice_attempt_out(attempt)


@router.get("/reviews/due", response_model=list[DueReviewOut])
def list_due_reviews(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> list[DueReviewOut]:
    """
    Every Sabaq currently due for spaced-repetition review, most overdue
    first — the full list the Dashboard's Sabqi/Manzil slots are drawn
    from two items at a time. Powers the dedicated Revision page.
    """
    due = get_due_reviews(db, student.id)
    return [
        DueReviewOut(
            sabaq=SabaqOut.model_validate(sabaq),
            schedule=ReviewScheduleOut(
                repetition_number=schedule.repetition_number,
                ease_factor=round(schedule.ease_factor, 2),
                interval_days=schedule.interval_days,
                due_date=schedule.due_date,
                last_reviewed_date=schedule.last_reviewed_date,
            ),
        )
        for sabaq, schedule in due
    ]


@router.get("/gamification", response_model=GamificationSummary)
def get_gamification_summary(
    student: StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)
) -> GamificationSummary:
    """
    XP, level, and achievements — all computed from real recorded activity
    (see services/gamification.py's module docstring for the exact,
    documented weights). Checks for newly-earned achievements on every
    call, so this is self-healing rather than depending on a hook having
    fired at exactly the right past moment.
    """
    check_and_award_achievements(db, student)

    xp = compute_xp(db, student).total
    level_info = level_for_xp(xp)

    earned = db.query(Achievement).filter(Achievement.student_id == student.id).all()
    earned_keys = {a.achievement_key: a.earned_at for a in earned}

    earned_out = [
        AchievementOut(key=d.key, name=d.name, description=d.description, earned_at=earned_keys[d.key])
        for d in ACHIEVEMENT_DEFS
        if d.key in earned_keys
    ]
    locked_out = [
        AchievementOut(key=d.key, name=d.name, description=d.description, earned_at=None)
        for d in ACHIEVEMENT_DEFS
        if d.key not in earned_keys
    ]

    return GamificationSummary(
        xp=xp,
        level=level_info.level,
        xp_into_level=level_info.xp_into_level,
        xp_to_next_level=level_info.xp_to_next_level,
        earned_achievements=earned_out,
        locked_achievements=locked_out,
    )


@router.get("/leaderboard", response_model=list[LeaderboardEntryOut])
def get_leaderboard_endpoint(
    scope: str = "class",
    student: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[LeaderboardEntryOut]:
    if scope not in ("class", "all"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "scope must be 'class' or 'all'")

    entries = get_leaderboard(db, student, scope)
    return [
        LeaderboardEntryOut(
            rank=i + 1,
            student_id=e.student_id,
            name=e.name,
            xp=e.xp,
            level=e.level,
            is_current_student=e.is_current_student,
        )
        for i, e in enumerate(entries)
    ]
