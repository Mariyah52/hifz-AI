import { API_BASE_URL, getToken } from '@/services/apiClient';
import type {
  LiveCoachChunkResultMessage,
  LiveCoachStartedMessage,
} from '@/types/liveCoach';

function wsBaseUrl(): string {
  return API_BASE_URL.replace(/^http/, 'ws');
}

export interface LiveCoachSocketHandlers {
  onStarted: (msg: LiveCoachStartedMessage) => void;
  onChunkResult: (msg: LiveCoachChunkResultMessage) => void;
  onError: (message: string) => void;
  onClose: () => void;
}

export class LiveCoachSocket {
  private ws: WebSocket | null = null;

  connect(
    params: { surahNumber: number; fromAyah: number; toAyah: number },
    handlers: LiveCoachSocketHandlers,
  ): void {
    const token = getToken();
    if (!token) {
      handlers.onError('You must be signed in to use the live coach.');
      return;
    }

    const ws = new WebSocket(
      `${wsBaseUrl()}/ws/live-coach?token=${encodeURIComponent(token)}`,
    );
    ws.binaryType = 'arraybuffer';
    this.ws = ws;

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          type: 'start',
          surahNumber: params.surahNumber,
          fromAyah: params.fromAyah,
          toAyah: params.toAyah,
        }),
      );
    };

    ws.onmessage = (event) => {
      if (typeof event.data !== 'string') return;
      let msg: { type?: string; message?: string } & Record<string, unknown>;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }
      if (msg.type === 'started') {
        handlers.onStarted(msg as unknown as LiveCoachStartedMessage);
      } else if (msg.type === 'chunk_result') {
        handlers.onChunkResult(msg as unknown as LiveCoachChunkResultMessage);
      } else if (msg.type === 'error') {
        handlers.onError(msg.message ?? 'Live coach reported an error.');
      }
    };

    ws.onerror = () => {
      handlers.onError('Connection to the live coach was lost.');
    };

    ws.onclose = () => {
      handlers.onClose();
    };
  }

  sendChunk(blob: Blob): void {
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    blob.arrayBuffer().then((buf) => {
      if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(buf);
    });
  }

  end(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'end' }));
    }
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}
