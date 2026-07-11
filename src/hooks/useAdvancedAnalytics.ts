import { useQuery } from '@tanstack/react-query';
import { getAdvancedAnalytics } from '@/services/analyticsService';

export function useAdvancedAnalytics() {
  return useQuery({ queryKey: ['analytics', 'advanced'], queryFn: getAdvancedAnalytics });
}
