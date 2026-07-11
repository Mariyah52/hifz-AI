import { useCallback, useEffect, useRef, useState } from 'react';
import { API_BASE_URL, getToken } from '@/services/apiClient';
import type { LiveMistakeEvent, MarkType, PeerRole, RemotePeer } from '@/types/liveSession';

/**
 * Public STUN only (Google's), no TURN server. STUN is enough for most
 * home/mobile networks to establish a direct peer connection; without a
 * TURN relay, a student behind a restrictive/symmetric NAT (common on
 * some corporate or school networks) may simply fail to connect. Running
 * a TURN server (e.g. coturn) is real infrastructure — a deployed,
 * publicly-reachable server with real bandwidth costs — not something
 * this app can stand up as code. This is a genuine, known limitation,
 * not swept under the rug.
 */
const ICE_SERVERS: RTCIceServer[] = [{ urls: 'stun:stun.l.google.com:19302' }];

interface SignalMessage {
  type: 'joined' | 'peer-joined' | 'peer-left' | 'signal' | 'mistake-marked';
  peerId?: string;
  role?: PeerRole;
  name?: string;
  existingPeers?: { peerId: string; role: PeerRole; name: string }[];
  fromPeerId?: string;
  signalType?: 'offer' | 'answer' | 'ice-candidate';
  payload?: unknown;
  studentPeerId?: string;
  markType?: MarkType;
  note?: string | null;
}

function wsUrl(sessionId: string): string {
  const httpUrl = new URL(`/ws/live-sessions/${sessionId}`, API_BASE_URL);
  httpUrl.protocol = httpUrl.protocol === 'https:' ? 'wss:' : 'ws:';
  httpUrl.searchParams.set('token', getToken() ?? '');
  return httpUrl.toString();
}

