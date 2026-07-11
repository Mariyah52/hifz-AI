import { PLAYBACK_RATES, REPEAT_GAP_OPTIONS_SECONDS, type PlaybackRate } from '@/hooks/useAudioPlayer';

interface PlaybackSettingsRowProps {
  playbackRate: PlaybackRate;
  onPlaybackRateChange: (rate: PlaybackRate) => void;
  repeatGapSeconds: number;
  onRepeatGapSecondsChange: (seconds: number) => void;
}

const selectClass =
  'rounded-lg border border-ink/10 bg-paper-dim px-2 py-1.5 font-mono text-xs text-ink';

export function PlaybackSettingsRow({
  playbackRate,
  onPlaybackRateChange,
  repeatGapSeconds,
  onRepeatGapSecondsChange,
}: PlaybackSettingsRowProps) {
  return (
    <div className="flex items-center justify-between gap-3">
      <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
        Speed
        <select
          value={playbackRate}
          onChange={(e) => onPlaybackRateChange(Number(e.target.value) as PlaybackRate)}
          className={selectClass}
        >
          {PLAYBACK_RATES.map((rate) => (
            <option key={rate} value={rate}>
              {rate}×
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
        Gap between repeats
        <select
          value={repeatGapSeconds}
          onChange={(e) => onRepeatGapSecondsChange(Number(e.target.value))}
          className={selectClass}
        >
          {REPEAT_GAP_OPTIONS_SECONDS.map((seconds) => (
            <option key={seconds} value={seconds}>
              {seconds === 0 ? 'None' : `${seconds}s`}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
