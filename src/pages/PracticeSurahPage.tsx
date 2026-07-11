import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronLeft, Pause, Play } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { RecordButton } from '@/components/practice/RecordButton';
import { PlaybackControls } from '@/components/practice/PlaybackControls';
import { AttemptHistoryCard } from '@/components/practice/AttemptHistoryCard';
import { PlaybackSettingsRow } from '@/components/learn/PlaybackSettingsRow';
import { useSurah } from '@/hooks/useQuranData';
import { useRecorder } from '@/hooks/useRecorder';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';
import { estimatePace } from '@/services/scoringService';
import { getAttemptsForSurah, saveAttempt } from '@/services/practiceService';
import type { PracticeAttempt } from '@/types/practice';

export function PracticeSurahPage() {
  const params = useParams<{ surahNumber: string }>();
  const surahNumber = Number(params.surahNumber);
  const surah = useSurah(surahNumber);

  const [fromAyah, setFromAyah] = useState(1);
  const [toAyah, setToAyah] = useState(1);
  const [attempts, setAttempts] = useState<PracticeAttempt[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (surah) {
      setFromAyah(1);
      setToAyah(surah.ayahCount);
      getAttemptsForSurah(surah.number).then(setAttempts).catch(() => setAttempts([]));
    }
  }, [surah]);

  const referencePlayer = useAudioPlayer({
    surahNumber,
    ayahNumbers: surah ? Array.from({ length: surah.ayahCount }, (_, i) => i + 1) : [1],
    rangeStart: fromAyah,
    rangeEnd: toAyah,
  });

  useEffect(() => {
    referencePlayer.setRepeatMode('range');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const recorder = useRecorder();

  if (!surah) {
    return (
      <div className="p-5 text-ink-soft font-body text-sm">
        {Number.isNaN(surahNumber) ? 'Unknown surah.' : 'Loading surah…'}
      </div>
    );
  }

  const pace = recorder.audioUrl
    ? estimatePace(toAyah - fromAyah + 1, recorder.durationSeconds)
    : null;

  async function handleSave() {
    if (!recorder.audioUrl || !pace || !surah) return;
    setIsSaving(true);
    try {
      await saveAttempt({
        surahNumber: surah.number,
        surahName: surah.name,
        fromAyah,
        toAyah,
        durationSeconds: recorder.durationSeconds,
        expectedMinSeconds: pace.expectedSecondsRange[0],
        expectedMaxSeconds: pace.expectedSecondsRange[1],
        audioBlob: recorder.audioBlob,
      });
      setAttempts(await getAttemptsForSurah(surah.number));
      recorder.reset();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/practice"
          aria-label="Back to surah list"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Practice Mode</p>
          <h1 className="font-display text-xl font-semibold text-ink">{surah.name}</h1>
        </div>
      </header>

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
        <Card>
          <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-2">Range</p>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
              From
              <input
                type="number"
                min={1}
                max={surah.ayahCount}
                value={fromAyah}
                onChange={(e) => setFromAyah(Number(e.target.value))}
                className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink"
              />
            </label>
            <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
              To
              <input
                type="number"
                min={fromAyah}
                max={surah.ayahCount}
                value={toAyah}
                onChange={(e) => setToAyah(Number(e.target.value))}
                className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink"
              />
            </label>
          </div>
        </Card>

        <Card className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono">Reference</p>
            <p className="font-body text-sm text-ink mt-0.5">Al-Husary · ayah {referencePlayer.currentAyah}</p>
          </div>
          <button
            aria-label={referencePlayer.isPlaying ? 'Pause reference audio' : 'Play reference audio'}
            onClick={referencePlayer.toggle}
            className="grid h-11 w-11 place-items-center rounded-full bg-teal/10 text-teal-dark hover:bg-teal/20 transition-colors"
          >
            {referencePlayer.isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-0.5" />}
          </button>
        </Card>

        <Card>
          <PlaybackSettingsRow
            playbackRate={referencePlayer.playbackRate}
            onPlaybackRateChange={referencePlayer.setPlaybackRate}
            repeatGapSeconds={referencePlayer.repeatGapSeconds}
            onRepeatGapSecondsChange={referencePlayer.setRepeatGapSeconds}
          />
        </Card>

        <Card className="flex flex-col items-center gap-4 py-6">
          {!recorder.audioUrl && (
            <RecordButton status={recorder.status} onStart={recorder.start} onStop={recorder.stop} />
          )}

          {recorder.error && (
            <p className="text-xs text-maroon font-body text-center">{recorder.error}</p>
          )}

          {recorder.audioUrl && pace && (
            <div className="w-full flex flex-col gap-3">
              <PlaybackControls
                audioUrl={recorder.audioUrl}
                durationSeconds={recorder.durationSeconds}
                pace={pace}
                onReRecord={recorder.reset}
              />
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="rounded-full bg-teal text-paper font-semibold text-sm py-3 hover:bg-teal-dark transition-colors disabled:opacity-60"
              >
                {isSaving ? 'Saving…' : 'Save attempt'}
              </button>
            </div>
          )}
        </Card>

        {attempts.length > 0 && (
          <section>
            <h3 className="font-display text-base font-semibold text-ink mb-3">Previous attempts</h3>
            <div className="flex flex-col gap-2">
              {attempts.map((attempt) => (
                <AttemptHistoryCard key={attempt.id} attempt={attempt} />
              ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
