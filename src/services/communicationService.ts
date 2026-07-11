import { apiFetch } from './apiClient';
import type { Announcement, ConversationSummary, DirectMessage, Homework } from '@/types/communication';

export function getConversations(): Promise<ConversationSummary[]> {
  return apiFetch<ConversationSummary[]>('/me/conversations');
}

export function startConversation(otherUserId: string): Promise<ConversationSummary> {
  return apiFetch<ConversationSummary>('/me/conversations', { method: 'POST', body: { otherUserId } });
}

export function getConversationMessages(conversationId: string): Promise<DirectMessage[]> {
  return apiFetch<DirectMessage[]>(`/me/conversations/${conversationId}/messages`);
}

export function sendConversationMessage(
  conversationId: string,
  content: string | null,
  attachment?: File | Blob | null,
): Promise<DirectMessage> {
  const form = new FormData();
  if (content) form.set('content', content);
  if (attachment) form.set('attachment', attachment, attachment instanceof File ? attachment.name : 'voice-note.webm');
  return apiFetch<DirectMessage>(`/me/conversations/${conversationId}/messages`, { method: 'POST', formData: form });
}

export function getAnnouncements(): Promise<Announcement[]> {
  return apiFetch<Announcement[]>('/me/announcements');
}

export function getHomework(): Promise<Homework[]> {
  return apiFetch<Homework[]>('/me/homework');
}

export function postTeacherAnnouncement(classId: string, title: string, content: string): Promise<Announcement> {
  return apiFetch<Announcement>('/teacher/announcements', { method: 'POST', body: { classId, title, content } });
}

export function postAdminAnnouncement(title: string, content: string): Promise<Announcement> {
  return apiFetch<Announcement>('/admin/announcements', { method: 'POST', body: { title, content } });
}

export function postHomework(classId: string, title: string, description: string, dueDate: string): Promise<Homework> {
  return apiFetch<Homework>('/teacher/homework', { method: 'POST', body: { classId, title, description, dueDate } });
}
