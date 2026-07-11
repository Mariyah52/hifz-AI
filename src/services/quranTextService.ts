import { getCachedJson, setCachedJson } from './textCacheDb';
import { isParseableTajweedText } from '@/utils/tajweed';
import type { AyahText } from '@/types/quran';

/**
 * Quran text is NEVER bundled as static data in this app — a single
 * mistyped diacritic in scripture is not an acceptable risk. Instead this
 * service fetches the standard Uthmani text at runtime from Al Quran
 * Cloud's public API (no auth, no rate limit published) and caches it
 * in memory per surah for the session.
 *
 * Phase 26: successful fetches are also persisted to IndexedDB
 * (textCacheDb.ts), so a surah visited once while online renders from
 * that cache on a later offline visit — network is still tried first
 * every time (so text always reflects the live source when reachable);
 * the cache is a fallback, not a replacement for it.
 *
 * If this API ever needs to change, this file is the only place that
 * needs to — pages call getSurahText()/getAyahText(), never the network
 * directly.
 */
const API_BASE = 'https://api.alquran.cloud/v1';
const TEXT_EDITION = 'quran-uthmani';

interface RawAyah {
  numberInSurah: number;
  text: string;
}

interface RawSurahResponse {
  data: { ayahs: RawAyah[] };
}

const surahTextCache = new Map<number, AyahText[]>();
const inFlight = new Map<number, Promise<AyahText[]>>();

function cacheKey(surahNumber: number): string {
  return `surah:${surahNumber}`;
}

export async function getSurahText(surahNumber: number): Promise<AyahText[]> {
  const cached = surahTextCache.get(surahNumber);
  if (cached) return cached;

  const pending = inFlight.get(surahNumber);
  if (pending) return pending;

  const request = (async () => {
    try {
      const res = await fetch(`${API_BASE}/surah/${surahNumber}/${TEXT_EDITION}`);
      if (!res.ok) {
        throw new Error(`Failed to load surah ${surahNumber} text (HTTP ${res.status})`);
      }
      const json = (await res.json()) as RawSurahResponse;
      const ayahs: AyahText[] = json.data.ayahs.map((a) => ({
        surahNumber,
        ayahNumber: a.numberInSurah,
        text: a.text,
      }));
      surahTextCache.set(surahNumber, ayahs);
      setCachedJson(cacheKey(surahNumber), ayahs);
      return ayahs;
    } catch (networkError) {
      const offlineCopy = await getCachedJson<AyahText[]>(cacheKey(surahNumber));
      if (offlineCopy) {
        surahTextCache.set(surahNumber, offlineCopy);
        return offlineCopy;
      }
      throw networkError;
    } finally {
      inFlight.delete(surahNumber);
    }
  })();

  inFlight.set(surahNumber, request);
  return request;
}

export async function getAyahText(surahNumber: number, ayahNumber: number): Promise<AyahText | undefined> {
  const ayahs = await getSurahText(surahNumber);
  return ayahs.find((a) => a.ayahNumber === ayahNumber);
}

const TAJWEED_EDITION = 'quran-tajweed';
const tajweedTextCache = new Map<number, AyahText[]>();
const tajweedInFlight = new Map<number, Promise<AyahText[]>>();

/**
 * Same live-fetch/cache pattern as `getSurahText`, but the `quran-tajweed`
 * edition — each ayah's `text` comes back with tajweed rules embedded as
 * inline `<tajweed class="...">` tags (see utils/tajweed.ts for how those
 * get parsed into colored spans). Reading/display use only — Practice and
 * Test mode's word-diff analysis must keep using the plain
 * `getSurahText`/`getAyahText` above, never this, since the embedded tags
 * aren't part of the actual recited words.
 */
export async function getSurahTajweedText(surahNumber: number): Promise<AyahText[]> {
  const cached = tajweedTextCache.get(surahNumber);
  if (cached) return cached;

  const pending = tajweedInFlight.get(surahNumber);
  if (pending) return pending;

  const request = (async () => {
    try {
      const res = await fetch(`${API_BASE}/surah/${surahNumber}/${TAJWEED_EDITION}`);
      if (!res.ok) {
        throw new Error(`Failed to load surah ${surahNumber} tajweed text (HTTP ${res.status})`);
      }
      const json = (await res.json()) as RawSurahResponse;
      const ayahs: AyahText[] = json.data.ayahs.map((a) => ({
        surahNumber,
        ayahNumber: a.numberInSurah,
        text: a.text,
      }));
      if (!isParseableTajweedText(ayahs)) {
        throw new Error(
          "Tajweed colors aren't available right now — the source returned a format this app can't safely interpret yet.",
        );
      }
      tajweedTextCache.set(surahNumber, ayahs);
      setCachedJson(`tajweed:${surahNumber}`, ayahs);
      return ayahs;
    } catch (networkError) {
      const offlineCopy = await getCachedJson<AyahText[]>(`tajweed:${surahNumber}`);
      if (offlineCopy) {
        tajweedTextCache.set(surahNumber, offlineCopy);
        return offlineCopy;
      }
      throw networkError;
    } finally {
      tajweedInFlight.delete(surahNumber);
    }
  })();

  tajweedInFlight.set(surahNumber, request);
  return request;
}
