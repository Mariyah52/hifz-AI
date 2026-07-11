import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Radio, Check, AlertTriangle, X, Users } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useLiveSession } from '@/hooks/useLiveSession';
import { getMyClasses, startLiveSession, endLiveSession, getMyActiveTeacherSession, type TeacherClass } from '@/services/liveSessionService';
import type { LiveSession, LiveSessionReport, MarkType } from '@/types/liveSession';

const MARK_BUTTONS: { type: MarkType; label: string; icon: typeof Check; tone: string }[] = [
  { type: 'perfect', label: 'Perfect', icon: Check, tone: 'bg-teal/10 text-teal-dark hover:bg-teal/20' },
  { type: 'hesitation', label: 'Hesitation', icon: AlertTriangle, tone: 'bg-gold/10 text-[#8a6218] hover:bg-gold/20' },
  { type: 'mistake', label: 'Mistake', icon: X, tone: 'bg-maroon/10 text-maroon hover:bg-maroon/20' },
];

export function LiveSessionHostPage() {
  const [classes, setClasses] = useState<TeacherClass[]>([]);
  const [session, setSession] = useState<LiveSession | null>(null);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<LiveSessionReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([getMyClasses(), getMyActiveTeacherSession()])
      .then(([classList, active]) => {
        setClasses(classList);
        if (classList[0]) setSelectedClassId(classList[0].id);
        if (active) setSession(active);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const live = useLiveSession(session?.id ?? '', 'teacher');

  async function handleStart() {
    setError(null);
    try {
      const started = await startLiveSession(selectedClassId);
      setSession(started);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start the session.');
    }
  }

  async function handleEnd() {
    if (!session) return;
    const finalReport = await endLiveSession(session.id);
    setReport(finalReport);
    setSession(null);
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/teacher"
          aria-label="Back to Teacher Portal"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Teacher Portal</p>
          <h1 className="font-display text-xl font-semibold text-ink">Live class</h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        {isLoading && <p className="text-center text-ink-soft font-body text-sm py-8">Loading…</p>}

        {!isLoading && !session && !report && (
          <Card className="flex flex-col gap-3">
            <p className="font-body text-sm text-ink-soft">
              Audio only, peer-to-peer between browsers — no video, no recording. Works best on
              home/mobile networks; a student on a very restrictive network may not be able to
              connect (this app doesn't run a relay/TURN server).
            </p>
            {classes.length === 0 ? (
              <p className="font-body text-sm text-ink-soft">You don't have any classes yet.</p>
            ) : (
              <>
                <select
                  value={selectedClassId}
                  onChange={(e) => setSelectedClassId(e.target.value)}
                  className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
                >
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleStart}
                  className="flex items-center justify-center gap-2 rounded-full bg-teal text-paper font-semibold text-sm py-3 hover:bg-teal-dark transition-colors"
                >
                  <Radio size={16} />
                  Start live session
                </button>
              </>
            )}
            {error && <p className="text-xs text-maroon font-body">{error}</p>}
          </Card>
        )}

        {session && (
          <>
            <Card className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-maroon opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-maroon" />
                </span>
                <p className="font-body font-semibold text-ink text-sm">Live now</p>
              </div>
              <button
                onClick={handleEnd}
                className="rounded-full bg-maroon/10 text-maroon font-semibold text-xs px-4 py-2 hover:bg-maroon/20 transition-colors"
              >
                End session
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

            <section>
              <h3 className="font-display text-base font-semibold text-ink mb-2 flex items-center gap-1.5">
                <Users size={16} />
                {live.peers.length} joined
              </h3>
              <div className="flex flex-col gap-2">
                {live.peers.map((peer) => (
                  <Card key={peer.peerId} className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <p className="font-body font-semibold text-ink text-sm">{peer.name}</p>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                          peer.connectionState === 'connected'
                            ? 'bg-teal/10 text-teal-dark'
                            : 'bg-sage text-ink-soft'
                        }`}
                      >
                        {peer.connectionState}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      {MARK_BUTTONS.map(({ type, label, icon: Icon, tone }) => (
                        <button
                          key={type}
                          onClick={() => live.markMistake(peer.peerId, type)}
                          className={`flex-1 flex items-center justify-center gap-1 rounded-full text-xs font-semibold py-2 transition-colors ${tone}`}
                        >
                          <Icon size={13} />
                          {label}
                        </button>
                      ))}
                    </div>
                  </Card>
                ))}
                {live.peers.length === 0 && (
                  <Card>
                    <p className="font-body text-sm text-ink-soft">Waiting for students to join…</p>
                  </Card>
                )}
              </div>
            </section>
          </>
        )}

        {report && (
          <Card className="flex flex-col gap-3">
            <p className="font-body font-semibold text-ink text-sm">Session ended</p>
            <div>
              <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-1">Attendance</p>
              {report.participants.length === 0 && (
                <p className="font-body text-sm text-ink-soft">No one joined this session.</p>
              )}
              {report.participants.map((p) => (
                <div key={p.studentId} className="flex items-center justify-between text-sm font-body py-1">
                  <span className="text-ink">{p.studentName}</span>
                  <span className="text-ink-soft font-mono text-xs">
                    {p.durationSeconds != null ? `${Math.round(p.durationSeconds / 60)} min` : '—'}
                  </span>
                </div>
              ))}
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-1">Marks</p>
              {report.mistakes.length === 0 && (
                <p className="font-body text-sm text-ink-soft">No marks recorded.</p>
              )}
              {report.mistakes.map((m, i) => (
                <div key={i} className="flex items-center justify-between text-sm font-body py-1">
                  <span className="text-ink">{m.studentName}</span>
                  <span className="text-ink-soft text-xs">{m.markType}</span>
                </div>
              ))}
            </div>
          </Card>
        )}
      </main>
    </>
  );
}
