export type AttemptStatus = 'recorded' | 'analyzed';
export type AnalysisStatus = 'not_analyzed' | 'completed' | 'failed';
export type MistakeType = 'missing' | 'extra' | 'substituted';

/**
 * A single recorded/transcribed word discrepancy between what the ayah
 * actually says and what Whisper transcribed from the recording.
 * `ayahNumber` is null only for 'extra' (a recited word with no
 * reference counterpart to attribute it to).
 */
export interface PracticeMistake {
  mistakeType: MistakeType;
  ayahNumber: number | null;
  referenceWord: string | null;
  transcribedWord: string | null;
}

/**
 * A single practice recording. Phase 14 added real, on-demand recitation
 * analysis (`analysisStatus` starts 'not_analyzed' until the student taps
 * "Analyze recitation") — word-level transcription diffing, not
 * pronunciation/fluency/Tajweed scoring. This app still never reports a
 * `pronunciationScore`/`fluencyScore`-style number it can't actually
 * compute; there's deliberately no such field on this type at all.
 */
export interface PracticeAttempt {
  id: string;
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  recordedAt: string; // ISO datetime
  durationSeconds: number;
  status: AttemptStatus;
  pace: PaceEstimate;
  /** Set only if the recording was actually uploaded and saved server-side (Phase 10). */
  audioUrl?: string | null;

  analysisStatus: AnalysisStatus;
  analysisError?: string | null;
  transcribedText?: string | null;
  matchedWordCount?: number | null;
  totalWordCount?: number | null;
  mistakes: PracticeMistake[];

  /**
   * Phase 26: true only for a locally-synthesized placeholder returned
   * while offline — this attempt was queued, not yet accepted by the
   * server, and its `id` isn't a real server id. Never set on a real
   * API response.
   */
  isPendingSync?: boolean;
}

/**
 * A local, non-AI pace signal: how the recording's duration compares to a
 * rough expected range for the ayah count, based on typical tarteel pace.
 * This is NOT recitation analysis — it can't see pronunciation, fluency, or
 * mistakes. It exists only so Practice Mode has *something* useful before
 * Phase 10's real scoring lands, without pretending to be more than it is.
 */
export interface PaceEstimate {
  expectedSecondsRange: [number, number];
  actualSeconds: number;
  withinExpectedRange: boolean;
}
