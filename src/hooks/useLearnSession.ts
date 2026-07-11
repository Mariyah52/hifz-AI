import { useEffect, useMemo, useState } from 'react';
import { useSurah } from '@/hooks/useQuranData';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';
import { getSurahTajweedText, getSurahText } from '@/services/quranTextService';
import type { AyahText } from '@/types/quran';

interface UseLearnSessionArgs {
  surahNumber: number;
  rangeStart?: number;
  rangeEnd?: number;
}

export function useLearnSession({ surahNumber, rangeStart, rangeEnd }: UseLearnSessionArgs) {
  const surah = useSurah(surahNumber);
  const [ayahs, setAyahs] = useState<AyahText[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showTajweed, setShowTajweed] = useState(false);
  const [tajweedAyahs, setTajweedAyahs] = useState<AyahText[] | null>(null);
  const [isTajweedLoading, setIsTajweedLoading] = useState(false);
  const [tajweedError, setTajweedError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setAyahs(null);
    setError(null);
    setTajweedAyahs(null);
    setTajweedError(null);

    getSurahText(surahNumber)
      .then((text) => {
        if (!cancelled) setAyahs(text);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load ayah text');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [surahNumber]);

  // Fetched lazily (only once the student actually asks for tajweed
  // colors) rather than alongside the plain text on every visit — most
  // visits never need it, and it's a separate network request/edition.
  useEffect(() => {
    if (!showTajweed || tajweedAyahs || isTajweedLoading) return;
    let cancelled = false;
    setIsTajweedLoading(true);
    setTajweedError(null);

    getSurahTajweedText(surahNumber)
      .then((text) => {
        if (!cancelled) setTajweedAyahs(text);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setTajweedError(err instanceof Error ? err.message : 'Failed to load tajweed colors');
        }
      })
      .finally(() => {
        if (!cancelled) setIsTajweedLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showTajweed, surahNumber]);

  const ayahNumbers = useMemo(
    () => (surah ? Array.from({ length: surah.ayahCount }, (_, i) => i + 1) : []),
    [surah],
  );

  const player = useAudioPlayer({
    surahNumber,
    ayahNumbers: ayahNumbers.length > 0 ? ayahNumbers : [1],
    rangeStart,
    rangeEnd,
  });

  return {
    surah,
    ayahs,
    error,
    isLoading: !ayahs && !error,
    showTajweed,
    setShowTajweed,
    tajweedAyahs,
    isTajweedLoading,
    tajweedError,
    ...player,
  };
}
