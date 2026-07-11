import { apiFetch } from './apiClient';
import type { DueReview } from '@/types/review';

/**
 * Real spaced-repetition scheduling, computed server-side
 * (`backend/app/services/spaced_repetition.py`) from actual Test Mode
 * results — not a client-side estimate. This is the same list the
 * Dashboard's Sabqi/Manzil slots are drawn two items from.
 */
export function getDueReviews(): Promise<DueReview[]> {
  return apiFetch<DueReview[]>('/me/reviews/due');
}
