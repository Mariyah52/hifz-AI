import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getAssistantMessages, sendAssistantMessage } from '@/services/assistantService';
import type { ChatMessage } from '@/types/assistant';

export function useAssistant() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['assistant', 'messages'], queryFn: getAssistantMessages });
  const [pendingUserMessage, setPendingUserMessage] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(text: string) {
    setError(null);
    setPendingUserMessage(text);
    setIsSending(true);
    try {
      await sendAssistantMessage(text);
      await queryClient.invalidateQueries({ queryKey: ['assistant', 'messages'] });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not reach the assistant.');
    } finally {
      setPendingUserMessage(null);
      setIsSending(false);
    }
  }

  const messages: ChatMessage[] = query.data ?? [];

  return {
    messages,
    isLoading: query.isLoading,
    pendingUserMessage,
    isSending,
    error,
    send,
  };
}
