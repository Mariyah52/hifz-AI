import { toArabicNumerals } from '@/utils/arabicNumerals';
import { parseTajweedSegments } from '@/utils/tajweed';

interface TajweedAyahTextProps {
  ayahNumber: number;
  /** Raw text with embedded `<tajweed class="...">` tags from the quran-tajweed edition. */
  text: string;
  isActive: boolean;
  onSelect: () => void;
}

/** Same layout/behavior as `MushafAyah`, but renders each tajweed rule in its documented color instead of plain ink. */
export function TajweedAyahText({ ayahNumber, text, isActive, onSelect }: TajweedAyahTextProps) {
  const segments = parseTajweedSegments(text);

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
      {segments.map((segment, i) =>
        segment.color ? (
          <span key={i} style={{ color: segment.color }} title={segment.ruleName ?? undefined}>
            {segment.text}
          </span>
        ) : (
          <span key={i}>{segment.text}</span>
        ),
      )}
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
