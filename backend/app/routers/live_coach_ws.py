import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.models.user import StudentProfile, User
from app.security import decode_access_token
from app.services.arabic_text import Mistake
from app.services.live_coach import LiveCoachUpdate, process_chunk, start_session
from app.services.quran_text import ReferenceTextError

router = APIRouter()

"""
See services/live_coach.py's module docstring first — this is chunked
near-real-time feedback (Whisper-per-chunk), not true streaming ASR.

Message protocol (student's browser <-> here):
  Client sends first, as JSON text:
    {"type": "start", "surahNumber": 67, "fromAyah": 1, "toAyah": 5}
  Server replies:
    {"type": "started", "totalReferenceWordCount": 42}
    or {"type": "error", "message": "..."} then closes.
  Client then sends each ~6-8s audio chunk as BINARY frames (raw audio
  bytes, e.g. webm/opus from MediaRecorder) — one binary frame per chunk.
  Server replies after each chunk, as JSON text:
    {"type": "chunk_result", "chunkNumber": 1, "matchedWordCount": 12,
     "totalReferenceWordCount": 42, "mistakes": [...],
     "chunkTranscriptionError": null}
  Client sends {"type": "end"} (JSON text) when the student stops
  reciting, server closes normally.

Same query-param JWT auth as /ws/live-sessions — see that router's note
on why (browsers can't set custom headers on the WebSocket handshake).
"""


def _mistake_to_dict(mistake: Mistake) -> dict:
    return {
        "position": mistake.position,
        "mistakeType": mistake.mistake_type,
        "ayahNumber": mistake.ayah_number,
        "referenceWord": mistake.reference_word,
        "transcribedWord": mistake.transcribed_word,
    }


def _update_to_dict(update: LiveCoachUpdate) -> dict:
    return {
        "type": "chunk_result",
        "chunkNumber": update.chunk_number,
        "matchedWordCount": update.matched_word_count,
        "totalReferenceWordCount": update.total_reference_word_count,
        "mistakes": [_mistake_to_dict(m) for m in update.mistakes],
        "chunkTranscriptionError": update.chunk_transcription_error,
    }


@router.websocket("/ws/live-coach")
async def live_coach_socket(websocket: WebSocket, token: str) -> None:
    db = SessionLocal()
    try:
        try:
            payload = decode_access_token(token)
        except ValueError:
            await websocket.close(code=4401)
            return

        user = db.get(User, payload["sub"])
        student = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first() if user else None
        if student is None:
            await websocket.close(code=4403)  # Only students recite; teachers/parents/admins don't use this.
            return

        await websocket.accept()

        start_message = await websocket.receive_json()
        if start_message.get("type") != "start":
            await websocket.send_json({"type": "error", "message": "First message must be type 'start'."})
            await websocket.close(code=4400)
            return

        try:
            session = await start_session(
                surah_number=start_message["surahNumber"],
                from_ayah=start_message["fromAyah"],
                to_ayah=start_message["toAyah"],
            )
        except ReferenceTextError as exc:
            await websocket.send_json({"type": "error", "message": str(exc)})
            await websocket.close(code=4404)
            return
        except KeyError as exc:
            await websocket.send_json({"type": "error", "message": f"Missing field in start message: {exc}"})
            await websocket.close(code=4400)
            return

        await websocket.send_json(
            {"type": "started", "totalReferenceWordCount": len(session.reference_words)}
        )

        try:
            while True:
                message = await websocket.receive()

                if message.get("type") == "websocket.disconnect":
                    break

                if "bytes" in message and message["bytes"] is not None:
                    update = await process_chunk(session, message["bytes"])
                    await websocket.send_json(_update_to_dict(update))

                elif "text" in message and message["text"] is not None:
                    try:
                        parsed = json.loads(message["text"])
                    except json.JSONDecodeError:
                        continue
                    if parsed.get("type") == "end":
                        break

        except WebSocketDisconnect:
            pass
    finally:
        db.close()
