import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useDueReviews } from '@/hooks/useDueReviews';
import { getJuzForAyah } from '@/services/quranService';

function daysOverdue(dueDateIso: string): number {
  const due = new Date(dueDateIso);
  const today = new Date();
  due.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  return Math.max(0, Math.round((today.getTime() - due.getTime()) / (1000 * 60 * 60 * 24)));
}

export function RevisionPage() {
  const { data: reviews, isLoading } = useDueReviews();

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/"
          aria-label="Back to Dashboard"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Revision</p>
          <h1 className="font-display text-xl font-semibold text-ink">
            {isLoading ? 'Loading…' : `${reviews?.length ?? 0} due`}
          </h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4">
        <Card className="mb-4 py-4 text-center">
          <p className="font-body text-sm text-ink-soft">
            Scheduled by SM-2 from your real Test Mode results — the more consistently you score
            well on a Sabaq, the longer the gap grows before it's due again.
          </p>
        </Card>

        {!isLoading && reviews?.length === 0 && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">
              Nothing due right now. Reviews appear here once a completed Sabaq is tested at least
              once and its next due date arrives.
            </p>
          </Card>
        )}

        <div className="flex flex-col gap-2">
          {reviews?.map(({ sabaq, schedule }) => {
            const overdue = daysOverdue(schedule.dueDate);
            const juz = getJuzForAyah(sabaq.surahNumber, sabaq.fromAyah);
            return (
              <Link
                key={sabaq.id}
                to={`/test/${sabaq.surahNumber}?from=${sabaq.fromAyah}&to=${sabaq.toAyah}`}
                className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3 hover:bg-sage/60 transition-colors"
              >
                <div>
                  <p className="font-body font-semibold text-ink text-sm">{sabaq.surahName}</p>
                  <p className="font-mono text-xs text-ink-soft mt-0.5">
                    Ayah {sabaq.fromAyah}–{sabaq.toAyah} · Juz {juz}
                  </p>
                  <p className="font-mono text-[11px] text-ink-soft mt-0.5">
                    {schedule.repetitionNumber === 0
                      ? 'Not yet reviewed'
                      : `Reviewed ${schedule.repetitionNumber}× · ${schedule.intervalDays}-day interval`}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Badge tone={overdue > 0 ? 'maroon' : 'gold'}>
                    {overdue > 0 ? `${overdue}d overdue` : 'due today'}
                  </Badge>
                  <ChevronRight size={16} className="text-ink-soft" />
                </div>
              </Link>
            );
          })}
        </div>
      </main>
    </>
  );
}
