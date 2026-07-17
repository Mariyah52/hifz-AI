import { MessageCircle, Megaphone } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { ProgressRing } from '@/components/ui/ProgressRing';
import { StreakBadge } from '@/components/dashboard/StreakBadge';
import { SabaqCard } from '@/components/dashboard/SabaqCard';
import { StatTile } from '@/components/progress/StatTile';
import { WeeklyActivityChart } from '@/components/progress/WeeklyActivityChart';
import { FeedbackItem } from '@/components/teacher/FeedbackItem';
import { OrganizationBanner } from '@/components/layout/OrganizationBanner';
import { useChildOverview } from '@/hooks/useChildOverview';

export function ParentDashboardPage() {
  const { overview, isLoading } = useChildOverview();


  if (isLoading) {
    return <div className="p-5 text-ink-soft font-body text-sm">Loading…</div>;
  }

  if (!overview) {
    return (
      <>
        <OrganizationBanner roleLabel="Parent" subtitle="No linked child yet" />
        <main className="px-5 mt-2 pb-4">
          <Card>
            <p className="font-body text-sm text-ink-soft">
              This account isn't linked to a student yet. An admin can link one, or you can create a
              new account and provide a child's student ID at sign-up.
            </p>
          </Card>
        </main>
      </>
    );
  }

  const isActiveToday = overview.streak.lastActiveDate === new Date().toISOString().slice(0, 10);

  return (
    <>
      <OrganizationBanner roleLabel="Parent" subtitle={overview.name} />

      <main className="px-5 flex flex-col gap-5 mt-2 pb-4">
        <div className="grid grid-cols-2 gap-2">
          <Link
            to="/messages"
            className="flex flex-col items-center justify-center gap-1 rounded-2xl bg-paper-dim px-3 py-3 hover:bg-sage/60 transition-colors"
          >
            <MessageCircle size={18} className="text-ink-soft" />
            <p className="font-body font-semibold text-ink text-xs">Messages</p>
          </Link>
          <Link
            to="/class-updates"
            className="flex flex-col items-center justify-center gap-1 rounded-2xl bg-paper-dim px-3 py-3 hover:bg-sage/60 transition-colors"
          >
            <Megaphone size={18} className="text-ink-soft" />
            <p className="font-body font-semibold text-ink text-xs">Class updates</p>
          </Link>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Card className="flex flex-col items-center gap-2 py-6">
            <ProgressRing
              value={overview.progress.completionPercent}
              label={`${overview.progress.completionPercent}%`}
              sublabel="of the Quran"
              tone="teal"
            />
          </Card>
          <Card className="flex flex-col items-center justify-center gap-3 py-6">
            <StreakBadge streak={overview.streak} isActiveToday={isActiveToday} />
          </Card>
        </div>

        <div className="flex gap-3">
          <StatTile label="Practice sessions" value={String(overview.progress.totalPracticeAttempts)} />
          <StatTile label="Tests taken" value={String(overview.progress.totalTestSessions)} />
          <StatTile
            label="Avg. test score"
            value={overview.progress.overallAverageTestScore != null ? `${overview.progress.overallAverageTestScore}%` : '—'}
          />
        </div>

        <section>
          <h3 className="heading-subsection mb-3">This week's activity</h3>
          <Card>
            <WeeklyActivityChart data={overview.progress.weeklyActivity} />
            <div className="flex items-center gap-4 mt-2 justify-center">
              <span className="flex items-center gap-1.5 text-[11px] text-ink-soft font-body">
                <span className="h-2 w-2 rounded-full bg-teal" /> Practice
              </span>
              <span className="flex items-center gap-1.5 text-[11px] text-ink-soft font-body">
                <span className="h-2 w-2 rounded-full bg-gold" /> Test
              </span>
            </div>
          </Card>
        </section>

        <section>
          <h3 className="heading-subsection mb-3">Today's Sabaq</h3>
          {overview.todaysSabaq ? (
            <SabaqCard sabaq={overview.todaysSabaq} />
          ) : (
            <Card>
              <p className="font-body text-sm text-ink-soft">No Sabaq assigned yet.</p>
            </Card>
          )}
        </section>

        {overview.recentSabaqs.length > 0 && (
          <section>
            <h3 className="heading-subsection mb-3">Recent Sabaqs</h3>
            <div className="flex flex-col gap-2">
              {overview.recentSabaqs.map((s) => (
                <SabaqCard key={s.id} sabaq={s} />
              ))}
            </div>
          </section>
        )}

        <section>
          <h3 className="heading-subsection mb-3">Teacher comments</h3>
          {overview.feedback.length > 0 ? (
            <div className="flex flex-col gap-2">
              {overview.feedback.map((f) => (
                <FeedbackItem key={f.id} feedback={f} />
              ))}
            </div>
          ) : (
            <Card>
              <p className="font-body text-sm text-ink-soft">No feedback from a teacher yet.</p>
            </Card>
          )}
        </section>

        <Card className="py-4 text-center opacity-70">
          <p className="font-body text-xs text-ink-soft">
            Attendance isn't tracked anywhere in the app yet — it needs a real class/session model,
            which is out of scope until the backend (Phase 10). Nothing here is a stand-in for it.
          </p>
        </Card>
      </main>
    </>
  );
}
