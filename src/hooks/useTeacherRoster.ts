import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getRoster } from '@/services/teacherService';

export function useTeacherRoster() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['teacher', 'roster'], queryFn: getRoster });

  return {
    roster: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refresh: () => queryClient.invalidateQueries({ queryKey: ['teacher', 'roster'] }),
  };
}
