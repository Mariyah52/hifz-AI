import { Badge } from '@/components/ui/Badge';
import type { Sabaq } from '@/types/lesson';

interface SabaqCardProps {
  sabaq: Sabaq;
}

const statusTone = {
  completed: 'teal',
  in_progress: 'gold',
  not_started: 'neutral',
} as const;

export function SabaqCard({ sabaq }: SabaqCardProps) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3">
      <div>
        <p className="font-body font-semibold text-ink text-sm">{sabaq.surahName}</p>
        <p className="font-mono text-xs text-ink-soft mt-0.5">
          Ayah {sabaq.fromAyah}–{sabaq.toAyah}
        </p>
      </div>
      <div className="flex items-center gap-2">
        {typeof sabaq.score === 'number' && (
          <span className="font-mono text-sm font-semibold text-teal-dark">{sabaq.score}%</span>
        )}
        <Badge tone={statusTone[sabaq.status]}>{sabaq.status.replace('_', ' ')}</Badge>
      </div>
    </div>
  );
}
