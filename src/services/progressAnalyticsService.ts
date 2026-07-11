import { apiFetch } from './apiClient';
import { getCachedJson, setCachedJson } from './textCacheDb';
import type { ProgressSummary } from '@/types/progress';

const CACHE_KEY = 'last-progress-summary';

/**
 * Real backend call now — this used to recompute everything client-side
 * from `localStorage` (this file had all the aggregation logic: distinct
 * correct ayahs, daily buckets, etc). That logic now lives once, server
 * side, in `backend/app/services/progress_analytics.py`, computed from
 * the same Postgres rows every portal reads — nothing to keep in sync
 * across devices/browsers anymore.
 *
 * Phase 26: the last successful response is also cached (same IndexedDB
 * store the Quran text caching uses), so Progress is viewable — read-only,
 * as of the last time it synced — while offline, rather than just erroring.
 */
export async function getProgressSummary(): Promise<ProgressSummary> {
  try {
    const summary = await apiFetch<ProgressSummary>('/me/progress');
    setCachedJson(CACHE_KEY, summary);
    return summary;
  } catch (error) {
    const cached = await getCachedJson<ProgressSummary>(CACHE_KEY);
    if (cached) return cached;
    throw error;
  }
}
