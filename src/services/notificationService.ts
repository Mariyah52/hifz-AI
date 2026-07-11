import { apiFetch } from './apiClient';
import type { AppNotification } from '@/types/notification';

export function getNotifications(): Promise<AppNotification[]> {
  return apiFetch<AppNotification[]>('/notifications');
}

export function getUnreadCount(): Promise<number> {
  return apiFetch<number>('/notifications/unread-count');
}

export function markNotificationRead(id: string): Promise<AppNotification> {
  return apiFetch<AppNotification>(`/notifications/${id}/read`, { method: 'POST' });
}

export function markAllNotificationsRead(): Promise<number> {
  return apiFetch<number>('/notifications/read-all', { method: 'POST' });
}

export function getVapidPublicKey(): Promise<{ publicKey: string | null }> {
  return apiFetch<{ publicKey: string | null }>('/notifications/vapid-public-key');
}

export function registerPushSubscription(subscription: globalThis.PushSubscription): Promise<void> {
  const json = subscription.toJSON();
  return apiFetch<void>('/notifications/push-subscription', {
    method: 'POST',
    body: {
      endpoint: json.endpoint,
      p256dhKey: json.keys?.p256dh,
      authKey: json.keys?.auth,
    },
  });
}

export function unregisterPushSubscription(endpoint: string): Promise<void> {
  return apiFetch<void>('/notifications/push-subscription', {
    method: 'DELETE',
    query: { endpoint },
  });
}
