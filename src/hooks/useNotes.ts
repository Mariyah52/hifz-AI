import { useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteNote, getNotes, saveNote, type SaveNoteInput } from '@/services/noteService';
import type { Note } from '@/types/note';

export function useNotes() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['notes'], queryFn: getNotes });

  return {
    notes: query.data ?? [],
    isLoading: query.isLoading,
    addNote: async (input: SaveNoteInput) => {
      // Update the cache directly with whatever saveNote returns (the real
      // saved note, or a locally-queued placeholder) instead of
      // invalidating+refetching — a refetch would just fail while offline,
      // which is exactly the case this needs to work in.
      const note = await saveNote(input);
      queryClient.setQueryData<Note[]>(['notes'], (old) => [note, ...(old ?? [])]);
    },
    removeNote: async (id: string) => {
      // A note still queued offline has a client-only 'local_' id — there's
      // nothing on the server yet to delete, so just drop it from the view.
      if (!id.startsWith('local_')) await deleteNote(id);
      queryClient.setQueryData<Note[]>(['notes'], (old) => (old ?? []).filter((n) => n.id !== id));
    },
  };
}
