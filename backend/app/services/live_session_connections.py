from dataclasses import dataclass

from fastapi import WebSocket

"""
In-process, single-server, same caveat as the scheduler (Phase 16) and
rate limiter (Phase 17): this dict lives in this Python process's
memory. One server handles WebRTC signaling for however many sessions
are live on it; running more than one instance without a shared
message bus (e.g. Redis pub/sub) would split a class's teacher and
students across processes that can't relay to each other. Fine for a
single-server deployment, the honest limit to know about before scaling
this beyond one.

This registry only relays signaling messages (WebRTC SDP offers/answers,
ICE candidates, mistake marks) — it never touches audio itself. Audio is
peer-to-peer between browsers via WebRTC once signaling completes.
"""


@dataclass
class ConnectedPeer:
    websocket: WebSocket
    role: str
    name: str


class LiveSessionConnectionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, ConnectedPeer]] = {}

    async def connect(self, session_id: str, peer_id: str, role: str, name: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sessions.setdefault(session_id, {})[peer_id] = ConnectedPeer(websocket, role, name)

    def disconnect(self, session_id: str, peer_id: str) -> None:
        peers = self._sessions.get(session_id)
        if peers is None:
            return
        peers.pop(peer_id, None)
        if not peers:
            self._sessions.pop(session_id, None)

    def existing_peers(self, session_id: str, exclude_peer_id: str) -> list[dict]:
        return [
            {"peerId": pid, "role": p.role, "name": p.name}
            for pid, p in self._sessions.get(session_id, {}).items()
            if pid != exclude_peer_id
        ]

    async def send_to_peer(self, session_id: str, peer_id: str, message: dict) -> None:
        target = self._sessions.get(session_id, {}).get(peer_id)
        if target is not None:
            await target.websocket.send_json(message)

    async def broadcast(self, session_id: str, message: dict, exclude_peer_id: str | None = None) -> None:
        for peer_id, peer in list(self._sessions.get(session_id, {}).items()):
            if peer_id == exclude_peer_id:
                continue
            try:
                await peer.websocket.send_json(message)
            except Exception:
                continue


live_session_connections = LiveSessionConnectionManager()
