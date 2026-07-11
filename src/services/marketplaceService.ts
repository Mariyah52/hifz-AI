import { apiFetch } from './apiClient';
import type { InstalledMarketplaceItem, MarketplaceItem } from '@/types/marketplace';

export function getMarketplaceCatalog(): Promise<MarketplaceItem[]> {
  return apiFetch<MarketplaceItem[]>('/admin/marketplace/catalog');
}

export function getInstalledMarketplaceItems(): Promise<InstalledMarketplaceItem[]> {
  return apiFetch<InstalledMarketplaceItem[]>('/admin/marketplace/installed');
}

export function installMarketplaceItem(itemId: string): Promise<InstalledMarketplaceItem> {
  return apiFetch<InstalledMarketplaceItem>('/admin/marketplace/install', {
    method: 'POST',
    body: { itemId },
  });
}

export function uninstallMarketplaceItem(itemId: string): Promise<void> {
  return apiFetch<void>(`/admin/marketplace/installed/${itemId}`, { method: 'DELETE' });
}
