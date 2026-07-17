import { Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { StatTile } from '@/components/progress/StatTile';
import { useAdvancedAnalytics } from '@/hooks/useAdvancedAnalytics';

export function AdvancedAnalyticsPage() {
  const { data, isLoading } = useAdvancedAnalytics();

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/progress"
          aria-label="Back to Progress"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Analytics</p>
          <h1 className="heading-section">Deeper insights</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        {isLoading && <div className="text-ink-soft font-body text-sm text-center py-8">Loading…</div>}

        {data && (
          <>
            <Card className="py-4 text-center">
              <p className="font-body text-xs text-ink-soft">
                Every number here comes from your real recorded Test Mode results and review
                history — nothing is estimated.
              </p>
            </Card>

            <div className="grid grid-cols-2 gap-3">
              <StatTile label="Overall accuracy" value={`${data.overallAccuracy}%`} />
              <StatTile label="Longest streak" value={`${data.longestStreak}d`} />
              <StatTile
                label="Retention rate"
                value={data.retentionRate != null ? `${data.retentionRate}%` : '—'}
              />
              <StatTile
                label="Confidence score"
                value={data.confidenceScore != null ? `${data.confidenceScore}%` : '—'}
              />
              <StatTile
                label="Avg. revision time"
                value={
                  data.averageRevisionTimeSeconds != null
                    ? `${Math.round(data.averageRevisionTimeSeconds)}s`
                    : '—'
                }
              />
            </div>

            <section>
              <h3 className="heading-subsection mb-2">Where to focus</h3>
              <div className="flex flex-col gap-2">
                {data.weakestSurah && (
                  <div className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono">
                        Weakest surah
                      </p>
                      <p className="font-body font-semibold text-ink text-sm mt-0.5">
                        {data.weakestSurah.surahName}
                      </p>
                    </div>
                    <span className="font-mono text-sm font-semibold text-maroon">
                      {data.weakestSurah.accuracy}%
                    </span>
                  </div>
                )}

                {data.weakestJuz && (
                  <div className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono">
                        Weakest juz
                      </p>
                      <p className="font-body font-semibold text-ink text-sm mt-0.5">
                        Juz {data.weakestJuz.juz}
                      </p>
                    </div>
                    <span className="font-mono text-sm font-semibold text-maroon">
                      {data.weakestJuz.accuracy}%
                    </span>
                  </div>
                )}

                {data.weakestPages.length > 0 && (
                  <div className="rounded-2xl bg-paper-dim px-4 py-3">
                    <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-1">
                      Weakest pages
                    </p>
                    <div className="flex gap-2 flex-wrap">
                      {data.weakestPages.map((p) => (
                        <span
                          key={p.page}
                          className="rounded-full bg-maroon/10 text-maroon text-xs font-mono font-semibold px-2.5 py-1"
                        >
                          {p.page} · {p.accuracy}%
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {data.mostForgottenAyah && (
                  <div className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono">
                        Most forgotten ayah
                      </p>
                      <p className="font-body font-semibold text-ink text-sm mt-0.5">
                        {data.mostForgottenAyah.surahName} {data.mostForgottenAyah.surahNumber}:
                        {data.mostForgottenAyah.ayahNumber}
                      </p>
                      <p className="font-mono text-[11px] text-ink-soft mt-0.5">
                        Missed {data.mostForgottenAyah.missedCount} of {data.mostForgottenAyah.attemptCount} times
                      </p>
                    </div>
                    <span className="font-mono text-sm font-semibold text-maroon">
                      {data.mostForgottenAyah.accuracy}%
                    </span>
                  </div>
                )}

                {!data.weakestSurah && !data.weakestJuz && data.weakestPages.length === 0 && !data.mostForgottenAyah && (
                  <Card>
                    <p className="font-body text-sm text-ink-soft">
                      Not enough Test Mode history yet to identify weak spots — each ayah needs at
                      least 2 recorded attempts before it shows up here.
                    </p>
                  </Card>
                )}
              </div>
            </section>
          </>
        )}
      </main>
    </>
  );
}
