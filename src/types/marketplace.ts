export type MarketplaceCategory = 'question_bank' | 'revision_plan' | 'reciter' | 'theme' | 'plugin';

export interface MarketplaceItem {
  id: string;
  category: MarketplaceCategory;
  name: string;
  description: string;
  priceCents: number;
  isPremium: boolean;
}

export interface InstalledMarketplaceItem {
  id: string;
  item: MarketplaceItem;
  installedAt: string;
}
