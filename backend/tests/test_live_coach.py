import asyncio

from app.services.arabic_text import ReferenceWord
from app.services.live_coach import LiveCoachSession, TranscriptionError, process_chunk

"""
Tests the service layer directly (constructing a LiveCoachSession by
hand, bypassing start_session's real network call to get_reference_words
-- the same "test the pure logic, mock the network" split as
test_arabic_text.py uses for align() itself). No websocket test here:
this project's own test_live_sessions.py doesn't test the raw WebSocket
protocol layer either, only the REST endpoints around it -- same
precedent followed here.

Plain sync test functions wrapping asyncio.run() rather than
pytest.mark.asyncio, since this project doesn't already depend on
pytest-asyncio -- no reason to add a new test-only dependency for this.
"""


def _session(words: list[str]) -> LiveCoachSession:
    return LiveCoachSession(
        surah_number=67, from_ayah=1, to_ayah=1,
        reference_words=[ReferenceWord(word=w, ayah_number=1) for w in words],
    )


def test_first_chunk_transcribes_and_aligns(monkeypatch):
    session = _session(["الملك", "بيده", "الملك"])

    async def fake_transcribe(_path: str) -> str:
        return "الملك بيده"

    monkeypatch.setattr("app.services.live_coach.transcribe_audio", fake_transcribe)

    update = asyncio.run(process_chunk(session, audio_bytes=b"fake-audio-bytes"))

    assert update.chunk_number == 1
    assert update.total_reference_word_count == 3
    assert update.matched_word_count == 2
    assert update.chunk_transcription_error is None
    assert session.cumulative_transcript == "الملك بيده"


def test_second_chunk_appends_to_cumulative_transcript(monkeypatch):
    session = _session(["الملك", "بيده", "الملك"])
    session.cumulative_transcript = "الملك بيده"
    session.chunks_processed = 1

    async def fake_transcribe(_path: str) -> str:
        return "الملك"

    monkeypatch.setattr("app.services.live_coach.transcribe_audio", fake_transcribe)

    update = asyncio.run(process_chunk(session, audio_bytes=b"fake-audio-bytes-2"))

    assert update.chunk_number == 2
    assert session.cumulative_transcript == "الملك بيده الملك"
    assert update.matched_word_count == 3
    assert len(update.mistakes) == 0


def test_a_failed_chunk_transcription_does_not_lose_prior_progress(monkeypatch):
    session = _session(["الملك", "بيده"])
    session.cumulative_transcript = "الملك"
    session.chunks_processed = 1

    async def failing_transcribe(_path: str) -> str:
        raise TranscriptionError("network blip")

    monkeypatch.setattr("app.services.live_coach.transcribe_audio", failing_transcribe)

    update = asyncio.run(process_chunk(session, audio_bytes=b"fake-audio-bytes-3"))

    assert update.chunk_transcription_error == "network blip"
    assert session.cumulative_transcript == "الملك"
    assert update.matched_word_count == 1


def test_a_recitation_mistake_is_reported(monkeypatch):
    session = _session(["الملك", "بيده", "الملك"])

    async def fake_transcribe(_path: str) -> str:
        return "الملك بيدك الملك"

    monkeypatch.setattr("app.services.live_coach.transcribe_audio", fake_transcribe)

    update = asyncio.run(process_chunk(session, audio_bytes=b"fake-audio-bytes"))

    assert update.matched_word_count == 2
    assert len(update.mistakes) == 1
    assert update.mistakes[0].mistake_type == "substituted"
