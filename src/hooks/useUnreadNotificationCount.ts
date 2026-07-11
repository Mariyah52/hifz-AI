import { useQuery } from '@tanstack/react-query';
import { getUnreadCount } from '@/services/notificationService';

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 60_000, // light polling so the badge doesn't go stale for long
  });
}