export function useLiveSession(sessionId: string, myRole: PeerRole) {
  const [peers, setPeers] = useState<Map<string, RemotePeer>>(new Map());
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [micError, setMicError] = useState<string | null>(null);
  const [mistakeEvents, setMistakeEvents] = useState<LiveMistakeEvent[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const myPeerIdRef = useRef<string | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const peerConnectionsRef = useRef<Map<string, RTCPeerConnection>>(new Map());
  const pendingIceRef = useRef<Map<string, RTCIceCandidateInit[]>>(new Map());
  const audioElementsRef = useRef<Map<string, HTMLAudioElement>>(new Map());

  const updatePeer = useCallback((peerId: string, patch: Partial<RemotePeer>) => {
    setPeers((prev) => {
      const next = new Map(prev);
      const existing = next.get(peerId);
      if (existing) next.set(peerId, { ...existing, ...patch });
      return next;
    });
  }, []);

  const sendSignal = useCallback(
    (targetPeerId: string, signalType: 'offer' | 'answer' | 'ice-candidate', payload: unknown) => {
      wsRef.current?.send(JSON.stringify({ type: 'signal', targetPeerId, signalType, payload }));
    },
    [],
  );

  const getOrCreatePeerConnection = useCallback(
    (remotePeerId: string, role: PeerRole, name: string): RTCPeerConnection => {
      const existing = peerConnectionsRef.current.get(remotePeerId);
      if (existing) return existing;

      const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
      localStreamRef.current?.getTracks().forEach((track) => {
        pc.addTrack(track, localStreamRef.current!);
      });

      pc.onicecandidate = (event) => {
        if (event.candidate) sendSignal(remotePeerId, 'ice-candidate', event.candidate.toJSON());
      };

      pc.ontrack = (event) => {
        let audioEl = audioElementsRef.current.get(remotePeerId);
        if (!audioEl) {
          audioEl = new Audio();
          audioEl.autoplay = true;
          audioElementsRef.current.set(remotePeerId, audioEl);
        }
        audioEl.srcObject = event.streams[0];
      };

      pc.onconnectionstatechange = () => {
        updatePeer(remotePeerId, { connectionState: pc.connectionState });
      };

      peerConnectionsRef.current.set(remotePeerId, pc);
      setPeers((prev) => new Map(prev).set(remotePeerId, { peerId: remotePeerId, role, name, connectionState: pc.connectionState }));
      return pc;
    },
    [sendSignal, updatePeer],
  );

  const initiateOfferTo = useCallback(
    async (remotePeerId: string, role: PeerRole, name: string) => {
      const pc = getOrCreatePeerConnection(remotePeerId, role, name);
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      sendSignal(remotePeerId, 'offer', offer);
    },
    [getOrCreatePeerConnection, sendSignal],
  );

  const closePeer = useCallback((peerId: string) => {
    peerConnectionsRef.current.get(peerId)?.close();
    peerConnectionsRef.current.delete(peerId);
    const audioEl = audioElementsRef.current.get(peerId);
    if (audioEl) {
      audioEl.srcObject = null;
      audioElementsRef.current.delete(peerId);
    }
    pendingIceRef.current.delete(peerId);
    setPeers((prev) => {
      const next = new Map(prev);
      next.delete(peerId);
      return next;
    });
  }, []);

  const handleMessage = useCallback(
    async (message: SignalMessage) => {
      if (message.type === 'joined') {
        myPeerIdRef.current = message.peerId ?? null;
        for (const peer of message.existingPeers ?? []) {
          if (myRole === 'student' && peer.role === 'teacher') {
            await initiateOfferTo(peer.peerId, peer.role, peer.name);
          }
        }
        return;
      }

      if (message.type === 'peer-joined') {
        const { peerId, role, name } = message;
        if (!peerId || !role || !name) return;
        if (myRole === 'student' && role === 'teacher') {
          await initiateOfferTo(peerId, role, name);
        } else {
          setPeers((prev) => new Map(prev).set(peerId, { peerId, role, name, connectionState: 'new' }));
        }
        return;
      }

      if (message.type === 'peer-left') {
        if (message.peerId) closePeer(message.peerId);
        return;
      }

      if (message.type === 'mistake-marked') {
        if (message.studentPeerId && message.markType) {
          setMistakeEvents((prev) => [
            ...prev,
            { studentPeerId: message.studentPeerId!, markType: message.markType!, note: message.note ?? null, at: Date.now() },
          ]);
        }
        return;
      }

      if (message.type === 'signal' && message.fromPeerId && message.signalType) {
        const fromPeerId = message.fromPeerId;

        if (message.signalType === 'offer') {
          const existingPeer = peers.get(fromPeerId);
          const pc = getOrCreatePeerConnection(fromPeerId, existingPeer?.role ?? 'student', existingPeer?.name ?? 'Participant');
          await pc.setRemoteDescription(new RTCSessionDescription(message.payload as RTCSessionDescriptionInit));
          const queued = pendingIceRef.current.get(fromPeerId) ?? [];
          for (const candidate of queued) await pc.addIceCandidate(new RTCIceCandidate(candidate));
          pendingIceRef.current.delete(fromPeerId);

          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          sendSignal(fromPeerId, 'answer', answer);
        } else if (message.signalType === 'answer') {
          const pc = peerConnectionsRef.current.get(fromPeerId);
          if (pc) await pc.setRemoteDescription(new RTCSessionDescription(message.payload as RTCSessionDescriptionInit));
        } else if (message.signalType === 'ice-candidate') {
          const pc = peerConnectionsRef.current.get(fromPeerId);
          const candidate = message.payload as RTCIceCandidateInit;
          if (pc && pc.remoteDescription) {
            await pc.addIceCandidate(new RTCIceCandidate(candidate));
          } else {
            const queue = pendingIceRef.current.get(fromPeerId) ?? [];
            queue.push(candidate);
            pendingIceRef.current.set(fromPeerId, queue);
          }
        }
      }
    },
    [myRole, initiateOfferTo, closePeer, getOrCreatePeerConnection, sendSignal, peers],
  );

  const handleMessageRef = useRef(handleMessage);
  useEffect(() => {
    handleMessageRef.current = handleMessage;
  }, [handleMessage]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    async function setup() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        localStreamRef.current = stream;
      } catch {
        setMicError('Microphone access is required to join a live session.');
        return;
      }

      const ws = new WebSocket(wsUrl(sessionId));
      wsRef.current = ws;
      ws.onmessage = (event) => {
        // Always calls the latest handleMessage (via the ref kept in
        // sync above), not whatever closure existed when this listener
        // was attached — handleMessage's own identity changes whenever
        // `peers` updates, but this listener is only ever attached once
        // per session connection.
        handleMessageRef.current(JSON.parse(event.data)).catch(() => {
          // A single malformed/unexpected signaling message shouldn't
          // tear down the whole session — the next message may recover.
        });
      };
      ws.onerror = () => setConnectionError('Lost connection to the live session.');
      ws.onclose = (event) => {
        if (event.code === 4401) setConnectionError('Your session expired — please log in again.');
        else if (event.code === 4403) setConnectionError("You don't have access to this session.");
        else if (event.code === 4404) setConnectionError('This session is no longer live.');
      };
    }

    setup();

    return () => {
      cancelled = true;
      wsRef.current?.close();
      peerConnectionsRef.current.forEach((pc) => pc.close());
      peerConnectionsRef.current.clear();
      localStreamRef.current?.getTracks().forEach((t) => t.stop());
      audioElementsRef.current.forEach((el) => {
        el.srcObject = null;
      });
      audioElementsRef.current.clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const markMistake = useCallback((studentPeerId: string, markType: MarkType, note?: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'mark-mistake', studentPeerId, markType, note: note ?? null }));
  }, []);

  return {
    peers: Array.from(peers.values()),
    micError,
    connectionError,
    mistakeEvents,
    markMistake,
  };
}
