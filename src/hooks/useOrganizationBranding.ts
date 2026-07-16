import { useQuery } from '@tanstack/react-query';
import { useAuth } from './useAuth';
import { getOrganizationPublic, type OrganizationPublic } from '@/services/organizationService';

/**
 * Shared query for the logged-in user's organization branding (name,
 * colors, logo, welcome message). Backed by the same cache key as
 * useOrganizationTheme, so calling this from multiple components (e.g.
 * Header for the logo, useOrganizationTheme for the CSS variables)
 * doesn't trigger duplicate network requests — React Query dedupes by
 * queryKey and this one has a 60s staleTime.
 */
export function useOrganizationBranding() {
  const { user } = useAuth();
  return useQuery<OrganizationPublic>({
    queryKey: ['organization', 'public', user?.organizationSlug],
    queryFn: () => getOrganizationPublic(user!.organizationSlug),
    enabled: Boolean(user?.organizationSlug),
    staleTime: 60_000,
  });
}
