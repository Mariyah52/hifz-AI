import { EyeOff } from 'lucide-react';

interface HiddenAyahPlaceholderProps {
  fromAyah: number;
  toAyah: number;
}

export function HiddenAyahPlaceholder({ fromAyah, toAyah }: HiddenAyahPlaceholderProps) {
  const label = fromAyah === toAyah ? `Ayah ${fromAyah}` : `Ayah ${fromAyah}–${toAyah}`;
  return (
    <div className="rounded-card bg-paper-dim border border-ink/[0.06] flex flex-col items-center justify-center gap-2 py-12">
      <EyeOff size={22} className="text-ink-soft" />
      <p className="font-mono text-xs text-ink-soft">{label} · text hidden</p>
    </div>
  );
}
