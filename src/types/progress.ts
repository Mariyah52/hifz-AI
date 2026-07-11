export interface DailyActivity {
  date: string; // ISO date (day)
  practiceCount: number;
  testCount: number;
  /** Average self-reported test score that day, or null if no tests run. */
  testAverageScore: number | null;
}

/**
 * Everything here is derived from real recorded activity — Test Mode
 * sessions, Practice Mode attempts, and the streak service — never
 * fabricated for display. In particular:
 *
 * `memorizedAyahCount` is a proxy, not a certified fact: it's the count of
 * distinct ayahs the student has self-marked "correct" in at least one Test
 * Mode session. That's a real, defensible signal from actual usage, but
 * it's still a self-report, not AI-verified mastery — the UI should say so.
 */
export interface ProgressSummary {
  memorizedAyahCount: number;
  totalAyahCount: number;
  completionPercent: number;
  currentStreak: number;
  longestStreak: number;
  totalPracticeAttempts: number;
  totalTestSessions: number;
  overallAverageTestScore: number | null;
  weeklyActivity: DailyActivity[]; // last 7 days
  monthlyActivity: DailyActivity[]; // last 30 days
}
