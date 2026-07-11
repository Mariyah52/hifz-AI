import type { Sabaq } from './lesson';
import type { PracticeAttempt } from './practice';
import type { TestSession } from './test';

/** Roster-list view of a student — enough for the teacher's overview screen. */
export interface Student {
  id: string;
  /** The underlying account id — distinct from `id` (the student *profile* id). Use this, not `id`, for anything that talks to a user (e.g. messaging). */
  userId: string;
  name: string;
  classId: string;
  currentStreak: number;
  todaysSabaq: Sabaq | null;
}

export interface TeacherFeedback {
  id: string;
  studentId: string;
  note: string;
  createdAt: string; // ISO datetime
}

/**
 * Full detail view for one student. Reuses PracticeAttempt/TestSession as-is
 * (same shapes the student's own Practice/Test pages use) rather than
 * inventing parallel teacher-side types — a teacher reviewing a student's
 * history should see the exact same record shape the student sees.
 */
export interface StudentDetail extends Student {
  recentPracticeAttempts: PracticeAttempt[];
  recentTestSessions: TestSession[];
  feedback: TeacherFeedback[];
}
