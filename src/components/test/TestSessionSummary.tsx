import { ProgressRing } from '@/components/ui/ProgressRing';
import { MistakeList } from '@/components/practice/MistakeList';
import type { TestSession } from '@/types/test';

interface TestSessionSummaryProps {
  session: TestSession;
}

export function TestSessionSummary({ session }: TestSessionSummaryProps) {
  if (session.analysisStatus !== 'completed') {
    return null; // TestRunner shows the failed/pending state itself.
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col items-center gap-2">
        <ProgressRing value={session.scorePercent} label={`${session.scorePercent}%`} tone="gold" />
        <p className="font-mono text-xs text-ink-soft">
          {session.matchedWordCount}/{session.totalWordCount} words matched
        </p>
        <p className="text-xs text-ink-soft font-body text-center">
          AI-scored from your recording — a real Whisper transcription word-diffed against the actual
          ayah text, not self-reported.
        </p>
      </div>

      <div>
        <p className="font-body font-semibold text-ink text-sm mb-2">Word-level differences</p>
        <MistakeList mistakes={session.mistakes} />
      </div>
    </div>
  );
}
