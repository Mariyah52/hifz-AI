import surahs from '@/data/surahs.json';
import juzBoundaries from '@/data/juzBoundaries.json';
import type { AyahRef, JuzBoundary, Surah } from '@/types/quran';

const SURAHS = surahs as Surah[];
const JUZ_BOUNDARIES = juzBoundaries as JuzBoundary[];

export function getAllSurahs(): Surah[] {
  return SURAHS;
}

export function getSurahByNumber(number: number): Surah | undefined {
  return SURAHS.find((s) => s.number === number);
}

/** Surahs whose ayahs fall (at least partially) within the given juz. */
export function getSurahsInJuz(juz: number): Surah[] {
  return SURAHS.filter((s) => s.juz.includes(juz));
}

/**
 * Absolute position of an ayah across the whole Quran (1-6236), derived by
 * summing ayahCounts of preceding surahs. Throws on an out-of-range ayah so
 * bad references fail loudly instead of silently producing a wrong number.
 */
export function getGlobalAyahNumber(surahNumber: number, ayahNumber: number): number {
  const surah = getSurahByNumber(surahNumber);
  if (!surah) throw new Error(`Unknown surah number: ${surahNumber}`);
  if (ayahNumber < 1 || ayahNumber > surah.ayahCount) {
    throw new Error(`Ayah ${ayahNumber} out of range for surah ${surahNumber} (1-${surah.ayahCount})`);
  }
  let offset = 0;
  for (const s of SURAHS) {
    if (s.number === surahNumber) break;
    offset += s.ayahCount;
  }
  return offset + ayahNumber;
}

/** Reverse of getGlobalAyahNumber: absolute position (1-6236) -> surah/ayah. */
export function getSurahAndAyahFromGlobal(globalAyahNumber: number): { surahNumber: number; ayahNumber: number } {
  if (globalAyahNumber < 1 || globalAyahNumber > 6236) {
    throw new Error(`globalAyahNumber out of range: ${globalAyahNumber} (1-6236)`);
  }
  let remaining = globalAyahNumber;
  for (const s of SURAHS) {
    if (remaining <= s.ayahCount) {
      return { surahNumber: s.number, ayahNumber: remaining };
    }
    remaining -= s.ayahCount;
  }
  throw new Error(`Unreachable: globalAyahNumber ${globalAyahNumber} not resolved`);
}

function isWithinBoundary(surahNumber: number, ayahNumber: number, b: JuzBoundary): boolean {
  const afterStart =
    surahNumber > b.startSurah || (surahNumber === b.startSurah && ayahNumber >= b.startAyah);
  const beforeEnd = surahNumber < b.endSurah || (surahNumber === b.endSurah && ayahNumber <= b.endAyah);
  return afterStart && beforeEnd;
}

/** Which of the 30 juz a given ayah belongs to, using the verified boundary table. */
export function getJuzForAyah(surahNumber: number, ayahNumber: number): number {
  const match = JUZ_BOUNDARIES.find((b) => isWithinBoundary(surahNumber, ayahNumber, b));
  if (!match) {
    throw new Error(`No juz boundary matched surah ${surahNumber}, ayah ${ayahNumber}`);
  }
  return match.juz;
}

export function getJuzBoundaries(): JuzBoundary[] {
  return JUZ_BOUNDARIES;
}

/**
 * Full ayah reference. `page`/`hizb`/`rub` are intentionally left undefined —
 * see the comment on AyahRef in types/quran.ts for why, and what needs to
 * land before they can be populated.
 */
export function getAyahRef(surahNumber: number, ayahNumber: number): AyahRef {
  return {
    surahNumber,
    ayahNumber,
    globalAyahNumber: getGlobalAyahNumber(surahNumber, ayahNumber),
    juz: getJuzForAyah(surahNumber, ayahNumber),
  };
}
