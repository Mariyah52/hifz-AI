import type { TeacherFeedback } from '@/types/teacher';

interface FeedbackItemProps {
  feedback: TeacherFeedback;
}

export function FeedbackItem({ feedback }: FeedbackItemProps) {
  const date = new Date(feedback.createdAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

  return (
    <div className="rounded-2xl bg-paper-dim px-4 py-3">
      <p className="font-body text-sm text-ink">{feedback.note}</p>
      <p className="font-mono text-[11px] text-ink-soft mt-1">{date}</p>
    </div>
  );
}
