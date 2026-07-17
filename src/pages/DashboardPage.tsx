import { Header } from '@/components/layout/Header';
import { ContinueCTA } from '@/components/dashboard/ContinueCTA';
import { StreakBadge } from '@/components/dashboard/StreakBadge';
import { SabaqCard } from '@/components/dashboard/SabaqCard';
import { DailyPlanCard } from '@/components/dashboard/DailyPlanCard';
import { Card } from '@/components/ui/Card';
import { ProgressRing } from '@/components/ui/ProgressRing';
import { useDashboard } from '@/hooks/useDashboard';
import { useDueReviews } from '@/hooks/useDueReviews';
import { Link } from 'react-router-dom';
import { ChevronRight, Sparkles, Radio, MessageCircle, Megaphone } from 'lucide-react';
import type { Sabaq, SabqiReview, ManzilReview } from '@/types/lesson';
import type { StreakInfo } from '@/types/user';

function greetingForNow(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export function DashboardPage() {
  const { data, isLoading } = useDashboard();

  if (isLoading || !data) {
    return <div className="p-5 text-ink-soft font-body text-sm">Loading your dashboard…</div>;
  }

  return (
    <DashboardContent
      name={data.user.name.split(' ')[0]}
      todaysSabaq={data.todaysSabaq}
      todaysSabqi={data.todaysSabqi}
      todaysManzil={data.todaysManzil}
      recentSabaqs={data.recentSabaqs}
      juzProgress={data.juzProgress}
      overallAccuracy={data.overallAccuracy}
      streak={data.streak}
    />
  );
}

interface DashboardContentProps {
  name: string;
  todaysSabaq: Sabaq | null;
  todaysSabqi: SabqiReview | null;
  todaysManzil: ManzilReview | null;
  recentSabaqs: Sabaq[];
  juzProgress: number;
  overallAccuracy: number;
  streak: StreakInfo;
}

function DashboardContent({
  name,
  todaysSabaq,
  todaysSabqi,
  todaysManzil,
  recentSabaqs,
  juzProgress,
  overallAccuracy,
  streak,
}: DashboardContentProps) {
  const isActiveToday = streak.lastActiveDate === new Date().toISOString().slice(0, 10);
  const { data: dueReviews } = useDueReviews();

  return (
    <>
      <Header greeting={greetingForNow()} name={name} />

      <main className="px-5 flex flex-col gap-5 mt-2">
        {todaysSabaq && <ContinueCTA sabaq={todaysSabaq} />}

        <StreakBadge streak={streak} isActiveToday={isActiveToday} />

        <Link
          to="/live-session"
          className="flex items-center justify-between rounded-2xl bg-maroon/10 px-4 py-3 hover:bg-maroon/20 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Radio size={18} className="text-maroon shrink-0" />
            <div>
              <p className="font-body font-semibold text-maroon text-sm">Live class</p>
              <p className="font-body text-xs text-ink-soft mt-0.5">Join if your teacher has started one</p>
            </div>
          </div>
          <ChevronRight size={16} className="text-maroon shrink-0" />
        </Link>

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

        <Link
          to="/assistant"
          className="flex items-center justify-between rounded-2xl bg-teal/10 px-4 py-3 hover:bg-teal/20 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-teal-dark shrink-0" />
            <div>
              <p className="font-body font-semibold text-teal-dark text-sm">Ask your tutor</p>
              <p className="font-body text-xs text-ink-soft mt-0.5">
                Weak spots, what to revise, tajweed questions
              </p>
            </div>
          </div>
          <ChevronRight size={16} className="text-teal-dark shrink-0" />
        </Link>

        <section>
          <h3 className="heading-subsection mb-3">Today's Plan</h3>
          <DailyPlanCard sabaq={todaysSabaq} sabqi={todaysSabqi} manzil={todaysManzil} />
          {dueReviews && dueReviews.length > 0 && (
            <Link
              to="/revision"
              className="flex items-center justify-between mt-2 px-1 py-2 text-sm font-body
                text-teal-dark hover:text-teal-dark/80 transition-colors"
            >
              <span>
                {dueReviews.length} review{dueReviews.length === 1 ? '' : 's'} due — see all
              </span>
              <ChevronRight size={16} />
            </Link>
          )}
        </section>

        <div className="grid grid-cols-2 gap-4">
          <Card className="flex flex-col items-center gap-2 py-6">
            <ProgressRing
              value={(juzProgress / 30) * 100}
              label={juzProgress.toFixed(1)}
              sublabel="of 30 Juz"
              tone="teal"
            />
          </Card>
          <Card className="flex flex-col items-center gap-2 py-6">
            <ProgressRing value={overallAccuracy} label={`${overallAccuracy}%`} sublabel="accuracy" tone="gold" />
          </Card>
        </div>

        <section>
          <h3 className="heading-subsection mb-3">Recent Sabaqs</h3>
          <div className="flex flex-col gap-2">
            {recentSabaqs.map((sabaq) => (
              <SabaqCard key={sabaq.id} sabaq={sabaq} />
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
