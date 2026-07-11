export type LessonMode = 'learn' | 'practice' | 'test';

export type LessonStatus = 'not_started' | 'in_progress' | 'completed';

/** Repeat strategy while listening/reciting in Learn mode. */
export type RepeatMode = 'single' | 'range' | 'continuous';

/**
 * A "Sabaq" is the day's assigned portion of memorization —
 * the core teaching unit in traditional hifz curricula.
 */
export interface Sabaq {
  id: string;
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  assignedDate: string; // ISO date
  status: LessonStatus;
  /** 0-100, set by scoring (stubbed until AI integration in Phase 4/10) */
  score?: number;
}

/**
 * "Sabqi" — recent review of a lesson learned in the last several days,
 * reinforcing it before it graduates to Manzil rotation.
 */
export interface SabqiReview {
  id: string;
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  status: LessonStatus;
  score?: number;
}

/**
 * "Manzil" — distant/rotational review of an older completed Sabaq, done
 * on a longer cycle than Sabqi to keep older memorization from fading.
 *
 * Through Phase 12 this was juz-shaped (a rotating older *juz*, picked by
 * a heuristic with no real scheduling behind it). As of Phase 13 it's a
 * real SM-2-scheduled due review instead — same shape as SabqiReview,
 * distinguished from it only by which due item the backend's spaced-
 * repetition engine picked (see `backend/app/services/spaced_repetition.py`).
 * The UI still shows a "Juz N" label for this row — computed client-side
 * from `surahNumber`/`fromAyah` via `quranService.getJuzForAyah` (already
 * verified in Phase 2), not carried in this type.
 */
export interface ManzilReview {
  id: string;
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  status: LessonStatus;
  score?: number;
}

export interface LessonProgress {
  sabaqId: string;
  mode: LessonMode;
  ayahsCompleted: number;
  totalAyahs: number;
  lastActivityAt: string; // ISO datetime
}
