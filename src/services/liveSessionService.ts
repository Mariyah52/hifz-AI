import { apiFetch } from './apiClient';
import type { LiveSession, LiveSessionReport } from '@/types/liveSession';

export interface TeacherClass {
  id: string;
  name: string;
}

export function getMyClasses(): Promise<TeacherClass[]> {
  return apiFetch<TeacherClass[]>('/teacher/classes');
}

export function startLiveSession(classId: string): Promise<LiveSession> {
  return apiFetch<LiveSession>('/teacher/live-sessions', { method: 'POST', body: { classId } });
}

export function getMyActiveTeacherSession(): Promise<LiveSession | null> {
  return apiFetch<LiveSession | null>('/teacher/live-sessions/active');
}

export function endLiveSession(sessionId: string): Promise<LiveSessionReport> {
  return apiFetch<LiveSessionReport>(`/teacher/live-sessions/${sessionId}/end`, { method: 'POST' });
}

export function getLiveSessionReport(sessionId: string): Promise<LiveSessionReport> {
  return apiFetch<LiveSessionReport>(`/teacher/live-sessions/${sessionId}/report`);
}

export function getMyClassActiveSession(): Promise<LiveSession | null> {
  return apiFetch<LiveSession | null>('/me/live-sessions/active');
}
