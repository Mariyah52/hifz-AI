import os

from sqlalchemy.orm import Session

from app.config import settings
from app.models.practice import PracticeAttempt
from app.models.practice_analysis import PracticeAttemptAnalysis, PracticeMistakeRow
from app.services.arabic_text import align
from app.services.quran_text import ReferenceTextError, get_reference_words
from app.services.transcription import TranscriptionError, transcribe_audio


class AnalysisNotAvailable(Exception):
    pass


def _audio_disk_path(attempt: PracticeAttempt) -> str:
    if not attempt.audio_url:
        raise AnalysisNotAvailable("This attempt has no uploaded recording to analyze.")
    relative = attempt.audio_url.removeprefix("/media/")
    return os.path.join(settings.media_root, relative)


async def analyze_attempt(db: Session, attempt: PracticeAttempt) -> PracticeAttemptAnalysis:
    """
    Runs (or re-runs) analysis for one practice attempt and persists the
    result. Always returns a row — on failure (missing API key, network
    error, transcription failure) it stores `status='failed'` with a
    real error message rather than raising past this point, so a bad
    external-API call doesn't 500 the whole request; the caller decides
    how to present a failed analysis.
    """
    existing = db.query(PracticeAttemptAnalysis).filter(PracticeAttemptAnalysis.attempt_id == attempt.id).first()

    try:
        audio_path = _audio_disk_path(attempt)
        reference_words = await get_reference_words(attempt.surah_number, attempt.from_ayah, attempt.to_ayah)
        transcribed_text = await transcribe_audio(audio_path)
        matched, mistakes = align(reference_words, transcribed_text)

        if existing:
            db.query(PracticeMistakeRow).filter(PracticeMistakeRow.analysis_id == existing.id).delete()
            analysis = existing
            analysis.status = "completed"
            analysis.error_message = None
            analysis.transcribed_text = transcribed_text
            analysis.reference_word_count = len(reference_words)
            analysis.matched_word_count = matched
        else:
            analysis = PracticeAttemptAnalysis(
                attempt_id=attempt.id,
                status="completed",
                transcribed_text=transcribed_text,
                reference_word_count=len(reference_words),
                matched_word_count=matched,
            )
            db.add(analysis)
            db.flush()

        for mistake in mistakes:
            db.add(
                PracticeMistakeRow(
                    analysis_id=analysis.id,
                    position=mistake.position,
                    mistake_type=mistake.mistake_type,
                    ayah_number=mistake.ayah_number,
                    reference_word=mistake.reference_word,
                    transcribed_word=mistake.transcribed_word,
                )
            )

    except (AnalysisNotAvailable, ReferenceTextError, TranscriptionError) as exc:
        if existing:
            db.query(PracticeMistakeRow).filter(PracticeMistakeRow.analysis_id == existing.id).delete()
            analysis = existing
            analysis.status = "failed"
            analysis.error_message = str(exc)
        else:
            analysis = PracticeAttemptAnalysis(attempt_id=attempt.id, status="failed", error_message=str(exc))
            db.add(analysis)

    db.commit()
    db.refresh(analysis)
    return analysis
