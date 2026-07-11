import { Badge } from '@/components/ui/Badge';
import type { PracticeMistake } from '@/types/practice';

interface MistakeListProps {
  mistakes: PracticeMistake[];
}

const typeLabel: Record<PracticeMistake['mistakeType'], string> = {
  missing: 'not heard',
  extra: 'extra word',
  substituted: 'heard differently',
};

const typeTone: Record<PracticeMistake['mistakeType'], 'maroon' | 'gold' | 'neutral'> = {
  missing: 'maroon',
  extra: 'neutral',
  substituted: 'gold',
};

export function MistakeList({ mistakes }: MistakeListProps) {
  if (mistakes.length === 0) {
    return (
      <p className="font-body text-xs text-teal-dark">No word-level differences found — nice work.</p>
    );
  }

  return (
    <ul className="flex flex-col gap-1.5">
      {mistakes.map((mistake, i) => (
        <li key={i} className="flex items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 font-arabic text-base" dir="rtl">
            {mistake.referenceWord && (
              <span className={mistake.mistakeType === 'substituted' ? 'line-through text-ink-soft' : 'text-ink'}>
                {mistake.referenceWord}
              </span>
            )}
            {mistake.transcribedWord && (
              <span className="text-maroon">{mistake.transcribedWord}</span>
            )}
          </div>
          <div className="flex items-center gap-1.5 shrink-0 font-body">
            {mistake.ayahNumber && (
              <span className="font-mono text-[10px] text-ink-soft">ayah {mistake.ayahNumber}</span>
            )}
            <Badge tone={typeTone[mistake.mistakeType]}>{typeLabel[mistake.mistakeType]}</Badge>
          </div>
        </li>
      ))}
    </ul>
  );
}
