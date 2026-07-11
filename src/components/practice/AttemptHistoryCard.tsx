import { useEffect, useRef, useState } from 'react';
import { Play, Pause, Sparkles, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { MistakeList } from '@/components/practice/MistakeList';
import { resolveMediaUrl } from '@/services/apiClient';
import { analyzeAttempt } from '@/services/practiceService';
import type { PracticeAttempt } from '@/types/practice';

interface AttemptHistoryCardProps {
  attempt: PracticeAttempt;
}

export function AttemptHistoryCard({ attempt: initialAttempt }: AttemptHistoryCardProps) {
  const [attempt, setAttempt] = useState(initialAttempt);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  // Resync if the parent hands us a fresh copy of the same attempt (e.g.
  // after the surrounding list refetches for an unrelated reason).
  useEffect(() => {
    setAttempt(initialAttempt);
  }, [initialAttempt]);

  const date = new Date(attempt.recordedAt);
  const dateLabel = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  const timeLabel = date.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  function togglePlayback() {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) audio.pause();
    else audio.play();
  }

  async function handleAnalyze() {
    setIsAnalyzing(true);
    try {
      const updated = await analyzeAttempt(attempt.id);
      setAttempt(updated);
      setIsExpanded(true);
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <div className="rounded-2xl bg-paper-dim px-4 py-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-body font-semibold text-ink text-sm">
            Ayah {attempt.fromAyah}–{attempt.toAyah}
          </p>
          <p className="font-mono text-xs text-ink-soft mt-0.5">
            {dateLabel} · {timeLabel} · {attempt.durationSeconds.toFixed(1)}s
          </p>
        </div>
        <div className="flex items-center gap-2">
          {attempt.audioUrl && (
            <>
              <audio
                ref={audioRef}
                src={resolveMediaUrl(attempt.audioUrl)}
                onEnded={() => setIsPlaying(false)}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
              />
              <button
                aria-label={isPlaying ? 'Pause recording' : 'Play recording'}
                onClick={togglePlayback}
                className="grid h-8 w-8 place-items-center rounded-full bg-teal/10 text-teal-dark hover:bg-teal/20 transition-colors"
              >
                {isPlaying ? <Pause size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" className="ml-0.5" />}
              </button>
            </>
          )}
          <Badge tone={attempt.pace.withinExpectedRange ? 'teal' : 'gold'}>
            {attempt.pace.withinExpectedRange ? 'steady pace' : 'check pace'}
          </Badge>
        </div>
      </div>

      {/* Phase 14: recitation analysis — word-level diff against the real
          ayah text, not a pronunciation/fluency score. See MistakeList and
          the backend's arabic_text.py for exactly what this does and doesn't detect. */}
      {attempt.audioUrl && (
        <div className="mt-2 pt-2 border-t border-ink/[0.06]">
          {attempt.analysisStatus === 'not_analyzed' && (
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="flex items-center gap-1.5 text-xs font-body font-semibold text-teal-dark
                hover:text-teal-dark/80 transition-colors disabled:opacity-60"
            >
              {isAnalyzing ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
              {isAnalyzing ? 'Analyzing…' : 'Analyze recitation'}
            </button>
          )}

          {attempt.analysisStatus === 'failed' && (
            <div className="flex flex-col gap-1">
              <p className="font-body text-xs text-maroon">{attempt.analysisError ?? 'Analysis failed.'}</p>
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="self-start text-xs font-body font-semibold text-teal-dark hover:text-teal-dark/80 transition-colors"
              >
                {isAnalyzing ? 'Retrying…' : 'Retry'}
              </button>
            </div>
          )}

          {attempt.analysisStatus === 'completed' && (
            <div>
              <button
                onClick={() => setIsExpanded((v) => !v)}
                className="flex items-center justify-between w-full text-xs font-body"
              >
                <span className="text-ink-soft">
                  <span className="font-mono font-semibold text-ink">
                    {attempt.matchedWordCount}/{attempt.totalWordCount}
                  </span>{' '}
                  words matched
                </span>
                {isExpanded ? <ChevronUp size={14} className="text-ink-soft" /> : <ChevronDown size={14} className="text-ink-soft" />}
              </button>
              {isExpanded && (
                <div className="mt-2">
                  <MistakeList mistakes={attempt.mistakes} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
