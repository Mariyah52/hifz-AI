import type { Student } from './teacher';

export interface Teacher {
  id: string;
  name: string;
  classIds: string[];
}

export interface ClassSummary {
  id: string;
  name: string;
  teacherName: string | null;
  studentCount: number;
  averageStreak: number;
}

/**
 * Institution-wide numbers. See `adminService.ts` for exactly which parts
 * of this are real (persisted feedback/assignments) versus mock (the
 * roster itself) — same "mock now, swap later" split as the Teacher Portal,
 * just aggregated up a level.
 */
export interface AdminAnalytics {
  totalStudents: number;
  totalTeachers: number;
  totalClasses: number;
  totalFeedbackGiven: number;
  totalSabaqsAssigned: number;
  averageTestScore: number | null;
  studentsNeedingAttention: Student[];
}

/** The security audit trail from Phase 17 — real events, not reconstructed. */
export interface AuditLogEntry {
  id: string;
  userEmail: string | null;
  action: string;
  ipAddress: string | null;
  detail: string | null;
  createdAt: string;
}
