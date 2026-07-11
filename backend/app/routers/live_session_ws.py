from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.models.live_session import LiveSession
from app.models.user import StudentProfile, TeacherProfile, User
from app.security import decode_access_token
from app.services.live_session_connections import live_session_connections
from app.services.live_session_service import record_join, record_leave, record_mistake

router = APIRouter()

"""
Signaling only — this endpoint relays WebRTC SDP offers/answers and ICE
candidates (and lightweight mistake-mark messages) between a teacher's
browser and however many students have joined. It never touches audio
itself; once two peers exchange signaling through here, their audio
flows directly between their browsers over WebRTC.

Auth note: browsers' native WebSocket API can't send custom headers, so
the access token travels as a query parameter (`?token=...`) instead of
an Authorization header — the standard, if slightly unusual-looking,
way to authenticate a WebSocket handshake. Same JWT, same validity
window as everywhere else.
"""


def _authenticate(token: str, db) -> tuple[User, StudentProfile | None, TeacherProfile | None]:
    payload = decode_access_token(token)  # raises ValueError if invalid/expired
    user = db.get(User, payload["sub"])
    if user is None:
        raise ValueError("User no longer exists")

    student = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    teacher = db.query(TeacherProfile).filter(TeacherProfile.user_id == user.id).first()
    return user, student, teacher


@router.websocket("/ws/live-sessions/{session_id}")
async def live_session_socket(websocket: WebSocket, session_id: str, token: str) -> None:
    db = SessionLocal()
    try:
        try:
            user, student, teacher = _authenticate(token, db)
        except ValueError:
            await websocket.close(code=4401)
            return

        session = db.get(LiveSession, session_id)
        if session is None or session.status != "live":
            await websocket.close(code=4404)
            return

        is_this_teacher = teacher is not None and session.teacher_id == teacher.id
        is_class_student = student is not None and student.class_id == session.class_id
        if not is_this_teacher and not is_class_student:
            await websocket.close(code=4403)
            return

        peer_id = user.id
        role = "teacher" if is_this_teacher else "student"
        name = user.name

        existing_peers = live_session_connections.existing_peers(session_id, exclude_peer_id=peer_id)
        await live_session_connections.connect(session_id, peer_id, role, name, websocket)

        if is_class_student:
            record_join(db, session_id, student.id)

        await websocket.send_json(
            {"type": "joined", "peerId": peer_id, "role": role, "name": name, "existingPeers": existing_peers}
        )
        await live_session_connections.broadcast(
            session_id, {"type": "peer-joined", "peerId": peer_id, "role": role, "name": name}, exclude_peer_id=peer_id
        )

        try:
            while True:
                message = await websocket.receive_json()
                msg_type = message.get("type")

                if msg_type == "signal":
                    target_peer_id = message.get("targetPeerId")
                    if target_peer_id:
                        await live_session_connections.send_to_peer(
                            session_id,
                            target_peer_id,
                            {
                                "type": "signal",
                                "fromPeerId": peer_id,
                                "signalType": message.get("signalType"),
                                "payload": message.get("payload"),
                            },
                        )

                elif msg_type == "mark-mistake" and is_this_teacher:
                    student_peer_id = message.get("studentPeerId")
                    mark_type = message.get("markType")
                    note = message.get("note")
                    target_student = db.query(StudentProfile).join(User).filter(User.id == student_peer_id).first()
                    if target_student is not None and mark_type in ("perfect", "hesitation", "mistake"):
                        record_mistake(db, session_id, target_student.id, mark_type, note)
                        await live_session_connections.broadcast(
                            session_id,
                            {
                                "type": "mistake-marked",
                                "studentPeerId": student_peer_id,
                                "markType": mark_type,
                                "note": note,
                            },
                        )

        except WebSocketDisconnect:
            pass
        finally:
            live_session_connections.disconnect(session_id, peer_id)
            if is_class_student:
                record_leave(db, session_id, student.id)
            await live_session_connections.broadcast(session_id, {"type": "peer-left", "peerId": peer_id})
    finally:
        db.close()
