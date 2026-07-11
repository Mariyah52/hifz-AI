import { useMemo } from 'react';
import { getAllSurahs, getAyahRef, getSurahByNumber, getSurahsInJuz } from '@/services/quranService';
import type { AyahRef, Surah } from '@/types/quran';

/** All 114 surahs, memoized for the lifetime of the component. */
export function useSurahList(): Surah[] {
  return useMemo(() => getAllSurahs(), []);
}

export function useSurah(surahNumber: number): Surah | undefined {
  return useMemo(() => getSurahByNumber(surahNumber), [surahNumber]);
}

export function useSurahsInJuz(juz: number): Surah[] {
  return useMemo(() => getSurahsInJuz(juz), [juz]);
}

/** Full ayah reference (global number + juz). Throws for an invalid ayah. */
export function useAyahRef(surahNumber: number, ayahNumber: number): AyahRef {
  return useMemo(() => getAyahRef(surahNumber, ayahNumber), [surahNumber, ayahNumber]);
}
