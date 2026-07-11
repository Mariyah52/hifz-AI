import { ProgressRing } from '@/components/ui/ProgressRing';

interface LevelCardProps {
  level: number;
  xp: number;
  xpIntoLevel: number;
  xpToNextLevel: number;
}

export function LevelCard({ level, xp, xpIntoLevel, xpToNextLevel }: LevelCardProps) {
  const levelSpan = xpIntoLevel + xpToNextLevel;
  const percent = levelSpan > 0 ? (xpIntoLevel / levelSpan) * 100 : 0;

  return (
    <div className="flex items-center gap-4">
      <ProgressRing value={percent} size={88} label={`Lvl ${level}`} sublabel={`${xpToNextLevel} XP to next`} tone="gold" />
      <div>
        <p className="font-display text-lg font-semibold text-ink">{xp.toLocaleString()} XP</p>
        <p className="font-body text-xs text-ink-soft mt-0.5">
          Earned from real practice attempts, tests, completed Sabaqs, and your streak — nothing
          fabricated.
        </p>
      </div>
    </div>
  );
}
