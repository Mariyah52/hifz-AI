import { Link } from 'react-router-dom';
import { Flame } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { Student } from '@/types/teacher';

interface StudentCardProps {
  student: Student;
}

export function StudentCard({ student }: StudentCardProps) {
  return (
    <Link
      to={`/teacher/${student.id}`}
      className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3 hover:bg-sage/60 transition-colors"
    >
      <div>
        <p className="font-body font-semibold text-ink text-sm">{student.name}</p>
        {student.todaysSabaq ? (
          <p className="font-mono text-xs text-ink-soft mt-0.5">
            {student.todaysSabaq.surahName} {student.todaysSabaq.fromAyah}–{student.todaysSabaq.toAyah}
          </p>
        ) : (
          <p className="font-mono text-xs text-ink-soft mt-0.5">No Sabaq assigned</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="flex items-center gap-1 text-xs font-mono text-maroon">
          <Flame size={13} fill={student.currentStreak > 0 ? 'currentColor' : 'none'} />
          {student.currentStreak}
        </span>
        {student.todaysSabaq && (
          <Badge tone={student.todaysSabaq.status === 'completed' ? 'teal' : 'gold'}>
            {student.todaysSabaq.status.replace('_', ' ')}
          </Badge>
        )}
      </div>
    </Link>
  );
}
