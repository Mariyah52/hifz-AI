import { useQuery } from '@tanstack/react-query';
import { getGamificationSummary } from '@/services/gamificationService';

export function useGamification() {
  return useQuery({ queryKey: ['gamification'], queryFn: getGamificationSummary });
}
