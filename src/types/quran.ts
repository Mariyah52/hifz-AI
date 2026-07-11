/** Revelation place of a surah. */
export type RevelationType = 'meccan' | 'medinan';

/** Metadata for one of the 114 surahs. Full dataset lands in Phase 2. */
export interface Surah {
  number: number; // 1-114
  name: string; // English transliteration, e.g. "Al-Baqarah"
  arabicName: string; // e.g. "البقرة"
  englishTranslation: string; // e.g. "The Cow"
  ayahCount: number;
  revelationType: RevelationType;
  /** Juz numbers this surah spans, e.g. [1, 2, 3] */
  juz: number[];
}

/**
 * A single ayah reference, independent of translation/recitation content.
 *
 * `page`, `hizb`, and `rub` are left optional deliberately: computing them
 * correctly requires a verified per-ayah boundary table (the standard
 * 604-page Madani mushaf pagination + hizb/rub quarter markers), which is
 * NOT something to hand-derive from memory for a religious text. Juz is
 * safe to compute now because its 30 boundaries were verified against
 * multiple sources. Page/hizb/rub should be backfilled from a vetted
 * dataset (e.g. per-ayah `page`/`hizbQuarter` fields from a Quran API/
 * corpus) in a follow-up pass, without changing this type's shape.
 */
export interface AyahRef {
  surahNumber: number;
  ayahNumber: number; // 1-indexed within the surah
  /** Absolute position across the whole Quran, 1-6236 */
  globalAyahNumber: number;
  juz: number; // 1-30 — computed from the verified juzBoundaries table
  page?: number; // 1-604, Madani mushaf — not yet populated
  hizb?: number; // 1-60 (half-juz) — not yet populated
  rub?: number; // 1-240 (quarter-hizb) — not yet populated
}

/** One of the 30 verified juz boundaries, expressed as surah:ayah start/end. */
export interface JuzBoundary {
  juz: number;
  startSurah: number;
  startAyah: number;
  endSurah: number;
  endAyah: number;
}

/**
 * Ayah text fetched at runtime from a verified Quran text API — never
 * hand-typed. Quran text has zero tolerance for transcription error, so
 * this app never bundles scripture as static data; quranTextService fetches
 * it live and caches per surah.
 */
export interface AyahText {
  surahNumber: number;
  ayahNumber: number;
  text: string;
}

/** Reciter identifiers. Al-Husary is the only reciter wired up in Phase 3. */
export type ReciterId = 'husary';

export interface Reciter {
  id: ReciterId;
  name: string;
  arabicName: string;
}

/**
 * One ayah as it appears on a specific Mushaf page — Phase 12. Distinct
 * from `AyahText` (Learn Mode's per-surah fetch): this comes from the
 * same live, verified API but queried *by page*
 * (`/page/{n}/quran-uthmani`), which is also the only place this app
 * gets real page/hizb/sajda data from — see `quranPageService.ts` for
 * why that data is fetched live rather than hand-typed into a static
 * table, same principle as `AyahText` above.
 */
export interface MushafPageAyah {
  surahNumber: number;
  surahName: string;
  ayahNumber: number;
  text: string;
  hizbQuarter?: number; // 1-240, when the API provides it
  isSajda: boolean;
}

export interface MushafPage {
  pageNumber: number; // 1-604
  ayahs: MushafPageAyah[];
}
