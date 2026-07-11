import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { TestRunner } from '@/components/test/TestRunner';
import { TestHistoryCard } from '@/components/test/TestHistoryCard';
import { useSurah } from '@/hooks/useQuranData';
import { getTestSessionsForSurah } from '@/services/testService';
import type { TestSession } from '@/types/test';

export function TestSurahPage() {
  const params = useParams<{ surahNumber: string }>();
  const surahNumber = Number(params.surahNumber);
  const surah = useSurah(surahNumber);
  const [searchParams] = useSearchParams();

  const [fromAyah, setFromAyah] = useState(1);
  const [toAyah, setToAyah] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [sessions, setSessions] = useState<TestSession[]>([]);

  useEffect(() => {
    if (surah) {
      // A deep link (e.g. from the Revision page) can pre-fill the range
      // via ?from=&to= — falls back to the whole surah otherwise, same as before.
      const requestedFrom = Number(searchParams.get('from'));
      const requestedTo = Number(searchParams.get('to'));
      const validRange =
        Number.isInteger(requestedFrom) &&
        Number.isInteger(requestedTo) &&
        requestedFrom >= 1 &&
        requestedTo >= requestedFrom &&
        requestedTo <= surah.ayahCount;

      setFromAyah(validRange ? requestedFrom : 1);
      setToAyah(validRange ? requestedTo : surah.ayahCount);
      getTestSessionsForSurah(surah.number).then(setSessions).catch(() => setSessions([]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [surah]);

  if (!surah) {
    return (
      <div className="p-5 text-ink-soft font-body text-sm">
        {Number.isNaN(surahNumber) ? 'Unknown surah.' : 'Loading surah…'}
      </div>
    );
  }

  async function handleFinish(_session: TestSession) {
    // TestRunner already uploaded and saved this session (see
    // useTestSession/submitTestSession) — just refresh the list.
    setSessions(await getTestSessionsForSurah(surah!.number));
    setIsRunning(false);
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/test"
          aria-label="Back to surah list"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Test Mode</p>
          <h1 className="font-display text-xl font-semibold text-ink">{surah.name}</h1>
        </div>
      </header>

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
        {!isRunning && (
          <>
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

            <button
              onClick={() => setIsRunning(true)}
              className="rounded-full bg-teal text-paper font-semibold text-sm py-3 hover:bg-teal-dark transition-colors"
            >
              Start test
            </button>

            {sessions.length > 0 && (
              <section>
                <h3 className="font-display text-base font-semibold text-ink mb-3">Previous tests</h3>
                <div className="flex flex-col gap-2">
                  {sessions.map((s) => (
                    <TestHistoryCard key={s.id} session={s} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}

        {isRunning && (
          <TestRunner
            key={`${fromAyah}-${toAyah}`}
            surahNumber={surah.number}
            surahName={surah.name}
            fromAyah={fromAyah}
            toAyah={toAyah}
            onFinish={handleFinish}
          />
        )}
      </main>
    </>
  );
}
