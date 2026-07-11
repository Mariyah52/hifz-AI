export interface WeakSurah {
  surahNumber: number;
  surahName: string;
  accuracy: number;
  attemptCount: number;
}

export interface WeakJuz {
  juz: number;
  accuracy: number;
  attemptCount: number;
}

export interface WeakPage {
  page: number;
  accuracy: number;
  attemptCount: number;
}

export interface ForgottenAyah {
  surahNumber: number;
  surahName: string;
  ayahNumber: number;
  accuracy: number;
  missedCount: number;
  attemptCount: number;
}

/**
 * All computed from real recorded activity. `confidenceScore` is a
 * documented weighted blend (0.6 * retentionRate + 0.4 * overallAccuracy)
 * of two real measured signals, not a trained model's output — see the
 * backend's services/analytics.py for the exact formula.
 */
export interface AdvancedAnalytics {
  overallAccuracy: number;
  weakestSurah: WeakSurah | null;
  weakestJuz: WeakJuz | null;
  weakestPages: WeakPage[];
  mostForgottenAyah: ForgottenAyah | null;
  longestStreak: number;
  averageRevisionTimeSeconds: number | null;
  retentionRate: number | null;
  confidenceScore: number | null;
}
