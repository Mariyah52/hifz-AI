export interface AppNotification {
  id: string;
  notificationType: string;
  title: string;
  body: string;
  relatedId: string | null;
  isRead: boolean;
  createdAt: string; // ISO datetime
}
