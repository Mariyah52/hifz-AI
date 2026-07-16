import os
from dataclasses import dataclass

import httpx

from app.config import settings

WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"


class TranscriptionError(Exception):
    pass


async def transcribe_audio(file_path: str) -> str:
    """
    Sends the recording to OpenAI's Whisper API and returns the
    transcribed Arabic text. Costs real money per call — this is why
    analysis is an explicit, on-demand action (see the /analyze endpoint)
    rather than something run automatically on every saved attempt.
    """
    if not settings.openai_api_key:
        raise TranscriptionError(
            "Recitation analysis isn't configured on this server — OPENAI_API_KEY is unset."
        )

    if not os.path.isfile(file_path):
        raise TranscriptionError("No audio file found for this attempt.")

    async with httpx.AsyncClient(timeout=90.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                WHISPER_API_URL,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                files={"file": (os.path.basename(file_path), f, "application/octet-stream")},
                data={"model": "whisper-1", "language": "ar"},
            )

    if response.status_code != 200:
        raise TranscriptionError(f"Transcription request failed (HTTP {response.status_code}): {response.text[:300]}")

    body = response.json()
    text = body.get("text")
    if not text:
        raise TranscriptionError("Transcription succeeded but returned no text.")
    return text


@dataclass
class WordTiming:
    word: str
    start_seconds: float
    end_seconds: float


async def transcribe_audio_with_word_timestamps(file_path: str) -> list[WordTiming]:
    """
    Same Whisper API, same cost-per-call as transcribe_audio — the only
    difference is requesting `response_format=verbose_json` with
    `timestamp_granularities[]=word`, which makes Whisper return each
    word's real start/end time in the recording. This is what makes
    tajweed_analysis.py's elongation check possible without needing any
    separate audio-decoding library (ffmpeg, pydub, librosa, ...) on this
    server — Whisper does the acoustic timing work, this app just reads
    the timestamps back out of its response.
    """
    if not settings.openai_api_key:
        raise TranscriptionError(
            "Recitation analysis isn't configured on this server — OPENAI_API_KEY is unset."
        )
    if not os.path.isfile(file_path):
        raise TranscriptionError("No audio file found for this attempt.")

    async with httpx.AsyncClient(timeout=90.0) as client:
        with open(file_path, "rb") as f:
            response = await client.post(
                WHISPER_API_URL,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                files={"file": (os.path.basename(file_path), f, "application/octet-stream")},
                data={
                    "model": "whisper-1",
                    "language": "ar",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "word",
                },
            )

    if response.status_code != 200:
        raise TranscriptionError(f"Transcription request failed (HTTP {response.status_code}): {response.text[:300]}")

    body = response.json()
    raw_words = body.get("words")
    if not raw_words:
        raise TranscriptionError(
            "Transcription succeeded but returned no word-level timestamps "
            "(Whisper omits these for very short or silent audio)."
        )
    return [
        WordTiming(word=w["word"], start_seconds=w["start"], end_seconds=w["end"])
        for w in raw_words
    ]
