import { useEffect, useState } from 'react';
import { getPageAyahs, getPageAyahsTajweed, TOTAL_MUSHAF_PAGES } from '@/services/quranPageService';
import type { MushafPageAyah } from '@/types/quran';

export function useMushafPage(initialPage: number) {
  const [pageNumber, setPageNumber] = useState(clampPage(initialPage));
  const [ayahs, setAyahs] = useState<MushafPageAyah[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showTajweed, setShowTajweed] = useState(false);
  const [tajweedAyahs, setTajweedAyahs] = useState<MushafPageAyah[] | null>(null);
  const [isTajweedLoading, setIsTajweedLoading] = useState(false);
  const [tajweedError, setTajweedError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setAyahs(null);
    setError(null);
    setTajweedAyahs(null);
    setTajweedError(null);

    getPageAyahs(pageNumber)
      .then((result) => {
        if (!cancelled) setAyahs(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load this page');
      });

    return () => {
      cancelled = true;
    };
  }, [pageNumber]);

  // Lazy, same reasoning as useLearnSession — most page visits never turn this on.
  useEffect(() => {
    if (!showTajweed || tajweedAyahs || isTajweedLoading) return;
    let cancelled = false;
    setIsTajweedLoading(true);
    setTajweedError(null);

    getPageAyahsTajweed(pageNumber)
      .then((result) => {
        if (!cancelled) setTajweedAyahs(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) setTajweedError(err instanceof Error ? err.message : 'Failed to load tajweed colors');
      })
      .finally(() => {
        if (!cancelled) setIsTajweedLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showTajweed, pageNumber]);

  function goToPage(page: number) {
    setPageNumber(clampPage(page));
  }

  return {
    pageNumber,
    ayahs,
    error,
    isLoading: !ayahs && !error,
    totalPages: TOTAL_MUSHAF_PAGES,
    goToPage,
    nextPage: () => goToPage(pageNumber + 1),
    prevPage: () => goToPage(pageNumber - 1),
    showTajweed,
    setShowTajweed,
    tajweedAyahs,
    isTajweedLoading,
    tajweedError,
  };
}

function clampPage(page: number): number {
  return Math.min(TOTAL_MUSHAF_PAGES, Math.max(1, page));
}
