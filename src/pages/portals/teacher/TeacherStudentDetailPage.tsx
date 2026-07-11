import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, MessageCircle } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { AssignSabaqForm } from '@/components/teacher/AssignSabaqForm';
import { FeedbackForm } from '@/components/teacher/FeedbackForm';
import { FeedbackItem } from '@/components/teacher/FeedbackItem';
import { AttemptHistoryCard } from '@/components/practice/AttemptHistoryCard';
import { TestHistoryCard } from '@/components/test/TestHistoryCard';
import { IssueCertificateForm } from '@/components/teacher/IssueCertificateForm';
import { useStudentDetail } from '@/hooks/useStudentDetail';
import { assignSabaq, addFeedback } from '@/services/teacherService';
import { startConversation } from '@/services/communicationService';

export function TeacherStudentDetailPage() {
  const params = useParams<{ studentId: string }>();
  const studentId = params.studentId ?? '';
  const { detail, isLoading, refresh } = useStudentDetail(studentId);
  const navigate = useNavigate();
  const [messageError, setMessageError] = useState<string | null>(null);

  if (isLoading) {
    return <div className="p-5 text-ink-soft font-body text-sm">Loading…</div>;
  }

  if (!detail) {
    return <div className="p-5 text-ink-soft font-body text-sm">Student not found.</div>;
  }

  async function handleAssign(surahNumber: number, surahName: string, fromAyah: number, toAyah: number) {
    await assignSabaq(studentId, surahNumber, surahName, fromAyah, toAyah);
    refresh();
  }

  async function handleFeedback(note: string) {
    await addFeedback(studentId, note);
    refresh();
  }

  async function handleMessage() {
    // Bugfix: `studentId` here is the *student profile* id (route param),
    // but /me/conversations expects a real user id — those are different
    // primary keys, so this used to silently 404 every time the button
    // was clicked. `detail.userId` is the actual account id.
    if (!detail) return;
    setMessageError(null);
    try {
      const conversation = await startConversation(detail.userId);
      navigate(`/messages/${conversation.id}`);
    } catch {
      setMessageError("Couldn't start the conversation. Please try again.");
    }
  }

  return (
    <>
      <header className="flex items-center justify-between gap-3 px-5 pt-6 pb-2">
        <div className="flex items-center gap-3">
          <Link
            to="/teacher"
            aria-label="Back to roster"
            className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
          >
            <ChevronLeft size={18} />
          </Link>
          <div>
            <p className="text-sm text-ink-soft font-body">Teacher Portal</p>
            <h1 className="font-display text-xl font-semibold text-ink">{detail.name}</h1>
          </div>
        </div>
        <button
          onClick={handleMessage}
          aria-label="Message student"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <MessageCircle size={16} />
        </button>
      </header>

      {messageError && <p className="px-5 text-xs text-maroon font-body -mt-1 mb-2">{messageError}</p>}

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
        <Card>
          <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-2">Today's Sabaq</p>
          {detail.todaysSabaq ? (
            <div className="flex items-center justify-between">
              <p className="font-body font-semibold text-ink text-sm">
                {detail.todaysSabaq.surahName} {detail.todaysSabaq.fromAyah}–{detail.todaysSabaq.toAyah}
              </p>
              <Badge tone={detail.todaysSabaq.status === 'completed' ? 'teal' : 'gold'}>
                {detail.todaysSabaq.status.replace('_', ' ')}
              </Badge>
            </div>
          ) : (
            <p className="font-body text-sm text-ink-soft">No Sabaq assigned yet.</p>
          )}
        </Card>

        <section>
          <h3 className="font-display text-base font-semibold text-ink mb-3">Assign new Sabaq</h3>
          <Card>
            <AssignSabaqForm onAssign={handleAssign} />
          </Card>
        </section>

        {detail.recentTestSessions.length > 0 && (
          <section>
            <h3 className="font-display text-base font-semibold text-ink mb-3">Recent test sessions</h3>
            <div className="flex flex-col gap-2">
              {detail.recentTestSessions.map((s) => (
                <TestHistoryCard key={s.id} session={s} />
              ))}
            </div>
          </section>
        )}

        {detail.recentPracticeAttempts.length > 0 && (
          <section>
            <h3 className="font-display text-base font-semibold text-ink mb-3">Recent practice attempts</h3>
            <div className="flex flex-col gap-2">
              {detail.recentPracticeAttempts.map((a) => (
                <AttemptHistoryCard key={a.id} attempt={a} />
              ))}
            </div>
          </section>
        )}

        <section>
          <h3 className="font-display text-base font-semibold text-ink mb-3">Certificates</h3>
          <IssueCertificateForm studentId={studentId} onIssued={refresh} />
        </section>

        <section>
          <h3 className="font-display text-base font-semibold text-ink mb-3">Feedback</h3>
          <Card className="mb-3">
            <FeedbackForm onSubmit={handleFeedback} />
          </Card>
          <div className="flex flex-col gap-2">
            {detail.feedback.map((f) => (
              <FeedbackItem key={f.id} feedback={f} />
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
