import { useQuery } from '@tanstack/react-query';
import { getDueReviews } from '@/services/reviewService';

export function useDueReviews() {
  return useQuery({ queryKey: ['reviews', 'due'], queryFn: getDueReviews });
}
