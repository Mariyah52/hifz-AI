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
      // box-decoration-break: clone — without this, an inline element's
      // border/shadow only wraps the whole run's bounding box, which
      // renders as disconnected, mismatched boxes when a long ayah spans
      // multiple visual lines. clone makes each wrapped line render its
      // own consistent rounded box instead.
      style={{ WebkitBoxDecorationBreak: 'clone', boxDecorationBreak: 'clone' }}
      className={`cursor-pointer transition-colors duration-200 rounded-md px-0.5 ${
        isActive ? 'bg-gold/20 shadow-[inset_0_0_0_1px_var(--color-gold)]' : 'hover:bg-sage/60'
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
