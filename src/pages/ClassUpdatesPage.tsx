import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Megaphone, BookMarked } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';
import { homeRouteForRole } from '@/routes/roleHome';
import { getAnnouncements, getHomework } from '@/services/communicationService';
import type { Announcement, Homework } from '@/types/communication';

export function ClassUpdatesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [announcements, setAnnouncements] = useState<Announcement[] | null>(null);
  const [homework, setHomework] = useState<Homework[] | null>(null);

  useEffect(() => {
    getAnnouncements().then(setAnnouncements);
    getHomework().then(setHomework);
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
          <h1 className="heading-section">Class updates</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        <section>
          <h3 className="heading-subsection mb-2 flex items-center gap-1.5">
            <BookMarked size={16} />
            Homework
          </h3>
          {homework === null && <p className="text-ink-soft font-body text-sm">Loading…</p>}
          {homework?.length === 0 && (
            <Card>
              <p className="font-body text-sm text-ink-soft">No homework right now.</p>
            </Card>
          )}
          <div className="flex flex-col gap-2">
            {homework?.map((h) => (
              <Card key={h.id}>
                <div className="flex items-center justify-between">
                  <p className="font-body font-semibold text-ink text-sm">{h.title}</p>
                  <span className="font-mono text-[11px] text-ink-soft">
                    Due {new Date(h.dueDate).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                  </span>
                </div>
                <p className="font-body text-xs text-ink-soft mt-1">{h.description}</p>
                <p className="font-mono text-[10px] text-ink-soft mt-1">{h.className}</p>
              </Card>
            ))}
          </div>
        </section>

        <section>
          <h3 className="heading-subsection mb-2 flex items-center gap-1.5">
            <Megaphone size={16} />
            Announcements
          </h3>
          {announcements === null && <p className="text-ink-soft font-body text-sm">Loading…</p>}
          {announcements?.length === 0 && (
            <Card>
              <p className="font-body text-sm text-ink-soft">No announcements right now.</p>
            </Card>
          )}
          <div className="flex flex-col gap-2">
            {announcements?.map((a) => (
              <Card key={a.id}>
                <div className="flex items-center justify-between">
                  <p className="font-body font-semibold text-ink text-sm">{a.title}</p>
                  <span className="font-mono text-[10px] text-ink-soft">{a.className ?? 'Institution-wide'}</span>
                </div>
                <p className="font-body text-xs text-ink-soft mt-1">{a.content}</p>
                <p className="font-mono text-[10px] text-ink-soft mt-1">— {a.authorName}</p>
              </Card>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
