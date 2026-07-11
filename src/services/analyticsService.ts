import { apiFetch } from './apiClient';
import type { AdvancedAnalytics } from '@/types/analytics';

export function getAdvancedAnalytics(): Promise<AdvancedAnalytics> {
  return apiFetch<AdvancedAnalytics>('/me/analytics/advanced');
}
