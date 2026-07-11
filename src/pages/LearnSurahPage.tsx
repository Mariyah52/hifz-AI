import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronLeft, Palette } from 'lucide-react';
import { MushafViewer } from '@/components/mushaf/MushafViewer';
import { TajweedLegend } from '@/components/mushaf/TajweedLegend';
import { AudioControls } from '@/components/learn/AudioControls';
import { PlaybackSettingsRow } from '@/components/learn/PlaybackSettingsRow';
import { DownloadButton } from '@/components/learn/DownloadButton';
import { Card } from '@/components/ui/Card';
import { useLearnSession } from '@/hooks/useLearnSession';

export function LearnSurahPage() {
  const params = useParams<{ surahNumber: string }>();
  const surahNumber = Number(params.surahNumber);

  const [rangeStart, setRangeStart] = useState(1);
  const [rangeEnd, setRangeEnd] = useState(1);

  const {
    surah,
    ayahs,
    error,
    isLoading,
    currentAyah,
    isPlaying,
    repeatMode,
    setRepeatMode,
    playbackRate,
    setPlaybackRate,
    repeatGapSeconds,
    setRepeatGapSeconds,
    toggle,
    goToAyah,
    showTajweed,
    setShowTajweed,
    tajweedAyahs,
    isTajweedLoading,
    tajweedError,
  } = useLearnSession({ surahNumber, rangeStart, rangeEnd });

  // Once the surah's ayah count is known, default the range to the whole surah.
  useEffect(() => {
    if (surah) {
      setRangeStart(1);
      setRangeEnd(surah.ayahCount);
    }
  }, [surah]);

  if (!surah) {
    return (
      <div className="p-5 text-ink-soft font-body text-sm">
        {Number.isNaN(surahNumber) ? 'Unknown surah.' : 'Loading surah…'}
      </div>
    );
  }

  return (
    <>
      <header className="flex items-center justify-between gap-3 px-5 pt-6 pb-2">
        <div className="flex items-center gap-3">
          <Link
            to="/learn"
            aria-label="Back to surah list"
            className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
          >
            <ChevronLeft size={18} />
          </Link>
          <div>
            <p className="text-sm text-ink-soft font-body">Learn Mode</p>
            <h1 className="font-display text-xl font-semibold text-ink">{surah.name}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowTajweed((v) => !v)}
            aria-pressed={showTajweed}
            aria-label="Toggle tajweed colors"
            className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-body font-semibold transition-colors ${
              showTajweed ? 'bg-teal text-paper' : 'bg-sage text-ink-soft hover:bg-[#d8dfcd]'
            }`}
          >
            <Palette size={14} />
            Tajweed
          </button>
          <DownloadButton surahNumber={surah.number} ayahCount={surah.ayahCount} />
        </div>
      </header>

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
        {error && (
          <Card className="text-center py-6">
            <p className="font-body text-sm text-ink-soft">
              Couldn't load this surah's text right now. Check your connection and try again.
            </p>
          </Card>
        )}

        {isLoading && !error && (
          <Card className="text-center py-10">
            <p className="font-body text-sm text-ink-soft">Loading ayahs…</p>
          </Card>
        )}

        {showTajweed && isTajweedLoading && (
          <p className="text-center font-mono text-xs text-ink-soft">Loading tajweed colors…</p>
        )}
        {showTajweed && tajweedError && (
          <p className="text-center font-body text-xs text-maroon">{tajweedError}</p>
        )}

        {ayahs && (
          <MushafViewer
            ayahs={ayahs}
            activeAyah={currentAyah}
            onSelectAyah={goToAyah}
            tajweedAyahs={showTajweed ? tajweedAyahs : null}
          />
        )}

        {showTajweed && tajweedAyahs && <TajweedLegend />}

        <AudioControls
          currentAyah={currentAyah}
          totalAyahs={surah.ayahCount}
          isPlaying={isPlaying}
          repeatMode={repeatMode}
          onToggle={toggle}
          onPrev={() => goToAyah(Math.max(1, currentAyah - 1))}
          onNext={() => goToAyah(Math.min(surah.ayahCount, currentAyah + 1))}
          onRepeatModeChange={setRepeatMode}
        />

        <Card>
          <PlaybackSettingsRow
            playbackRate={playbackRate}
            onPlaybackRateChange={setPlaybackRate}
            repeatGapSeconds={repeatGapSeconds}
            onRepeatGapSecondsChange={setRepeatGapSeconds}
          />
        </Card>

        {repeatMode === 'range' && (
          <Card className="flex items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
              From
              <input
                type="number"
                min={1}
                max={surah.ayahCount}
                value={rangeStart}
                onChange={(e) => setRangeStart(Number(e.target.value))}
                className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink"
              />
            </label>
            <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
              To
              <input
                type="number"
                min={rangeStart}
                max={surah.ayahCount}
                value={rangeEnd}
                onChange={(e) => setRangeEnd(Number(e.target.value))}
                className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink"
              />
            </label>
          </Card>
        )}
      </main>
    </>
  );
}
