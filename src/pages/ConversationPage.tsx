import { useEffect, useRef, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronLeft, Send, Paperclip, FileText } from 'lucide-react';
import { getConversationMessages, sendConversationMessage } from '@/services/communicationService';
import { resolveMediaUrl } from '@/services/apiClient';
import type { DirectMessage } from '@/types/communication';
import { useAuth } from '@/hooks/useAuth';

export function ConversationPage() {
  const params = useParams<{ conversationId: string }>();
  const conversationId = params.conversationId ?? '';
  const { user } = useAuth();
  const [messages, setMessages] = useState<DirectMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  function refresh() {
    getConversationMessages(conversationId).then(setMessages);
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setIsSending(true);
    setInput('');
    try {
      await sendConversationMessage(conversationId, text);
      refresh();
    } finally {
      setIsSending(false);
    }
  }

  async function handleAttach(file: File) {
    setIsSending(true);
    try {
      await sendConversationMessage(conversationId, null, file);
      refresh();
    } finally {
      setIsSending(false);
    }
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/messages"
          aria-label="Back to messages"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <h1 className="font-display text-lg font-semibold text-ink">Conversation</h1>
      </header>

      <main className="px-5 flex flex-col gap-2 pb-4">
        {messages.map((m) => {
          const isMine = m.senderUserId === user?.id;
          return (
            <div key={m.id} className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm font-body ${isMine ? 'bg-teal text-paper' : 'bg-paper-dim text-ink'}`}>
                {m.content && <p className="whitespace-pre-line">{m.content}</p>}
                {m.attachmentUrl && m.attachmentType === 'audio' && (
                  <audio controls src={resolveMediaUrl(m.attachmentUrl)} className="mt-1 max-w-full" />
                )}
                {m.attachmentUrl && m.attachmentType === 'file' && (
                  <a
                    href={resolveMediaUrl(m.attachmentUrl)}
                    target="_blank"
                    rel="noreferrer"
                    className={`flex items-center gap-1.5 mt-1 text-xs underline ${isMine ? 'text-paper' : 'text-teal-dark'}`}
                  >
                    <FileText size={13} />
                    Attachment
                  </a>
                )}
              </div>
            </div>
          );
        })}
        <div ref={scrollRef} />
      </main>

      <form onSubmit={handleSubmit} className="flex items-center gap-2 px-5 py-3 sticky bottom-2">
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*,.pdf,.png,.jpg,.jpeg,.gif,.doc,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleAttach(file);
            e.target.value = '';
          }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          aria-label="Attach file"
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <Paperclip size={16} />
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          className="flex-1 rounded-full border border-ink/10 bg-paper px-4 py-2.5 font-body text-sm text-ink shadow-folio"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          aria-label="Send"
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-teal text-paper hover:bg-teal-dark transition-colors disabled:opacity-50"
        >
          <Send size={16} />
        </button>
      </form>
    </>
  );
}
