import { Pause, Play, RotateCcw } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { RecordButton } from '@/components/practice/RecordButton';
import { HiddenAyahPlaceholder } from '@/components/test/HiddenAyahPlaceholder';
import { TestSessionSummary } from '@/components/test/TestSessionSummary';
import { useTestSession } from '@/hooks/useTestSession';
import type { TestSession } from '@/types/test';

interface TestRunnerProps {
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  onFinish: (session: TestSession) => void;
}

export function TestRunner({ surahNumber, surahName, fromAyah, toAyah, onFinish }: TestRunnerProps) {
  const t = useTestSession({ surahNumber, surahName, fromAyah, toAyah });

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono">
          {t.phase === 'analyzing'
            ? 'Analyzing…'
            : t.phase === 'complete'
              ? 'Complete'
              : `Ayah ${fromAyah}–${toAyah}`}
        </p>
      </div>

      {t.phase === 'setup' && (
        <>
          <HiddenAyahPlaceholder fromAyah={fromAyah} toAyah={toAyah} />

          <div className="flex items-center gap-3">
            <button
              aria-label={t.isReferencePlaying ? 'Pause reference audio' : 'Play reference audio'}
              onClick={t.toggleReference}
              className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-teal/10 text-teal-dark hover:bg-teal/20 transition-colors"
            >
              {t.isReferencePlaying ? (
                <Pause size={18} fill="currentColor" />
              ) : (
                <Play size={18} fill="currentColor" className="ml-0.5" />
              )}
            </button>
            <p className="flex-1 text-xs text-ink-soft font-body">
              Optional: listen to the whole range once, then record yourself reciting it — the AI
              corrects it when you stop.
            </p>
          </div>

          {t.submitError && <p className="text-xs text-maroon font-body">{t.submitError}</p>}

          <div className="flex justify-center">
            <RecordButton status={t.recorder.status} onStart={t.startRecording} onStop={t.stopRecording} />
          </div>
        </>
      )}

      {t.phase === 'analyzing' && (
        <div className="flex flex-col items-center gap-2 py-10">
          <div className="h-8 w-8 rounded-full border-2 border-teal border-t-transparent animate-spin" />
          <p className="font-body text-sm text-ink-soft">
            Transcribing your recitation and comparing it to the real ayah text…
          </p>
        </div>
      )}

      {t.phase === 'complete' && t.session && t.session.analysisStatus === 'completed' && (
        <>
          <TestSessionSummary session={t.session} />
          <button
            onClick={() => onFinish(t.session!)}
            className="rounded-full bg-teal text-paper font-semibold text-sm py-3 hover:bg-teal-dark transition-colors"
          >
            Done
          </button>
        </>
      )}

      {t.phase === 'complete' && t.session && t.session.analysisStatus !== 'completed' && (
        <div className="flex flex-col items-center gap-3 py-6">
          <p className="font-body text-sm text-maroon text-center">
            {t.session.analysisStatus === 'pending'
              ? "Saved offline — this will be analyzed once you're back online."
              : (t.session.analysisError ?? 'Analysis failed.')}
          </p>
          <div className="flex items-center gap-3">
            {t.session.analysisStatus === 'failed' && (
              <button
                onClick={t.retryAnalysis}
                className="flex items-center gap-1.5 rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark transition-colors"
              >
                <RotateCcw size={13} /> Retry analysis
              </button>
            )}
            <button
              onClick={() => onFinish(t.session!)}
              className="rounded-full bg-sage text-ink-soft font-semibold text-xs px-4 py-2 hover:bg-[#d8dfcd] transition-colors"
            >
              Done for now
            </button>
          </div>
        </div>
      )}
    </Card>
  );
}
