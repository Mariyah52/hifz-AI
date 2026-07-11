import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getChildOverview, getChildren } from '@/services/parentService';

/**
 * A parent can be linked to more than one child now (real `ParentChildLink`
 * rows, not Phase 8's single hardcoded id) — this hook shows the first
 * linked child by default. A multi-child switcher UI is a reasonable next
 * step but out of scope for this pass; `children` is returned so one could
 * be added without changing this hook's shape.
 */
export function useChildOverview() {
  const queryClient = useQueryClient();

  const childrenQuery = useQuery({ queryKey: ['parent', 'children'], queryFn: getChildren });
  const firstChildId = childrenQuery.data?.[0]?.id;

  const overviewQuery = useQuery({
    queryKey: ['parent', 'overview', firstChildId],
    queryFn: () => getChildOverview(firstChildId!),
    enabled: !!firstChildId,
  });

  return {
    children: childrenQuery.data ?? [],
    overview: overviewQuery.data,
    isLoading: childrenQuery.isLoading || overviewQuery.isLoading,
    refresh: () => {
      queryClient.invalidateQueries({ queryKey: ['parent'] });
    },
  };
}
