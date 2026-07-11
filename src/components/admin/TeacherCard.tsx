import type { Teacher } from '@/types/admin';

interface TeacherCardProps {
  teacher: Teacher;
  classCount: number;
}

export function TeacherCard({ teacher, classCount }: TeacherCardProps) {
  return (
    <div className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3">
      <p className="font-body font-semibold text-ink text-sm">{teacher.name}</p>
      <p className="font-mono text-xs text-ink-soft">
        {classCount} {classCount === 1 ? 'class' : 'classes'}
      </p>
    </div>
  );
}
