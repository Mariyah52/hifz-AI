import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronLeft, Radio, PhoneOff, Check, AlertTriangle, X } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useLiveSession } from '@/hooks/useLiveSession';
import { useAuth } from '@/hooks/useAuth';
import { getMyClassActiveSession } from '@/services/liveSessionService';
import type { LiveSession, MarkType } from '@/types/liveSession';

const MARK_LABELS: Record<MarkType, { label: string; icon: typeof Check; tone: string }> = {
  perfect: { label: 'Perfect', icon: Check, tone: 'text-teal-dark' },
  hesitation: { label: 'Hesitation', icon: AlertTriangle, tone: 'text-[#8a6218]' },
  mistake: { label: 'Mistake', icon: X, tone: 'text-maroon' },
};

export function LiveSessionJoinPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [available, setAvailable] = useState<LiveSession | null>(null);
  const [hasJoined, setHasJoined] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    getMyClassActiveSession()
      .then(setAvailable)
      .finally(() => setIsLoading(false));
  }, []);

  const live = useLiveSession(hasJoined && available ? available.id : '', 'student');
  const teacherPeer = live.peers.find((p) => p.role === 'teacher');
  const myMarks = live.mistakeEvents.filter((m) => user && m.studentPeerId === user.id);

  function handleLeave() {
    setHasJoined(false);
    navigate('/');
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
          <p className="text-sm text-ink-soft font-body">Live class</p>
          <h1 className="heading-section">
            {available ? available.className : 'No live class'}
          </h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        {isLoading && <p className="text-center text-ink-soft font-body text-sm py-8">Loading…</p>}

        {!isLoading && !available && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">
              Your class doesn't have a live session running right now.
            </p>
          </Card>
        )}

        {!isLoading && available && !hasJoined && (
          <Card className="flex flex-col gap-3">
            <p className="font-body text-sm text-ink">
              {available.teacherName} started a live session for {available.className}.
            </p>
            <p className="font-body text-xs text-ink-soft">
              Audio only — your microphone will be used so your teacher can listen live.
            </p>
            <button
              onClick={() => setHasJoined(true)}
              className="flex items-center justify-center gap-2 rounded-full bg-teal text-paper font-semibold text-sm py-3 hover:bg-teal-dark transition-colors"
            >
              <Radio size={16} />
              Join now
            </button>
          </Card>
        )}

        {hasJoined && available && (
          <>
            <Card className="flex items-center justify-between">
              <div>
                <p className="font-body font-semibold text-ink text-sm">
                  {teacherPeer ? `Connected to ${teacherPeer.name}` : 'Connecting…'}
                </p>
                {teacherPeer && (
                  <p className="font-mono text-[11px] text-ink-soft mt-0.5">{teacherPeer.connectionState}</p>
                )}
              </div>
              <button
                onClick={handleLeave}
                aria-label="Leave session"
                className="grid h-10 w-10 place-items-center rounded-full bg-maroon/10 text-maroon hover:bg-maroon/20 transition-colors"
              >
                <PhoneOff size={16} />
              </button>
            </Card>

            {live.micError && (
              <Card>
                <p className="font-body text-sm text-maroon">{live.micError}</p>
              </Card>
            )}
            {live.connectionError && (
              <Card>
                <p className="font-body text-sm text-maroon">{live.connectionError}</p>
              </Card>
            )}

            {myMarks.length > 0 && (
              <section>
                <h3 className="heading-subsection mb-2">From your teacher</h3>
                <div className="flex flex-col gap-2">
                  {myMarks
                    .slice()
                    .reverse()
                    .map((mark, i) => {
                      const { label, icon: Icon, tone } = MARK_LABELS[mark.markType];
                      return (
                        <Card key={i} className="flex items-center gap-2">
                          <Icon size={16} className={tone} />
                          <span className={`font-body text-sm font-semibold ${tone}`}>{label}</span>
                        </Card>
                      );
                    })}
                </div>
              </section>
            )}
          </>
        )}
      </main>
    </>
  );
}
