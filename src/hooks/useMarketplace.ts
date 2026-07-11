import { useQueries, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import {
  getInstalledMarketplaceItems,
  getMarketplaceCatalog,
  installMarketplaceItem,
  uninstallMarketplaceItem,
} from '@/services/marketplaceService';

/**
 * Mirrors `useAdminOverview`'s `useQueries` shape (Phase 18) — catalog and
 * installed-items lists are fetched in parallel, invalidated together
 * after any install/uninstall so both stay in sync with one call.
 */
export function useMarketplace() {
  const queryClient = useQueryClient();
  const [pendingId, setPendingId] = useState<string | null>(null);

  const [catalogQuery, installedQuery] = useQueries({
    queries: [
      { queryKey: ['marketplace', 'catalog'], queryFn: getMarketplaceCatalog },
      { queryKey: ['marketplace', 'installed'], queryFn: getInstalledMarketplaceItems },
    ],
  });

  const installedItemIds = new Set((installedQuery.data ?? []).map((installed) => installed.item.id));

  async function install(itemId: string) {
    setPendingId(itemId);
    try {
      await installMarketplaceItem(itemId);
      await queryClient.invalidateQueries({ queryKey: ['marketplace'] });
      // Installing a theme can change the org's primaryColor — refresh that too.
      await queryClient.invalidateQueries({ queryKey: ['admin', 'organization'] });
    } finally {
      setPendingId(null);
    }
  }

  async function uninstall(itemId: string) {
    setPendingId(itemId);
    try {
      await uninstallMarketplaceItem(itemId);
      await queryClient.invalidateQueries({ queryKey: ['marketplace'] });
    } finally {
      setPendingId(null);
    }
  }

  return {
    catalog: catalogQuery.data ?? [],
    installedItemIds,
    isLoading: catalogQuery.isLoading || installedQuery.isLoading,
    pendingId,
    install,
    uninstall,
  };
}
