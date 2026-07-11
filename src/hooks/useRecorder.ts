import { useCallback, useRef, useState } from 'react';
import { createRecorder, requestMicrophoneStream, stopStreamTracks } from '@/services/recordingService';

export type RecorderStatus = 'idle' | 'requesting' | 'recording' | 'stopped' | 'error';

export function useRecorder() {
  const [status, setStatus] = useState<RecorderStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [durationSeconds, setDurationSeconds] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const startedAtRef = useRef(0);

  const start = useCallback(async () => {
    setError(null);
    setStatus('requesting');
    try {
      const stream = await requestMicrophoneStream();
      streamRef.current = stream;

      const recorder = createRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        setAudioBlob(blob);
        setAudioUrl((prevUrl) => {
          if (prevUrl) URL.revokeObjectURL(prevUrl);
          return URL.createObjectURL(blob);
        });
        setDurationSeconds((Date.now() - startedAtRef.current) / 1000);
        if (streamRef.current) stopStreamTracks(streamRef.current);
        setStatus('stopped');
      };

      mediaRecorderRef.current = recorder;
      startedAtRef.current = Date.now();
      recorder.start();
      setStatus('recording');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Microphone access was denied.');
      setStatus('error');
    }
  }, []);

  const stop = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  const reset = useCallback(() => {
    setAudioUrl((prevUrl) => {
      if (prevUrl) URL.revokeObjectURL(prevUrl);
      return null;
    });
    setAudioBlob(null);
    setDurationSeconds(0);
    setError(null);
    setStatus('idle');
  }, []);

  return { status, error, audioUrl, audioBlob, durationSeconds, start, stop, reset };
}
