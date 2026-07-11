import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Send, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useAssistant } from '@/hooks/useAssistant';
import { useAuth } from '@/hooks/useAuth';
import { homeRouteForRole } from '@/routes/roleHome';
import type { ChatMessage } from '@/types/assistant';

const TOOL_LABELS: Record<string, string> = {
  get_weak_spots: 'your weak spots',
  get_due_reviews: 'your due reviews',
  get_progress_summary: 'your progress',
};

function Bubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm font-body whitespace-pre-line ${
          isUser ? 'bg-teal text-paper' : 'bg-paper-dim text-ink'
        }`}
      >
        {message.content}
      </div>
      {message.toolsCalled.length > 0 && (
        <p className="text-[10px] text-ink-soft font-mono mt-1 px-1">
          checked {message.toolsCalled.map((t) => TOOL_LABELS[t] ?? t).join(', ')}
        </p>
      )}
    </div>
  );
}

export function AssistantPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { messages, isLoading, pendingUserMessage, isSending, error, send } = useAssistant();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingUserMessage]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isSending) return;
    setInput('');
    await send(text);
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <button
          aria-label="Back"
          onClick={() => navigate(user ? homeRouteForRole(user.role) : '/')}
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </button>
        <div>
          <p className="text-sm text-ink-soft font-body">Your tutor</p>
          <h1 className="font-display text-xl font-semibold text-ink flex items-center gap-1.5">
            <Sparkles size={16} className="text-teal-dark" />
            HifzAI Assistant
          </h1>
        </div>
      </header>

      <main className="px-5 flex flex-col gap-3 pb-4">
        {isLoading && <p className="text-center text-ink-soft font-body text-sm py-8">Loading…</p>}

        {!isLoading && messages.length === 0 && (
          <Card className="text-center py-6">
            <p className="font-body text-sm text-ink-soft">
              Ask about your weak spots, what to revise today, or a tajweed rule you want
              explained. Answers about your own progress are checked against your real data, not
              guessed.
            </p>
          </Card>
        )}

        {messages.map((m) => (
          <Bubble key={m.id} message={m} />
        ))}

        {pendingUserMessage && (
          <Bubble
            message={{ id: 'pending', role: 'user', content: pendingUserMessage, toolsCalled: [], createdAt: '' }}
          />
        )}
        {isSending && <p className="text-xs text-ink-soft font-body px-1">Thinking…</p>}
        {error && <p className="text-xs text-maroon font-body px-1">{error}</p>}

        <div ref={scrollRef} />

        <form onSubmit={handleSubmit} className="flex items-center gap-2 sticky bottom-2 pt-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your tutor anything…"
            className="flex-1 rounded-full border border-ink/10 bg-paper px-4 py-2.5 font-body text-sm text-ink shadow-folio"
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            aria-label="Send"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-teal text-paper hover:bg-teal-dark transition-colors disabled:opacity-50 shadow-folio"
          >
            <Send size={16} />
          </button>
        </form>
      </main>
    </>
  );
}
