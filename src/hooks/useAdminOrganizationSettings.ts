import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { getMyOrganization, updateMyOrganization } from '@/services/adminService';
import { useAuth } from './useAuth';
import type { UpdateOrganizationRequest } from '@/types/organization';

/**
 * Same shape as useMarketplace's install/uninstall: one query, one async
 * mutation-like function, a pending flag. Invalidates both the admin
 * dashboard's organization query AND the public branding query (used by
 * Header/useOrganizationTheme) so a saved logo/color shows up immediately
 * instead of waiting for the public query's 60s staleTime to lapse — the
 * same gap useMarketplace's install() still has today.
 */
export function useAdminOrganizationSettings() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [isSaving, setIsSaving] = useState(false);

  const organizationQuery = useQuery({
    queryKey: ['admin', 'organization'],
    queryFn: getMyOrganization,
  });

  async function save(payload: UpdateOrganizationRequest) {
    setIsSaving(true);
    try {
      await updateMyOrganization(payload);
      await queryClient.invalidateQueries({ queryKey: ['admin', 'organization'] });
      await queryClient.invalidateQueries({
        queryKey: ['organization', 'public', user?.organizationSlug],
      });
    } finally {
      setIsSaving(false);
    }
  }

  return {
    organization: organizationQuery.data,
    isLoading: organizationQuery.isLoading,
    isSaving,
    save,
  };
}
