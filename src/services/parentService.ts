import { apiFetch } from './apiClient';
import type { ChildOverview } from '@/types/parent';
import type { Student } from '@/types/teacher';

/**
 * Real backend calls now — Phase 8's `LINKED_CHILD_STUDENT_ID` hack (a
 * hardcoded pointer at the mock `stu_1` record) is gone. The backend's
 * `ParentChildLink` table is the real relationship, set up at
 * registration (see `RegisterRequest.childStudentId`) or by an admin.
 */
export function getChildren(): Promise<Student[]> {
  return apiFetch<Student[]>('/parent/children');
}

export function getChildOverview(studentId: string): Promise<ChildOverview> {
  return apiFetch<ChildOverview>(`/parent/children/${studentId}/overview`);
}
