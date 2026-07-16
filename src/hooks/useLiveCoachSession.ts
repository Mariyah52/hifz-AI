import { useCallback, useRef, useState } from 'react';
import {
  createRecorder,
  requestMicrophoneStream,
  stopStreamTracks,
} from '@/services/recordingService';
import { LiveCoachSocket } from '@/services/liveCoachSocket';
import type { LiveCoachMistake } from '@/types/liveCoach';

export type LiveCoachStatus =
  | 'idle'
  | 'connecting'
  | 'reciting'
  | 'stopped'
  | 'error';

const CHUNK_INTERVAL_MS = 7000;

export function useLiveCoachSession() {
  const [status, setStatus] = useState<LiveCoachStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [totalReferenceWordCount, setTotalReferenceWordCount] = useState(0);
  const [matchedWordCount, setMatchedWordCount] = useState(0);
  const [mistakes, setMistakes] = useState<LiveCoachMistake[]>([]);

  const socketRef = useRef<LiveCoachSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const start = useCallback(
    async (surahNumber: number, fromAyah: number, toAyah: number) => {
      setError(null);
      setMistakes([]);
      setMatchedWordCount(0);
      setTotalReferenceWordCount(0);
      setStatus('connecting');

      const socket = new LiveCoachSocket();
      socketRef.current = socket;

      socket.connect(
        { surahNumber, fromAyah, toAyah },
        {
          onStarted: async (msg) => {
            setTotalReferenceWordCount(msg.totalReferenceWordCount);
            try {
              const stream = await requestMicrophoneStream();
              streamRef.current = stream;
              const recorder = createRecorder(stream);
              recorder.ondataavailable = (event) => {
                if (event.data.size > 0) socket.sendChunk(event.data);
              };
              mediaRecorderRef.current = recorder;
              recorder.start(CHUNK_INTERVAL_MS);
              setStatus('reciting');
            } catch (err) {
              setError(
                err instanceof Error
                  ? err.message
                  : 'Microphone access was denied.',
              );
              setStatus('error');
              socket.disconnect();
            }
          },
          onChunkResult: (msg) => {
            setMatchedWordCount(msg.matchedWordCount);
            setTotalReferenceWordCount(msg.totalReferenceWordCount);
            if (msg.mistakes.length > 0) {
              setMistakes((prev) => [...prev, ...msg.mistakes]);
            }
          },
          onError: (message) => {
            setError(message);
            setStatus('error');
          },
          onClose: () => {
            setStatus((prev) => (prev === 'reciting' ? 'stopped' : prev));
          },
        },
      );
    },
    [],
  );

  const stop = useCallback(() => {
    mediaRecorderRef.current?.stop();
    if (streamRef.current) stopStreamTracks(streamRef.current);
    socketRef.current?.end();
    socketRef.current?.disconnect();
    setStatus('stopped');
  }, []);

  const reset = useCallback(() => {
    setStatus('idle');
    setError(null);
    setMistakes([]);
    setMatchedWordCount(0);
    setTotalReferenceWordCount(0);
  }, []);

  return {
    status,
    error,
    totalReferenceWordCount,
    matchedWordCount,
    mistakes,
    start,
    stop,
    reset,
  };
}
