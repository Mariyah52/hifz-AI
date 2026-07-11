import { useQuery } from '@tanstack/react-query';
import { getLeaderboard } from '@/services/gamificationService';
import type { LeaderboardScope } from '@/types/gamification';

export function useLeaderboard(scope: LeaderboardScope) {
  return useQuery({ queryKey: ['leaderboard', scope], queryFn: () => getLeaderboard(scope) });
}
