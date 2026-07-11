import { getAyahAudioUrl } from './audioService';
import * as cacheDb from './audioCacheDb';

const DOWNLOADED_SURAHS_KEY = 'downloadedSurahs';

export interface DownloadProgress {
  completed: number;
  total: number;
}

/** The CDN URL doubles as a natural, globally-unique cache key — no separate id scheme needed. */
function cacheKey(surahNumber: number, ayahNumber: number): string {
  return getAyahAudioUrl(surahNumber, ayahNumber);
}

export async function isAyahCached(surahNumber: number, ayahNumber: number): Promise<boolean> {
  const blob = await cacheDb.getBlob(cacheKey(surahNumber, ayahNumber));
  return blob !== undefined;
}

/**
 * Resolves the URL `useAudioPlayer` should actually play: a local
 * `blob:` URL if this ayah was downloaded, otherwise the live CDN URL
 * (which still works fine online — this function is the only thing that
 * changed, not the fallback behavior).
 */
export async function getPlayableAyahUrl(surahNumber: number, ayahNumber: number): Promise<string> {
  const key = cacheKey(surahNumber, ayahNumber);
  const cached = await cacheDb.getBlob(key);
  if (cached) return URL.createObjectURL(cached);
  return key;
}

export async function downloadAyah(surahNumber: number, ayahNumber: number): Promise<void> {
  const key = cacheKey(surahNumber, ayahNumber);
  const existing = await cacheDb.getBlob(key);
  if (existing) return;

  const response = await fetch(key);
  if (!response.ok) {
    throw new Error(`Couldn't download ayah ${ayahNumber} audio (HTTP ${response.status})`);
  }
  const blob = await response.blob();
  await cacheDb.putBlob(key, blob);
}

/**
 * Downloads a whole surah's audio for offline use. Sequential on purpose
 * — firing e.g. 286 parallel requests for Al-Baqarah would hammer the CDN
 * and the browser's connection pool for no real speed benefit on a
 * mobile connection; one-at-a-time with progress reporting is the
 * friendlier choice here.
 */
export async function downloadSurah(
  surahNumber: number,
  ayahCount: number,
  onProgress?: (progress: DownloadProgress) => void,
): Promise<void> {
  for (let ayah = 1; ayah <= ayahCount; ayah++) {
    await downloadAyah(surahNumber, ayah);
    onProgress?.({ completed: ayah, total: ayahCount });
  }

  const downloaded = (await cacheDb.getMeta<number[]>(DOWNLOADED_SURAHS_KEY)) ?? [];
  if (!downloaded.includes(surahNumber)) {
    await cacheDb.setMeta(DOWNLOADED_SURAHS_KEY, [...downloaded, surahNumber]);
  }
}

export async function deleteSurahDownload(surahNumber: number, ayahCount: number): Promise<void> {
  for (let ayah = 1; ayah <= ayahCount; ayah++) {
    await cacheDb.deleteBlob(cacheKey(surahNumber, ayah));
  }
  const downloaded = (await cacheDb.getMeta<number[]>(DOWNLOADED_SURAHS_KEY)) ?? [];
  await cacheDb.setMeta(
    DOWNLOADED_SURAHS_KEY,
    downloaded.filter((n) => n !== surahNumber),
  );
}

/** Fast path for list views: one metadata read instead of checking every ayah of every surah. */
export async function getDownloadedSurahNumbers(): Promise<number[]> {
  return (await cacheDb.getMeta<number[]>(DOWNLOADED_SURAHS_KEY)) ?? [];
}

/** Authoritative but slower check — used on a single surah's own page, not list views. */
export async function isSurahFullyDownloaded(surahNumber: number, ayahCount: number): Promise<boolean> {
  for (let ayah = 1; ayah <= ayahCount; ayah++) {
    if (!(await isAyahCached(surahNumber, ayah))) return false;
  }
  return true;
}

export async function getCacheStats(): Promise<{ ayahCount: number; approxBytes: number }> {
  const keys = await cacheDb.getAllBlobKeys();
  let approxBytes = 0;
  for (const key of keys) {
    const blob = await cacheDb.getBlob(key);
    if (blob) approxBytes += blob.size;
  }
  return { ayahCount: keys.length, approxBytes };
}
