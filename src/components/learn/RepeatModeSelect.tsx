import type { RepeatMode } from '@/types/lesson';

interface RepeatModeSelectProps {
  value: RepeatMode;
  onChange: (mode: RepeatMode) => void;
}

const options: { value: RepeatMode; label: string }[] = [
  { value: 'single', label: 'Repeat ayah' },
  { value: 'range', label: 'Repeat range' },
  { value: 'continuous', label: 'Continuous' },
];

export function RepeatModeSelect({ value, onChange }: RepeatModeSelectProps) {
  return (
    <div className="flex gap-1.5 rounded-full bg-sage p-1">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`flex-1 rounded-full px-2.5 py-1.5 text-[11px] font-semibold font-body transition-colors ${
            value === opt.value ? 'bg-teal text-paper' : 'text-ink-soft hover:text-ink'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
