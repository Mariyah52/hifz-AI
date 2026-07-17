import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronLeft, Mic, Square } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useSurah } from '@/hooks/useQuranData';
import { useLiveCoachSession } from '@/hooks/useLiveCoachSession';

export function LiveCoachSurahPage() {
  const params = useParams<{ surahNumber: string }>();
  const surahNumber = Number(params.surahNumber);
  const surah = useSurah(surahNumber);

  const [fromAyah, setFromAyah] = useState(1);
  const [toAyah, setToAyah] = useState(1);

  useEffect(() => {
    if (surah) {
      setFromAyah(1);
      setToAyah(surah.ayahCount);
    }
  }, [surah]);

  const session = useLiveCoachSession();

  if (!surah) {
    return (
      <div className="p-5 text-ink-soft font-body text-sm">
        {Number.isNaN(surahNumber) ? 'Unknown surah.' : 'Loading surah…'}
      </div>
    );
  }

  const isReciting = session.status === 'reciting' || session.status === 'connecting';
  const progressPct =
    session.totalReferenceWordCount > 0
      ? Math.min(
          100,
          Math.round(
            (session.matchedWordCount / session.totalReferenceWordCount) * 100,
          ),
        )
      : 0;

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/live-coach"
          aria-label="Back to surah list"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Live Coach</p>
          <h1 className="heading-section">
            {surah.name}
          </h1>
        </div>
      </header>

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
        <Card>
          <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-2">
            Range
          </p>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
              From
              <input
                type="number"
                min={1}
                max={surah.ayahCount}
                value={fromAyah}
                disabled={isReciting}
                onChange={(e) => setFromAyah(Number(e.target.value))}
                className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink disabled:opacity-60"
              />
            </label>
            <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
              To
              <input
                type="number"
                min={fromAyah}
                max={surah.ayahCount}
                value={toAyah}
                disabled={isReciting}
                onChange={(e) => setToAyah(Number(e.target.value))}
                className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink disabled:opacity-60"
              />
            </label>
          </div>
        </Card>

        <Card className="flex flex-col items-center gap-4 py-6">
          {session.status === 'idle' ||
          session.status === 'stopped' ||
          session.status === 'error' ? (
            <button
              onClick={() => session.start(surah.number, fromAyah, toAyah)}
              className="grid h-16 w-16 place-items-center rounded-full bg-teal text-paper hover:bg-teal-dark transition-colors"
              aria-label="Start reciting"
            >
              <Mic size={24} />
            </button>
          ) : (
            <button
              onClick={session.stop}
              className="grid h-16 w-16 place-items-center rounded-full bg-maroon text-paper hover:opacity-90 transition-colors"
              aria-label="Stop reciting"
            >
              <Square size={20} fill="currentColor" />
            </button>
          )}

          <p className="font-body text-sm text-ink-soft text-center">
            {session.status === 'idle' && 'Tap to start reciting.'}
            {session.status === 'connecting' && 'Connecting…'}
            {session.status === 'reciting' && 'Listening…'}
            {session.status === 'stopped' && 'Session ended.'}
            {session.status === 'error' &&
              (session.error ?? 'Something went wrong.')}
          </p>

          {session.totalReferenceWordCount > 0 && (
            <div className="w-full">
              <div className="flex justify-between text-xs font-mono text-ink-soft mb-1">
                <span>
                  {session.matchedWordCount} / {session.totalReferenceWordCount} words
                </span>
                <span>{progressPct}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-sage/60 overflow-hidden">
                <div
                  className="h-full bg-teal transition-all"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
          )}
        </Card>

        {session.mistakes.length > 0 && (
          <section>
            <h3 className="heading-subsection mb-3">
              Mistakes ({session.mistakes.length})
            </h3>
            <div className="flex flex-col gap-2">
              {session.mistakes.map((mistake, i) => (
                <Card key={i} className="py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-arabic text-base text-ink" dir="rtl">
                        {mistake.referenceWord}
                      </p>
                      <p className="font-body text-xs text-ink-soft mt-0.5">
                        Ayah {mistake.ayahNumber} · heard &quot;{mistake.transcribedWord}&quot;
                      </p>
                    </div>
                    <span className="text-[10px] font-mono uppercase tracking-wide text-maroon bg-maroon/10 px-2 py-1 rounded-full whitespace-nowrap">
                      {mistake.mistakeType}
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          </section>
        )}
      </main>
    </>
  );
}
