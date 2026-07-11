import { RotateCcw } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import type { PaceEstimate } from '@/types/practice';

interface PlaybackControlsProps {
  audioUrl: string;
  durationSeconds: number;
  pace: PaceEstimate;
  onReRecord: () => void;
}

export function PlaybackControls({ audioUrl, durationSeconds, pace, onReRecord }: PlaybackControlsProps) {
  return (
    <div className="flex flex-col gap-3">
      <audio src={audioUrl} controls className="w-full" />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-ink-soft">{durationSeconds.toFixed(1)}s</span>
          <Badge tone={pace.withinExpectedRange ? 'teal' : 'gold'}>
            {pace.withinExpectedRange ? 'steady pace' : 'check your pace'}
          </Badge>
        </div>
        <button
          onClick={onReRecord}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-dark hover:text-teal transition-colors"
        >
          <RotateCcw size={14} />
          Re-record
        </button>
      </div>

      <p className="text-xs text-ink-soft font-body">
        Pace is a rough local timing check, not recitation analysis — pronunciation and fluency
        feedback will arrive once AI scoring lands.
      </p>
    </div>
  );
}
