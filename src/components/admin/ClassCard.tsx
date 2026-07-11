import { Flame } from 'lucide-react';
import type { ClassSummary } from '@/types/admin';

interface ClassCardProps {
  classSummary: ClassSummary;
}

export function ClassCard({ classSummary }: ClassCardProps) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3">
      <div>
        <p className="font-body font-semibold text-ink text-sm">{classSummary.name}</p>
        <p className="font-mono text-xs text-ink-soft mt-0.5">
          {classSummary.teacherName ?? 'Unassigned'} · {classSummary.studentCount}{' '}
          {classSummary.studentCount === 1 ? 'student' : 'students'}
        </p>
      </div>
      <span className="flex items-center gap-1 text-xs font-mono text-maroon">
        <Flame size={13} fill={classSummary.averageStreak > 0 ? 'currentColor' : 'none'} />
        {classSummary.averageStreak}
      </span>
    </div>
  );
}
