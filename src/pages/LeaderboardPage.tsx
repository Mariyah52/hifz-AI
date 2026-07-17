import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Trophy } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useLeaderboard } from '@/hooks/useLeaderboard';
import type { LeaderboardScope } from '@/types/gamification';

export function LeaderboardPage() {
  const [scope, setScope] = useState<LeaderboardScope>('class');
  const { data: entries, isLoading } = useLeaderboard(scope);

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
          <p className="text-sm text-ink-soft font-body">Leaderboard</p>
          <h1 className="heading-section">Ranked by XP</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4">
        <div className="flex gap-1.5 rounded-full bg-sage p-1 mb-4">
          {(['class', 'all'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setScope(s)}
              className={`flex-1 rounded-full px-2.5 py-1.5 text-xs font-semibold font-body transition-colors ${
                scope === s ? 'bg-teal text-paper' : 'text-ink-soft hover:text-ink'
              }`}
            >
              {s === 'class' ? 'My Class' : 'Everyone'}
            </button>
          ))}
        </div>

        {isLoading && <div className="text-ink-soft font-body text-sm text-center py-8">Loading…</div>}

        {!isLoading && entries?.length === 0 && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">No one to rank yet.</p>
          </Card>
        )}

        <div className="flex flex-col gap-2">
          {entries?.map((entry) => (
            <div
              key={entry.studentId}
              className={`flex items-center justify-between rounded-2xl px-4 py-3 ${
                entry.isCurrentStudent ? 'bg-teal/10 border border-teal/30' : 'bg-paper-dim'
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`grid h-8 w-8 place-items-center rounded-full font-mono text-xs font-semibold ${
                    entry.rank <= 3 ? 'bg-gold/20 text-[#8a6218]' : 'bg-ink/[0.06] text-ink-soft'
                  }`}
                >
                  {entry.rank <= 3 ? <Trophy size={14} /> : entry.rank}
                </span>
                <div>
                  <p className="font-body font-semibold text-ink text-sm">
                    {entry.name}
                    {entry.isCurrentStudent && <span className="text-teal-dark"> (you)</span>}
                  </p>
                  <p className="font-mono text-xs text-ink-soft mt-0.5">Level {entry.level}</p>
                </div>
              </div>
              <span className="font-mono text-sm font-semibold text-ink">{entry.xp.toLocaleString()} XP</span>
            </div>
          ))}
        </div>
      </main>
    </>
  );
}
