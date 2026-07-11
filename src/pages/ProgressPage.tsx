import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { Header } from '@/components/layout/Header';
import { Card } from '@/components/ui/Card';
import { ProgressRing } from '@/components/ui/ProgressRing';
import { StreakBadge } from '@/components/dashboard/StreakBadge';
import { StatTile } from '@/components/progress/StatTile';
import { WeeklyActivityChart } from '@/components/progress/WeeklyActivityChart';
import { MonthlyTrendChart } from '@/components/progress/MonthlyTrendChart';
import { LevelCard } from '@/components/gamification/LevelCard';
import { AchievementGrid } from '@/components/gamification/AchievementGrid';
import { useDashboard } from '@/hooks/useDashboard';
import { useProgress } from '@/hooks/useProgress';
import { useGamification } from '@/hooks/useGamification';

export function ProgressPage() {
  // react-query dedupes this against DashboardPage's own useDashboard()
  // call under the same 'dashboard' queryKey — no duplicate network request.
  const { data: dashboard, isLoading: isDashboardLoading } = useDashboard();
  const { data: progress, isLoading: isProgressLoading } = useProgress();
  const { data: gamification } = useGamification();

  if (isDashboardLoading || isProgressLoading || !dashboard || !progress) {
    return <div className="p-5 text-ink-soft font-body text-sm">Loading your progress…</div>;
  }

  const isActiveToday = dashboard.streak.lastActiveDate === new Date().toISOString().slice(0, 10);

  return (
    <>
      <Header greeting="Progress" name="Your Hifz journey" />

      <main className="px-5 flex flex-col gap-5 mt-2 pb-4">
        <div className="grid grid-cols-2 gap-4">
          <Card className="flex flex-col items-center gap-2 py-6">
            <ProgressRing
              value={progress.completionPercent}
              label={`${progress.completionPercent}%`}
              sublabel="of the Quran"
              tone="teal"
            />
          </Card>
          <Card className="flex flex-col items-center justify-center gap-3 py-6">
            <StreakBadge streak={dashboard.streak} isActiveToday={isActiveToday} />
          </Card>
        </div>

        <Card>
          <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-1">
            Memorized ayat (self-reported)
          </p>
          <p className="font-mono text-2xl font-semibold text-ink">
            {progress.memorizedAyahCount.toLocaleString()}
            <span className="text-sm text-ink-soft font-body"> / {progress.totalAyahCount.toLocaleString()}</span>
          </p>
          <p className="text-xs text-ink-soft font-body mt-1">
            Counted from ayahs you've marked "correct" after revealing them in Test Mode — your own
            self-check, not an AI-verified count.
          </p>
        </Card>

        <div className="flex gap-3">
          <StatTile label="Practice sessions" value={String(progress.totalPracticeAttempts)} />
          <StatTile label="Tests taken" value={String(progress.totalTestSessions)} />
          <StatTile
            label="Avg. test score"
            value={progress.overallAverageTestScore != null ? `${progress.overallAverageTestScore}%` : '—'}
          />
        </div>

        {gamification && (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-display text-base font-semibold text-ink">Level &amp; Achievements</h3>
              <Link
                to="/leaderboard"
                className="flex items-center gap-1 text-xs font-body font-semibold text-teal-dark hover:text-teal-dark/80 transition-colors"
              >
                Leaderboard <ChevronRight size={14} />
              </Link>
            </div>
            <Card className="flex flex-col gap-4">
              <LevelCard
                level={gamification.level}
                xp={gamification.xp}
                xpIntoLevel={gamification.xpIntoLevel}
                xpToNextLevel={gamification.xpToNextLevel}
              />
              <AchievementGrid earned={gamification.earnedAchievements} locked={gamification.lockedAchievements} />
            </Card>
          </section>
        )}

        <Link
          to="/analytics"
          className="flex items-center justify-between rounded-2xl bg-teal/10 px-4 py-3 hover:bg-teal/20 transition-colors"
        >
          <div>
            <p className="font-body font-semibold text-teal-dark text-sm">Deeper insights</p>
            <p className="font-body text-xs text-ink-soft mt-0.5">
              Weakest juz, weakest pages, retention rate, and more
            </p>
          </div>
          <ChevronRight size={16} className="text-teal-dark" />
        </Link>

        <Link
          to="/certificates"
          className="flex items-center justify-between rounded-2xl bg-gold/10 px-4 py-3 hover:bg-gold/20 transition-colors"
        >
          <div>
            <p className="font-body font-semibold text-[#8a6218] text-sm">Certificates</p>
            <p className="font-body text-xs text-ink-soft mt-0.5">Completion, attendance, and achievement certificates</p>
          </div>
          <ChevronRight size={16} className="text-[#8a6218]" />
        </Link>

        <Link
          to="/notes"
          className="flex items-center justify-between rounded-2xl bg-paper-dim px-4 py-3 hover:bg-sage/60 transition-colors"
        >
          <div>
            <p className="font-body font-semibold text-ink text-sm">Notes</p>
            <p className="font-body text-xs text-ink-soft mt-0.5">Things you've jotted down for yourself</p>
          </div>
          <ChevronRight size={16} className="text-ink-soft" />
        </Link>

        <section>
          <h3 className="font-display text-base font-semibold text-ink mb-3">This week</h3>
          <Card>
            <WeeklyActivityChart data={progress.weeklyActivity} />
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
          <h3 className="font-display text-base font-semibold text-ink mb-3">Last 30 days</h3>
          <Card>
            <MonthlyTrendChart data={progress.monthlyActivity} />
          </Card>
        </section>
      </main>
    </>
  );
}
