import os
from collections import defaultdict

from sqlalchemy.orm import Session

from app.config import settings
from app.models.test import TestMistakeRow, TestResult, TestSession
from app.services.arabic_text import align
from app.services.quran_text import ReferenceTextError, get_reference_words
from app.services.transcription import TranscriptionError, transcribe_audio


class AnalysisNotAvailable(Exception):
    pass


def _audio_disk_path(session: TestSession) -> str:
    if not session.audio_url:
        raise AnalysisNotAvailable("This test session has no uploaded recording to analyze.")
    relative = session.audio_url.removeprefix("/media/")
    return os.path.join(settings.media_root, relative)


async def analyze_test_session(db: Session, session: TestSession) -> TestSession:
    """
    Runs (or re-runs) AI analysis for one continuous test recording:
    transcribe it once (Whisper), word-diff against the real reference text
    for the session's whole from_ayah..to_ayah range, then bucket the
    result back per-ayah for `TestResult` rows — same pipeline
    `recitation_analysis.py` uses for Practice Mode, just applied across a
    multi-ayah range in one pass instead of one attempt at a time.

    Always returns the session — on failure (missing API key, network
    error, transcription failure) it records `analysis_status='failed'`
    with a real error message rather than raising past this point, exactly
    like Practice Mode's analyze_attempt, so a bad external-API call
    doesn't 500 the request and the recording itself is never lost.
    """
    try:
        audio_path = _audio_disk_path(session)
        reference_words = await get_reference_words(session.surah_number, session.from_ayah, session.to_ayah)
        transcribed_text = await transcribe_audio(audio_path)
        _matched_total, mistakes = align(reference_words, transcribed_text)

        # Per-ayah reference word counts, to turn the flat mistake list
        # back into a per-ayah tally.
        total_per_ayah: dict[int, int] = defaultdict(int)
        for word in reference_words:
            total_per_ayah[word.ayah_number] += 1

        missed_per_ayah: dict[int, int] = defaultdict(int)
        for mistake in mistakes:
            if mistake.ayah_number is not None and mistake.mistake_type in ("missing", "substituted"):
                missed_per_ayah[mistake.ayah_number] += 1

        db.query(TestResult).filter(TestResult.session_id == session.id).delete()
        db.query(TestMistakeRow).filter(TestMistakeRow.session_id == session.id).delete()

        matched_total = 0
        total_words = 0
        for ayah_number in range(session.from_ayah, session.to_ayah + 1):
            total = total_per_ayah.get(ayah_number, 0)
            missed = min(missed_per_ayah.get(ayah_number, 0), total)
            matched = total - missed
            matched_total += matched
            total_words += total
            db.add(
                TestResult(
                    session_id=session.id,
                    ayah_number=ayah_number,
                    mark="correct" if missed == 0 else "missed",
                    matched_word_count=matched,
                    total_word_count=total,
                )
            )

        for mistake in mistakes:
            db.add(
                TestMistakeRow(
                    session_id=session.id,
                    position=mistake.position,
                    mistake_type=mistake.mistake_type,
                    ayah_number=mistake.ayah_number,
                    reference_word=mistake.reference_word,
                    transcribed_word=mistake.transcribed_word,
                )
            )

        session.analysis_status = "completed"
        session.analysis_error = None
        session.score_percent = round((matched_total / total_words) * 100) if total_words else 0

    except (AnalysisNotAvailable, ReferenceTextError, TranscriptionError) as exc:
        session.analysis_status = "failed"
        session.analysis_error = str(exc)

    db.add(session)
    db.commit()
    db.refresh(session)
    return session
