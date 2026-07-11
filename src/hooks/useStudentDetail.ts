import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getStudentDetail } from '@/services/teacherService';

export function useStudentDetail(studentId: string) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['teacher', 'student', studentId],
    queryFn: () => getStudentDetail(studentId),
    enabled: studentId.length > 0,
  });

  return {
    detail: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refresh: () => queryClient.invalidateQueries({ queryKey: ['teacher', 'student', studentId] }),
  };
}
