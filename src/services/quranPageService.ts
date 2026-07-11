import { getCachedJson, setCachedJson } from './textCacheDb';
import { isParseableTajweedText } from '@/utils/tajweed';
import type { MushafPageAyah } from '@/types/quran';

/**
 * Same principle as `quranTextService.ts`: page/hizb/sajda positions are
 * NOT hand-typed into a static table here. A cross-referenced project
 * comparing Quran metadata sources (quran-meta) explicitly documents that
 * page numbering differs between mushaf print conventions (15-line,
 * 16-line, etc.) — exactly the kind of fact this app shouldn't guess at
 * from memory. So this fetches each page's composition live, from the
 * same verified API this app already trusts for ayah text and audio,
 * rather than shipping a 604-entry table nobody here re-verified.
 *
 * Phase 26: same IndexedDB fallback as quranTextService.ts — a page
 * visited once online renders from the offline cache later; network is
 * always tried first.
 *
 * `TOTAL_MUSHAF_PAGES = 604` is the one number treated as a safe
 * constant, not fetched — it's the standard Uthmani/King Fahd Complex
 * mushaf's total page count, as invariant as "114 surahs" or "6236
 * ayahs" across virtually every print using this pagination convention.
 */
const API_BASE = 'https://api.alquran.cloud/v1';
const TEXT_EDITION = 'quran-uthmani';
const TAJWEED_EDITION = 'quran-tajweed';

export const TOTAL_MUSHAF_PAGES = 604;

interface RawPageAyah {
  numberInSurah: number;
  text: string;
  hizbQuarter?: number;
  sajda?: boolean | { id?: number; recommended?: boolean; obligatory?: boolean };
  surah: { number: number; englishName: string };
}

interface RawPageResponse {
  data: { ayahs: RawPageAyah[] };
}

interface RawSajdaResponse {
  data: { ayahs: { surah: { number: number }; numberInSurah: number }[] };
}

const pageCache = new Map<number, MushafPageAyah[]>();
const pageInFlight = new Map<number, Promise<MushafPageAyah[]>>();

let sajdaKeysCache: Set<string> | null = null;
let sajdaInFlight: Promise<Set<string>> | null = null;

function sajdaKey(surahNumber: number, ayahNumber: number): string {
  return `${surahNumber}:${ayahNumber}`;
}

function pageCacheKey(pageNumber: number): string {
  return `page:${pageNumber}`;
}

/**
 * The definitive list of sajda (prostration) ayahs — a small, fixed set
 * (14-15 ayahs depending on madhab convention; this API uses 15).
 * Fetched once per session and cached in memory, same as everything else
 * here: asked of the verified source, never encoded from memory.
 */
async function getSajdaKeys(): Promise<Set<string>> {
  if (sajdaKeysCache) return sajdaKeysCache;
  if (sajdaInFlight) return sajdaInFlight;

  sajdaInFlight = (async () => {
    try {
      const res = await fetch(`${API_BASE}/sajda/${TEXT_EDITION}`);
      if (!res.ok) throw new Error(`Failed to load sajda list (HTTP ${res.status})`);
      const json = (await res.json()) as RawSajdaResponse;
      const keys = new Set(json.data.ayahs.map((a) => sajdaKey(a.surah.number, a.numberInSurah)));
      sajdaKeysCache = keys;
      setCachedJson('sajda-keys', Array.from(keys));
      return keys;
    } catch {
      const offlineCopy = await getCachedJson<string[]>('sajda-keys');
      if (offlineCopy) {
        const keys = new Set(offlineCopy);
        sajdaKeysCache = keys;
        return keys;
      }
      // Non-critical: if this fails, pages still render — just without
      // sajda badges. Not worth blocking page load over.
      return new Set<string>();
    } finally {
      sajdaInFlight = null;
    }
  })();

  return sajdaInFlight;
}

