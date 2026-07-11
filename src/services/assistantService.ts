import { apiFetch } from './apiClient';
import type { ChatMessage } from '@/types/assistant';

export function getAssistantMessages(): Promise<ChatMessage[]> {
  return apiFetch<ChatMessage[]>('/me/assistant/messages');
}

export function sendAssistantMessage(message: string): Promise<ChatMessage> {
  return apiFetch<ChatMessage>('/me/assistant/messages', { method: 'POST', body: { message } });
}
