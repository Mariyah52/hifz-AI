import { useState } from 'react';
import { useSurahList } from '@/hooks/useQuranData';

interface AssignSabaqFormProps {
  onAssign: (surahNumber: number, surahName: string, fromAyah: number, toAyah: number) => void;
}

export function AssignSabaqForm({ onAssign }: AssignSabaqFormProps) {
  const surahs = useSurahList();
  const [surahNumber, setSurahNumber] = useState(surahs[0]?.number ?? 1);
  const [fromAyah, setFromAyah] = useState(1);
  const [toAyah, setToAyah] = useState(5);

  const selected = surahs.find((s) => s.number === surahNumber);

  function handleSubmit() {
    if (!selected) return;
    onAssign(selected.number, selected.name, fromAyah, toAyah);
  }

  return (
    <div className="flex flex-col gap-3">
      <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
        Surah
        <select
          value={surahNumber}
          onChange={(e) => setSurahNumber(Number(e.target.value))}
          className="rounded-lg border border-ink/10 bg-paper-dim px-2 py-1.5 font-body text-sm text-ink"
        >
          {surahs.map((s) => (
            <option key={s.number} value={s.number}>
              {s.number}. {s.name}
            </option>
          ))}
        </select>
      </label>

      <div className="flex items-center gap-3">
        <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
          From
          <input
            type="number"
            min={1}
            max={selected?.ayahCount ?? 1}
            value={fromAyah}
            onChange={(e) => setFromAyah(Number(e.target.value))}
            className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink"
          />
        </label>
        <label className="flex items-center gap-2 text-xs text-ink-soft font-body">
          To
          <input
            type="number"
            min={fromAyah}
            max={selected?.ayahCount ?? 1}
            value={toAyah}
            onChange={(e) => setToAyah(Number(e.target.value))}
            className="w-16 rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink"
          />
        </label>
      </div>

      <button
        onClick={handleSubmit}
        className="rounded-full bg-teal text-paper font-semibold text-sm py-2.5 hover:bg-teal-dark transition-colors"
      >
        Assign Sabaq
      </button>
    </div>
  );
}
