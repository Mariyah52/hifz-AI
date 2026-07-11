import { apiFetch } from './apiClient';
import type { Sabaq } from '@/types/lesson';
import type { Student, StudentDetail, TeacherFeedback } from '@/types/teacher';
import type { Certificate } from '@/types/certificate';

/**
 * Real backend calls now — this used to read/write `localStorage` on top
 * of the mock roster in `data/mockStudents.ts` (Phase 7). The roster,
 * assignments, and feedback are all real rows in Postgres now, scoped to
 * whichever teacher is logged in (see `backend/app/routers/teacher.py`).
 */
export function getRoster(): Promise<Student[]> {
  return apiFetch<Student[]>('/teacher/roster');
}

export function getStudentDetail(studentId: string): Promise<StudentDetail> {
  return apiFetch<StudentDetail>(`/teacher/students/${studentId}`);
}

export function assignSabaq(
  studentId: string,
  surahNumber: number,
  surahName: string,
  fromAyah: number,
  toAyah: number,
): Promise<Sabaq> {
  return apiFetch<Sabaq>(`/teacher/students/${studentId}/sabaq`, {
    method: 'POST',
    body: { surahNumber, surahName, fromAyah, toAyah },
  });
}

export function addFeedback(studentId: string, note: string): Promise<TeacherFeedback> {
  return apiFetch<TeacherFeedback>(`/teacher/students/${studentId}/feedback`, {
    method: 'POST',
    body: { note },
  });
}

/** Phase 27 — attendance/competition certificates need a teacher's judgment call, unlike auto-detected surah/juz completion. */
export function issueCertificate(
  studentId: string,
  type: 'attendance' | 'competition',
  title: string,
  detail: string,
): Promise<Certificate> {
  return apiFetch<Certificate>(`/teacher/students/${studentId}/certificates`, {
    method: 'POST',
    body: { type, title, detail },
  });
}
