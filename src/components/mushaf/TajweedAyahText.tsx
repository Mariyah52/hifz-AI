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
