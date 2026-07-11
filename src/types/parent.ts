import type { StreakInfo } from './user';
import type { Sabaq } from './lesson';
import type { ProgressSummary } from './progress';
import type { TeacherFeedback } from './teacher';

/**
 * Everything a parent sees for their (one) linked child. Note that
 * `progress` and `streak` are real — the same recorded Practice/Test
 * activity and streak state the Progress page reads, not invented for this
 * portal. `todaysSabaq`/`recentSabaqs` are still the Phase 1 mock dashboard
 * values (same "mock now, swap later" pattern), and `feedback` is real
 * teacher feedback for the linked student record. See `parentService.ts`
 * for how these are assembled and why.
 */
export interface ChildOverview {
  studentId: string;
  name: string;
  classId: string;
  streak: StreakInfo;
  todaysSabaq: Sabaq | null;
  recentSabaqs: Sabaq[];
  progress: ProgressSummary;
  feedback: TeacherFeedback[];
}
