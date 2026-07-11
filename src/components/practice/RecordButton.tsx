import { Mic, Square } from 'lucide-react';
import type { RecorderStatus } from '@/hooks/useRecorder';

interface RecordButtonProps {
  status: RecorderStatus;
  onStart: () => void;
  onStop: () => void;
}

export function RecordButton({ status, onStart, onStop }: RecordButtonProps) {
  const isRecording = status === 'recording';
  const isRequesting = status === 'requesting';

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        onClick={isRecording ? onStop : onStart}
        disabled={isRequesting}
        className={`grid h-20 w-20 place-items-center rounded-full transition-colors disabled:opacity-50 ${
          isRecording ? 'bg-maroon text-paper animate-pulse' : 'bg-teal text-paper hover:bg-teal-dark'
        }`}
      >
        {isRecording ? <Square size={26} fill="currentColor" /> : <Mic size={28} />}
      </button>
      <p className="font-mono text-xs text-ink-soft">
        {isRequesting && 'Requesting microphone…'}
        {isRecording && 'Recording — tap to stop'}
        {status === 'idle' && 'Tap to record'}
        {status === 'stopped' && 'Tap to record again'}
      </p>
    </div>
  );
}
