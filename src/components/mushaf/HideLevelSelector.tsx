import type { HideLevel } from '@/components/mushaf/WordMaskedPageViewer';

interface HideLevelOption {
  level: HideLevel;
  label: string;
}

const OPTIONS: HideLevelOption[] = [
  { level: 'word', label: 'Word' },
  { level: 'line', label: 'Line' },
  { level: 'multiLine', label: 'Lines' },
  { level: 'halfPage', label: 'Half page' },
  { level: 'fullPage', label: 'Full page' },
];

interface HideLevelSelectorProps {
  value: HideLevel;
  onChange: (level: HideLevel) => void;
}

export function HideLevelSelector({ value, onChange }: HideLevelSelectorProps) {
  return (
    <div className="flex gap-1.5 rounded-full bg-sage p-1 overflow-x-auto">
      {OPTIONS.map((option) => (
        <button
          key={option.level}
          onClick={() => onChange(option.level)}
          className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold font-body transition-colors ${
            value === option.level ? 'bg-teal text-paper' : 'text-ink-soft hover:text-ink'
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
