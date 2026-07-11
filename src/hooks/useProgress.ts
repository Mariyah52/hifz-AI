import { useQuery } from '@tanstack/react-query';
import { getProgressSummary } from '@/services/progressAnalyticsService';

export function useProgress() {
  return useQuery({ queryKey: ['progress'], queryFn: getProgressSummary });
}
