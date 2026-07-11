import { useQueries, useQueryClient } from '@tanstack/react-query';
import { getAnalytics, getAuditLog, getClasses, getMyOrganization, getTeachers } from '@/services/adminService';

export function useAdminOverview() {
  const queryClient = useQueryClient();

  const [teachersQuery, classesQuery, analyticsQuery, auditLogQuery, organizationQuery] = useQueries({
    queries: [
      { queryKey: ['admin', 'teachers'], queryFn: getTeachers },
      { queryKey: ['admin', 'classes'], queryFn: getClasses },
      { queryKey: ['admin', 'analytics'], queryFn: getAnalytics },
      { queryKey: ['admin', 'audit-log'], queryFn: getAuditLog },
      { queryKey: ['admin', 'organization'], queryFn: getMyOrganization },
    ],
  });

  return {
    teachers: teachersQuery.data ?? [],
    classes: classesQuery.data ?? [],
    analytics: analyticsQuery.data,
    auditLog: auditLogQuery.data ?? [],
    organization: organizationQuery.data,
    isLoading: teachersQuery.isLoading || classesQuery.isLoading || analyticsQuery.isLoading,
    refresh: () => queryClient.invalidateQueries({ queryKey: ['admin'] }),
  };
}
