import { Badge } from '@/components/ui/Badge';
import type { TestSession } from '@/types/test';

interface TestHistoryCardProps {
  session: TestSession;
}

export function TestHistoryCard({ session }: TestHistoryCardProps) {
  const date = new Date(session.completedAt);
  const dateLabel = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

  return (
    <div className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3">
      <div>
        <p className="font-body font-semibold text-ink text-sm">
          Ayah {session.fromAyah}–{session.toAyah}
        </p>
        <p className="font-mono text-xs text-ink-soft mt-0.5">{dateLabel}</p>
      </div>
      <Badge tone={session.scorePercent >= 80 ? 'teal' : session.scorePercent >= 50 ? 'gold' : 'maroon'}>
        {session.scorePercent}%
      </Badge>
    </div>
  );
}
