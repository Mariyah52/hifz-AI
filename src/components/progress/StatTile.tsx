interface StatTileProps {
  label: string;
  value: string;
}

export function StatTile({ label, value }: StatTileProps) {
  return (
    <div className="flex-1 rounded-2xl bg-paper-dim px-3 py-3 text-center">
      <p className="font-mono text-lg font-semibold text-ink">{value}</p>
      <p className="text-[10px] uppercase tracking-wide text-ink-soft mt-0.5">{label}</p>
    </div>
  );
}
