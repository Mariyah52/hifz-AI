import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Trash2, Clock } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useNotes } from '@/hooks/useNotes';

export function NotesPage() {
  const { notes, isLoading, addNote, removeNote } = useNotes();
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = content.trim();
    if (!text) return;
    setIsSaving(true);
    try {
      await addNote({ content: text });
      setContent('');
    } finally {
      setIsSaving(false);
    }
  }

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
          <p className="text-sm text-ink-soft font-body">Notes</p>
          <h1 className="font-display text-xl font-semibold text-ink">{notes.length} saved</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        <form onSubmit={handleSubmit}>
          <Card className="flex flex-col gap-2">
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Jot something down — a mistake to remember, a reminder for next Sabaq…"
              rows={3}
              className="w-full resize-none rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
            />
            <button
              type="submit"
              disabled={isSaving || !content.trim()}
              className="self-end rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save note'}
            </button>
          </Card>
        </form>

        {isLoading && <p className="text-center text-ink-soft font-body text-sm py-4">Loading…</p>}

        {!isLoading && notes.length === 0 && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">No notes yet.</p>
          </Card>
        )}

        <div className="flex flex-col gap-2">
          {notes.map((note) => (
            <div key={note.id} className="rounded-2xl bg-paper-dim px-4 py-3">
              <p className="font-body text-sm text-ink whitespace-pre-line">{note.content}</p>
              <div className="flex items-center justify-between mt-2">
                <p className="font-mono text-[11px] text-ink-soft flex items-center gap-1">
                  {note.id.startsWith('local_') ? (
                    <>
                      <Clock size={11} />
                      queued — will sync
                    </>
                  ) : (
                    new Date(note.createdAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
                  )}
                </p>
                <button
                  aria-label="Delete note"
                  onClick={() => removeNote(note.id)}
                  className="text-ink-soft hover:text-maroon transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </>
  );
}