export async function getPageAyahs(pageNumber: number): Promise<MushafPageAyah[]> {
  const cached = pageCache.get(pageNumber);
  if (cached) return cached;

  const pending = pageInFlight.get(pageNumber);
  if (pending) return pending;

  const request = (async () => {
    try {
      const [res, sajdaKeys] = await Promise.all([
        fetch(`${API_BASE}/page/${pageNumber}/${TEXT_EDITION}`),
        getSajdaKeys(),
      ]);
      if (!res.ok) {
        throw new Error(`Failed to load page ${pageNumber} (HTTP ${res.status})`);
      }
      const json = (await res.json()) as RawPageResponse;
      const ayahs: MushafPageAyah[] = json.data.ayahs.map((a) => ({
        surahNumber: a.surah.number,
        surahName: a.surah.englishName,
        ayahNumber: a.numberInSurah,
        text: a.text,
        hizbQuarter: a.hizbQuarter,
        isSajda: Boolean(a.sajda) || sajdaKeys.has(sajdaKey(a.surah.number, a.numberInSurah)),
      }));
      pageCache.set(pageNumber, ayahs);
      setCachedJson(pageCacheKey(pageNumber), ayahs);
      return ayahs;
    } catch (networkError) {
      const offlineCopy = await getCachedJson<MushafPageAyah[]>(pageCacheKey(pageNumber));
      if (offlineCopy) {
        pageCache.set(pageNumber, offlineCopy);
        return offlineCopy;
      }
      throw networkError;
    } finally {
      pageInFlight.delete(pageNumber);
    }
  })();

  pageInFlight.set(pageNumber, request);
  return request;
}

const tajweedPageCache = new Map<number, MushafPageAyah[]>();
const tajweedPageInFlight = new Map<number, Promise<MushafPageAyah[]>>();

/**
 * Same as `getPageAyahs`, but the `quran-tajweed` edition — each ayah's
 * `text` comes back with tajweed rules embedded as inline
 * `<tajweed class="...">` tags (see utils/tajweed.ts). Display use only.
 */
export async function getPageAyahsTajweed(pageNumber: number): Promise<MushafPageAyah[]> {
  const cached = tajweedPageCache.get(pageNumber);
  if (cached) return cached;

  const pending = tajweedPageInFlight.get(pageNumber);
  if (pending) return pending;

  const request = (async () => {
    try {
      const [res, sajdaKeys] = await Promise.all([
        fetch(`${API_BASE}/page/${pageNumber}/${TAJWEED_EDITION}`),
        getSajdaKeys(),
      ]);
      if (!res.ok) {
        throw new Error(`Failed to load page ${pageNumber} tajweed text (HTTP ${res.status})`);
      }
      const json = (await res.json()) as RawPageResponse;
      const ayahs: MushafPageAyah[] = json.data.ayahs.map((a) => ({
        surahNumber: a.surah.number,
        surahName: a.surah.englishName,
        ayahNumber: a.numberInSurah,
        text: a.text,
        hizbQuarter: a.hizbQuarter,
        isSajda: Boolean(a.sajda) || sajdaKeys.has(sajdaKey(a.surah.number, a.numberInSurah)),
      }));
      if (!isParseableTajweedText(ayahs)) {
        throw new Error(
          "Tajweed colors aren't available right now — the source returned a format this app can't safely interpret yet.",
        );
      }
      tajweedPageCache.set(pageNumber, ayahs);
      setCachedJson(`tajweed-${pageCacheKey(pageNumber)}`, ayahs);
      return ayahs;
    } catch (networkError) {
      const offlineCopy = await getCachedJson<MushafPageAyah[]>(`tajweed-${pageCacheKey(pageNumber)}`);
      if (offlineCopy) {
        tajweedPageCache.set(pageNumber, offlineCopy);
        return offlineCopy;
      }
      throw networkError;
    } finally {
      tajweedPageInFlight.delete(pageNumber);
    }
  })();

  tajweedPageInFlight.set(pageNumber, request);
  return request;
}
