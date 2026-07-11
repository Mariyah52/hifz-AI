export type UserRole = 'student' | 'teacher' | 'parent' | 'admin';

export interface User {
  id: string;
  name: string;
  role: UserRole;
  avatarUrl?: string;
  /** Class/halaqah the student belongs to, if any */
  classId?: string;
}

export interface StreakInfo {
  currentStreak: number; // consecutive days
  longestStreak: number;
  lastActiveDate: string | null; // ISO date, or null if never active
  freezesAvailable: number;
}

export interface DashboardSummary {
  user: User;
  streak: StreakInfo;
  todaysSabaq: import('./lesson').Sabaq | null;
  todaysSabqi: import('./lesson').SabqiReview | null;
  todaysManzil: import('./lesson').ManzilReview | null;
  recentSabaqs: import('./lesson').Sabaq[];
  juzProgress: number; // 0-30, fractional allowed
  overallAccuracy: number; // 0-100
}
