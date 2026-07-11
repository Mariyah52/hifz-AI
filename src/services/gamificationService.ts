import { apiFetch } from './apiClient';
import type { GamificationSummary, LeaderboardEntry, LeaderboardScope } from '@/types/gamification';

export function getGamificationSummary(): Promise<GamificationSummary> {
  return apiFetch<GamificationSummary>('/me/gamification');
}

export function getLeaderboard(scope: LeaderboardScope): Promise<LeaderboardEntry[]> {
  return apiFetch<LeaderboardEntry[]>('/me/leaderboard', { query: { scope } });
}
