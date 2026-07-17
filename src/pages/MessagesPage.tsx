import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronLeft, MessageCircle } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';
import { homeRouteForRole } from '@/routes/roleHome';
import { getConversations } from '@/services/communicationService';
import type { ConversationSummary } from '@/types/communication';

export function MessagesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<ConversationSummary[] | null>(null);

  useEffect(() => {
    getConversations().then(setConversations);
  }, []);

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
          <p className="text-sm text-ink-soft font-body">Communication</p>
          <h1 className="heading-section">Messages</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-2">
        {conversations === null && <p className="text-center text-ink-soft font-body text-sm py-8">Loading…</p>}

        {conversations?.length === 0 && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">
              No conversations yet. Start one from a teacher's or student's profile.
            </p>
          </Card>
        )}

        {conversations?.map((c) => (
          <Link
            key={c.id}
            to={`/messages/${c.id}`}
            className="flex items-center gap-3 rounded-2xl bg-paper-dim px-4 py-3 hover:bg-sage/60 transition-colors"
          >
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-teal/15 text-teal-dark">
              <MessageCircle size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="font-body font-semibold text-ink text-sm truncate">{c.otherUserName}</p>
                {c.unreadCount > 0 && (
                  <span className="rounded-full bg-maroon text-paper text-[10px] font-mono font-bold h-4 w-4 grid place-items-center shrink-0">
                    {c.unreadCount > 9 ? '9+' : c.unreadCount}
                  </span>
                )}
              </div>
              <p className="font-body text-xs text-ink-soft truncate">{c.lastMessagePreview ?? 'No messages yet'}</p>
            </div>
          </Link>
        ))}
      </main>
    </>
  );
}
