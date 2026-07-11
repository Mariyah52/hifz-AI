import { Pause, Play, SkipBack, SkipForward } from 'lucide-react';
import { RepeatModeSelect } from './RepeatModeSelect';
import type { RepeatMode } from '@/types/lesson';

interface AudioControlsProps {
  currentAyah: number;
  totalAyahs: number;
  isPlaying: boolean;
  repeatMode: RepeatMode;
  onToggle: () => void;
  onPrev: () => void;
  onNext: () => void;
  onRepeatModeChange: (mode: RepeatMode) => void;
}

export function AudioControls({
  currentAyah,
  totalAyahs,
  isPlaying,
  repeatMode,
  onToggle,
  onPrev,
  onNext,
  onRepeatModeChange,
}: AudioControlsProps) {
  return (
    <div className="rounded-card bg-paper border border-ink/[0.06] shadow-folio p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-ink-soft">
          Ayah {currentAyah} of {totalAyahs}
        </span>
        <span className="font-mono text-xs text-ink-soft">Al-Husary</span>
      </div>

      <div className="flex items-center justify-center gap-6">
        <button
          aria-label="Previous ayah"
          onClick={onPrev}
          disabled={currentAyah <= 1}
          className="text-ink-soft hover:text-ink disabled:opacity-30 transition-colors"
        >
          <SkipBack size={22} />
        </button>
        <button
          aria-label={isPlaying ? 'Pause' : 'Play'}
          onClick={onToggle}
          className="grid h-14 w-14 place-items-center rounded-full bg-teal text-paper hover:bg-teal-dark transition-colors"
        >
          {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-0.5" />}
        </button>
        <button
          aria-label="Next ayah"
          onClick={onNext}
          disabled={currentAyah >= totalAyahs}
          className="text-ink-soft hover:text-ink disabled:opacity-30 transition-colors"
        >
          <SkipForward size={22} />
        </button>
      </div>

      <RepeatModeSelect value={repeatMode} onChange={onRepeatModeChange} />
    </div>
  );
}
