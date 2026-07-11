export type ChatRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  /** Which real backend tools the assistant called to ground this reply — empty for general-knowledge replies. */
  toolsCalled: string[];
  createdAt: string;
}
