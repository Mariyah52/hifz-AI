import { apiFetch } from './apiClient';
import type { AdminAnalytics, AuditLogEntry, ClassSummary, Teacher } from '@/types/admin';
import type { OrganizationAdmin, UpdateOrganizationRequest } from '@/types/organization';

/**
 * Real backend calls now — Phase 9's `mockTeachers.ts` roster is gone;
 * these hit `backend/app/routers/admin.py`, which aggregates real
 * teachers/classes/students/feedback/assignments from Postgres.
 */
export function getTeachers(): Promise<Teacher[]> {
  return apiFetch<Teacher[]>('/admin/teachers');
}

export function getClasses(): Promise<ClassSummary[]> {
  return apiFetch<ClassSummary[]>('/admin/classes');
}

export function getAnalytics(): Promise<AdminAnalytics> {
  return apiFetch<AdminAnalytics>('/admin/analytics');
}

/** Phase 17 — the real security audit trail (logins, lockouts, token activity). */
export function getAuditLog(): Promise<AuditLogEntry[]> {
  return apiFetch<AuditLogEntry[]>('/admin/audit-log', { query: { limit: 20 } });
}

/** Phase 18 — this admin's own organization, including real plan-usage numbers. */
export function getMyOrganization(): Promise<OrganizationAdmin> {
  return apiFetch<OrganizationAdmin>('/admin/organization');
}

export function updateMyOrganization(payload: UpdateOrganizationRequest): Promise<OrganizationAdmin> {
  return apiFetch<OrganizationAdmin>('/admin/organization', { method: 'PATCH', body: payload });
}
