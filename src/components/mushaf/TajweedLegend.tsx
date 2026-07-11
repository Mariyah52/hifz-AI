import { getTajweedLegend } from '@/utils/tajweed';

/** Small color-key card explaining what each tajweed color means — shown whenever tajweed coloring is on. */
export function TajweedLegend() {
  const legend = getTajweedLegend();

  return (
    <div className="rounded-card bg-paper-dim border border-ink/[0.06] p-4">
      <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-2">Tajweed colors</p>
      <div className="flex flex-wrap gap-x-3 gap-y-1.5">
        {legend.map((rule) => (
          <span key={rule.name} className="flex items-center gap-1.5 text-xs font-body text-ink-soft">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full shrink-0"
              style={{ backgroundColor: rule.color }}
              aria-hidden
            />
            {rule.name}
          </span>
        ))}
      </div>
    </div>
  );
}
