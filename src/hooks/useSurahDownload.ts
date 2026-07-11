import { useCallback, useEffect, useState } from 'react';
import * as audioCacheService from '@/services/audioCacheService';
import type { DownloadProgress } from '@/services/audioCacheService';

export function useSurahDownload(surahNumber: number, ayahCount: number) {
  const [isDownloaded, setIsDownloaded] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [progress, setProgress] = useState<DownloadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshStatus = useCallback(() => {
    if (!ayahCount) return;
    audioCacheService.isSurahFullyDownloaded(surahNumber, ayahCount).then(setIsDownloaded);
  }, [surahNumber, ayahCount]);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  const download = useCallback(async () => {
    setIsDownloading(true);
    setError(null);
    setProgress({ completed: 0, total: ayahCount });
    try {
      await audioCacheService.downloadSurah(surahNumber, ayahCount, setProgress);
      setIsDownloaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed — check your connection and try again.');
    } finally {
      setIsDownloading(false);
      setProgress(null);
    }
  }, [surahNumber, ayahCount]);

  const remove = useCallback(async () => {
    await audioCacheService.deleteSurahDownload(surahNumber, ayahCount);
    setIsDownloaded(false);
  }, [surahNumber, ayahCount]);

  return { isDownloaded, isDownloading, progress, error, download, remove };
}
