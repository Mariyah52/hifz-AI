import { Link } from 'react-router-dom';
import { ChevronLeft, Check, Loader2, Store } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useMarketplace } from '@/hooks/useMarketplace';
import type { MarketplaceCategory, MarketplaceItem } from '@/types/marketplace';

const CATEGORY_LABELS: Record<MarketplaceCategory, string> = {
  question_bank: 'Question banks',
  revision_plan: 'Revision plans',
  reciter: 'Premium reciters',
  theme: 'Themes',
  plugin: 'Plugins',
};

const CATEGORY_ORDER: MarketplaceCategory[] = ['question_bank', 'revision_plan', 'reciter', 'theme', 'plugin'];

function formatPrice(priceCents: number): string {
  return priceCents === 0 ? 'Free' : `$${(priceCents / 100).toFixed(2)}`;
}

/**
 * Phase 29 — admin-only. Institute add-ons: question banks, revision
 * plans, premium reciters, themes, plugins. Premium prices are shown for
 * reference only — there's no real payment flow behind "Install", the
 * same billing scope-cut this app made in Phase 18. Installing a theme
 * is the one category with a real, visible effect: it updates the
 * organization's branding color immediately (see `useMarketplace`).
 */
export function MarketplacePage() {
  const { catalog, installedItemIds, isLoading, pendingId, install, uninstall } = useMarketplace();

  const grouped = catalog.reduce<Partial<Record<MarketplaceCategory, MarketplaceItem[]>>>((acc, item) => {
    (acc[item.category] ??= []).push(item);
    return acc;
  }, {});

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/admin"
          aria-label="Back to Admin"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Admin</p>
          <h1 className="heading-section flex items-center gap-2">
            <Store size={18} /> Marketplace
          </h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-5">
        <Card className="bg-sage/40 border-none">
          <p className="font-body text-xs text-ink-soft">
            Add-ons your institution can install. Premium prices are shown for reference only —
            there's no real payment flow here, the same scope cut this app made for billing back in
            Phase 18: installing anything, free or premium, is instant and doesn't charge a card.
          </p>
        </Card>

        {isLoading && <p className="text-center text-ink-soft font-body text-sm py-8">Loading…</p>}

        {CATEGORY_ORDER.filter((category) => grouped[category]?.length).map((category) => (
          <section key={category}>
            <h3 className="heading-subsection mb-3">{CATEGORY_LABELS[category]}</h3>
            <div className="flex flex-col gap-2">
              {grouped[category]!.map((item) => {
                const isInstalled = installedItemIds.has(item.id);
                const isPending = pendingId === item.id;
                return (
                  <Card key={item.id} className="flex items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-body font-semibold text-ink text-sm truncate">{item.name}</p>
                        <span className="font-mono text-[10px] text-[#8a6218] bg-gold/15 rounded-full px-2 py-0.5 shrink-0">
                          {formatPrice(item.priceCents)}
                        </span>
                      </div>
                      <p className="font-body text-xs text-ink-soft mt-0.5">{item.description}</p>
                    </div>
                    <button
                      onClick={() => (isInstalled ? uninstall(item.id) : install(item.id))}
                      disabled={isPending}
                      className={`shrink-0 rounded-full font-body font-semibold text-xs px-4 py-2 transition-colors disabled:opacity-50 ${
                        isInstalled ? 'bg-sage text-ink-soft hover:bg-[#d8dfcd]' : 'bg-teal text-paper hover:bg-teal-dark'
                      }`}
                    >
                      {isPending ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : isInstalled ? (
                        <span className="flex items-center gap-1">
                          <Check size={13} /> Installed
                        </span>
                      ) : (
                        'Install'
                      )}
                    </button>
                  </Card>
                );
              })}
            </div>
          </section>
        ))}
      </main>
    </>
  );
}
