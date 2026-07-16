import os
import tempfile
from dataclasses import dataclass

from app.services.arabic_text import Mistake, ReferenceWord, align
from app.services.quran_text import get_reference_words
from app.services.transcription import TranscriptionError, transcribe_audio

"""
Phase 33: "real-time" recitation coach — v1.

Read this before assuming it's true streaming speech recognition. It
ISN'T, and the difference matters for both cost and what "real-time"
actually means here:

WHAT THIS ACTUALLY DOES: the student's browser records in short chunks
(recommended: 6-8 seconds each) and sends each chunk to this backend as
it finishes. Each chunk gets transcribed independently by the SAME
Whisper API call used for regular Practice/Test analysis
(services/transcription.py) — there is no cheaper or faster transcription
path for chunks. The chunk's text is appended to a running transcript for
the session, and `arabic_text.align()` re-runs against the FULL reference
range each time, so the student sees updated mistake feedback every
6-8 seconds instead of only after the entire recording finishes.

WHAT THIS IS NOT: true streaming ASR would transcribe continuously with
sub-second latency and word-by-word partial results, the way live
captioning works. That needs a fundamentally different audio pipeline
(a streaming-capable model, a persistent connection to it, incremental
decoding) — a real, separate infrastructure project, not a variation on
this one. If a much shorter feedback latency is ever required, revisit
this file's architecture rather than just shortening the chunk interval.

REAL COST IMPLICATION, not hidden: chunking multiplies Whisper API calls.
A single 2-minute recitation that would cost one Whisper call as a normal
Practice attempt costs roughly (120 seconds / chunk_length_seconds) calls
here — at an 8-second chunk length, that's ~15 calls instead of 1. This
is a genuine, real tradeoff for lower-latency feedback, not a rounding
error — factor it into whichever plan tier can access this feature.
"""


@dataclass
class LiveCoachSession:
    surah_number: int
    from_ayah: int
    to_ayah: int
    reference_words: list[ReferenceWord]
    cumulative_transcript: str = ""
    chunks_processed: int = 0


@dataclass
class LiveCoachUpdate:
    chunk_number: int
    matched_word_count: int
    total_reference_word_count: int
    mistakes: list[Mistake]
    chunk_transcription_error: str | None = None


async def start_session(surah_number: int, from_ayah: int, to_ayah: int) -> LiveCoachSession:
    reference_words = await get_reference_words(surah_number, from_ayah, to_ayah)
    return LiveCoachSession(
        surah_number=surah_number, from_ayah=from_ayah, to_ayah=to_ayah, reference_words=reference_words
    )


async def process_chunk(session: LiveCoachSession, audio_bytes: bytes, file_suffix: str = ".webm") -> LiveCoachUpdate:
    """
    Transcribes one audio chunk and returns updated feedback for the
    WHOLE session so far (not just this chunk) — simpler and more
    correct than trying to diff only the new portion, and cheap to do
    since re-running align() is pure in-memory difflib, not another API
    call. A transcription failure on one chunk (network blip, API error)
    doesn't end the session — it's reported on this update and the
    session keeps accepting further chunks with the transcript it has
    so far.
    """
    session.chunks_processed += 1
    chunk_error: str | None = None

    with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        chunk_text = await transcribe_audio(tmp_path)
        session.cumulative_transcript = (session.cumulative_transcript + " " + chunk_text).strip()
    except TranscriptionError as exc:
        chunk_error = str(exc)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    matched, mistakes = align(session.reference_words, session.cumulative_transcript)

    return LiveCoachUpdate(
        chunk_number=session.chunks_processed,
        matched_word_count=matched,
        total_reference_word_count=len(session.reference_words),
        mistakes=mistakes,
        chunk_transcription_error=chunk_error,
    )
