export type AyahMark = 'correct' | 'missed';
/** 'pending' only ever appears on a locally-synthesized offline placeholder (see testService.ts) — the backend itself only ever returns 'completed' or 'failed' since analysis runs synchronously before it responds. */
export type TestAnalysisStatus = 'completed' | 'failed' | 'pending';
export type TestMistakeType = 'missing' | 'extra' | 'substituted';

/**
 * A single recorded/transcribed word discrepancy — identical shape to
 * `PracticeMistake` (see types/practice.ts), reused structurally by
 * `MistakeList` for Test Mode's summary too.
 */
export interface TestMistake {
  mistakeType: TestMistakeType;
  ayahNumber: number | null;
  referenceWord: string | null;
  transcribedWord: string | null;
}

/**
 * One ayah's result within a test session. `mark` is AI-derived from a
 * real Whisper transcription of the session's one continuous recording,
 * word-diffed against the real reference text (see backend's
 * services/test_analysis.py) — not self-reported by the student. Same
 * word-level-only caveat as Practice Mode's analysis: this detects missing/
 * extra/substituted words, not Tajweed or pronunciation quality.
 */
export interface TestAyahResult {
  ayahNumber: number;
  mark: AyahMark;
  matchedWordCount: number;
  totalWordCount: number;
}

export interface TestSession {
  id: string;
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  completedAt: string; // ISO datetime
  results: TestAyahResult[];
  /** matchedWordCount / totalWordCount * 100, from the AI word-diff — 0 if analysis failed. */
  scorePercent: number;
  /** The one continuous recording covering the whole ayah range, if analysis succeeded. */
  audioUrl: string | null;
  analysisStatus: TestAnalysisStatus;
  analysisError: string | null;
  matchedWordCount: number;
  totalWordCount: number;
  mistakes: TestMistake[];
  /** Phase 26: true only for a locally-synthesized placeholder returned while offline. */
  isPendingSync?: boolean;
}
