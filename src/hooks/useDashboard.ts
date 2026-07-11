import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/services/apiClient';
import { getCachedJson, setCachedJson } from '@/services/textCacheDb';
import type { DashboardSummary } from '@/types/user';

const CACHE_KEY = 'last-dashboard-summary';

/** Phase 26: same last-successful-response cache as progressAnalyticsService, so Dashboard is viewable offline. */
async function fetchDashboard(): Promise<DashboardSummary> {
  try {
    const summary = await apiFetch<DashboardSummary>('/me/dashboard');
    setCachedJson(CACHE_KEY, summary);
    return summary;
  } catch (error) {
    const cached = await getCachedJson<DashboardSummary>(CACHE_KEY);
    if (cached) return cached;
    throw error;
  }
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard,
    staleTime: 60_000,
  });
}
