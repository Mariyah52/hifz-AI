import { toArabicNumerals } from '@/utils/arabicNumerals';

interface MushafAyahProps {
  ayahNumber: number;
  text: string;
  isActive: boolean;
  onSelect: () => void;
}

export function MushafAyah({ ayahNumber, text, isActive, onSelect }: MushafAyahProps) {
  return (
    <span
      id={`ayah-${ayahNumber}`}
      onClick={onSelect}
      // Background wash only, no border/outline — a border or inset
      // shadow on an inline element that wraps across several visual
      // lines (a long ayah in justified RTL text) renders as
      // disconnected, mismatched-size boxes per line no matter what
      // box-decoration-break does here. A plain background color fills
      // each wrapped line smoothly with no hard edges to look broken.
      style={{ WebkitBoxDecorationBreak: 'clone', boxDecorationBreak: 'clone' }}
      className={`cursor-pointer transition-colors duration-200 rounded-md px-0.5 ${
        isActive ? 'bg-gold/25' : 'hover:bg-sage/60'
      }`}
    >
      {text}
      {/* Ayah-end marker: a small rosette-style roundel around the Eastern Arabic numeral,
          echoing the ProgressRing signature element rather than a plain circle. */}
      <span
        className="inline-flex items-center justify-center mx-1 h-6 w-6 rounded-full border border-gold/50
          text-[11px] font-arabic text-gold align-middle"
        aria-hidden
      >
        {toArabicNumerals(ayahNumber)}
      </span>
    </span>
  );
}
