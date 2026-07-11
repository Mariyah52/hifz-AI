import { useState } from 'react';

interface FeedbackFormProps {
  onSubmit: (note: string) => void;
}

export function FeedbackForm({ onSubmit }: FeedbackFormProps) {
  const [note, setNote] = useState('');

  function handleSubmit() {
    const trimmed = note.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
    setNote('');
  }

  return (
    <div className="flex flex-col gap-2">
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Leave feedback for this student…"
        rows={3}
        className="rounded-xl border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink resize-none"
      />
      <button
        onClick={handleSubmit}
        disabled={!note.trim()}
        className="self-end rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark disabled:opacity-40 transition-colors"
      >
        Send feedback
      </button>
    </div>
  );
}
