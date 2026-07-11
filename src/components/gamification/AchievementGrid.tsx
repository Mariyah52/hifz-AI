import { Award, Lock } from 'lucide-react';
import type { Achievement } from '@/types/gamification';

interface AchievementGridProps {
  earned: Achievement[];
  locked: Achievement[];
}

export function AchievementGrid({ earned, locked }: AchievementGridProps) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {earned.map((achievement) => (
        <div
          key={achievement.key}
          className="flex flex-col items-center text-center gap-1.5 rounded-2xl bg-gold/10 px-3 py-4"
        >
          <div className="grid h-10 w-10 place-items-center rounded-full bg-gold/20 text-[#8a6218]">
            <Award size={20} />
          </div>
          <p className="font-body font-semibold text-ink text-xs">{achievement.name}</p>
          <p className="font-body text-[11px] text-ink-soft leading-snug">{achievement.description}</p>
        </div>
      ))}
      {locked.map((achievement) => (
        <div
          key={achievement.key}
          className="flex flex-col items-center text-center gap-1.5 rounded-2xl bg-sage/50 px-3 py-4 opacity-60"
        >
          <div className="grid h-10 w-10 place-items-center rounded-full bg-ink/[0.06] text-ink-soft">
            <Lock size={18} />
          </div>
          <p className="font-body font-semibold text-ink-soft text-xs">{achievement.name}</p>
          <p className="font-body text-[11px] text-ink-soft leading-snug">{achievement.description}</p>
        </div>
      ))}
    </div>
  );
}
