import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getNotifications, markAllNotificationsRead, markNotificationRead } from '@/services/notificationService';

export function useNotifications() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['notifications'], queryFn: getNotifications });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['notifications'] });
    queryClient.invalidateQueries({ queryKey: ['notifications', 'unread-count'] });
  }

  return {
    notifications: query.data ?? [],
    isLoading: query.isLoading,
    markRead: async (id: string) => {
      await markNotificationRead(id);
      invalidate();
    },
    markAllRead: async () => {
      await markAllNotificationsRead();
      invalidate();
    },
  };
}
