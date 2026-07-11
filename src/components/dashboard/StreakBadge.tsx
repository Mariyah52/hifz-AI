import { Flame } from 'lucide-react';
import type { StreakInfo } from '@/types/user';

interface StreakBadgeProps {
  streak: StreakInfo;
  isActiveToday: boolean;
}

export function StreakBadge({ streak, isActiveToday }: StreakBadgeProps) {
  return (
    <div className="flex items-center gap-3 rounded-full bg-maroon/[0.08] pl-2 pr-4 py-2">
      <div
        className={`grid h-9 w-9 place-items-center rounded-full bg-maroon/10 text-maroon
          ${isActiveToday ? 'animate-[flame-flicker_2.4s_ease-in-out_infinite]' : ''}`}
      >
        <Flame size={18} fill={isActiveToday ? 'currentColor' : 'none'} />
      </div>
      <div className="leading-tight">
        <p className="font-mono text-base font-semibold text-maroon">{streak.currentStreak} days</p>
        <p className="text-[11px] text-ink-soft">
          {isActiveToday ? "Today's Sabaq logged" : 'Recite today to keep it going'}
        </p>
      </div>
    </div>
  );
}
