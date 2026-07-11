import { apiFetch } from './apiClient';
import { generateClientMutationId, submitJsonOrQueue } from './offlineSyncService';
import type { Note } from '@/types/note';

export function getNotes(): Promise<Note[]> {
  return apiFetch<Note[]>('/me/notes');
}

export function deleteNote(id: string): Promise<void> {
  return apiFetch<void>(`/me/notes/${id}`, { method: 'DELETE' });
}

export interface SaveNoteInput {
  content: string;
  surahNumber?: number;
  ayahNumber?: number;
}

export async function saveNote(input: SaveNoteInput): Promise<Note> {
  const clientMutationId = generateClientMutationId();

  const outcome = await submitJsonOrQueue<Note>({
    clientMutationId,
    endpoint: '/me/notes',
    jsonBody: { ...input, clientMutationId },
  });

  if (outcome.status === 'submitted') return outcome.result;

  return {
    id: `local_${clientMutationId}`,
    content: input.content,
    surahNumber: input.surahNumber ?? null,
    ayahNumber: input.ayahNumber ?? null,
    createdAt: new Date().toISOString(),
  };
}
