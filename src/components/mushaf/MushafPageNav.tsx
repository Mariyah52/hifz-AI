import { useEffect, useState, type SyntheticEvent } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface MushafPageNavProps {
  pageNumber: number;
  totalPages: number;
  onPrev: () => void;
  onNext: () => void;
  onGoToPage: (page: number) => void;
}

export function MushafPageNav({ pageNumber, totalPages, onPrev, onNext, onGoToPage }: MushafPageNavProps) {
  const [inputValue, setInputValue] = useState(String(pageNumber));

  useEffect(() => {
    setInputValue(String(pageNumber));
  }, [pageNumber]);

  function handleJump(e: SyntheticEvent) {
    e.preventDefault();
    const parsed = Number(inputValue);
    if (Number.isFinite(parsed)) onGoToPage(parsed);
  }

  return (
    <div className="rounded-card bg-paper border border-ink/[0.06] shadow-folio p-4 flex items-center justify-between gap-3">
      <button
        aria-label="Previous page"
        onClick={onPrev}
        disabled={pageNumber <= 1}
        className="grid h-10 w-10 place-items-center rounded-full bg-sage text-ink-soft
          hover:bg-[#d8dfcd] disabled:opacity-30 transition-colors"
      >
        <ChevronLeft size={18} />
      </button>

      <form onSubmit={handleJump} className="flex items-center gap-2">
        <input
          type="number"
          min={1}
          max={totalPages}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onBlur={handleJump}
          className="w-14 text-center rounded-lg border border-ink/10 bg-paper-dim px-2 py-1 font-mono text-sm text-ink"
        />
        <span className="font-mono text-xs text-ink-soft">of {totalPages}</span>
      </form>

      <button
        aria-label="Next page"
        onClick={onNext}
        disabled={pageNumber >= totalPages}
        className="grid h-10 w-10 place-items-center rounded-full bg-sage text-ink-soft
          hover:bg-[#d8dfcd] disabled:opacity-30 transition-colors"
      >
        <ChevronRight size={18} />
      </button>
    </div>
  );
}
