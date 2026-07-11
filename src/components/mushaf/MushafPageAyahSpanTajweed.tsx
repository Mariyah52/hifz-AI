import { toArabicNumerals } from '@/utils/arabicNumerals';
import { parseTajweedSegments } from '@/utils/tajweed';

interface MushafPageAyahSpanTajweedProps {
  surahNumber: number;
  ayahNumber: number;
  /** Raw text with embedded `<tajweed class="...">` tags from the quran-tajweed edition. */
  text: string;
  isSajda: boolean;
}

/** Same layout as `MushafPageAyahSpan`, but colors each tajweed rule per its documented color. */
export function MushafPageAyahSpanTajweed({
  surahNumber,
  ayahNumber,
  text,
  isSajda,
}: MushafPageAyahSpanTajweedProps) {
  const segments = parseTajweedSegments(text);

  return (
    <span id={`page-ayah-${surahNumber}-${ayahNumber}`}>
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
      {isSajda && (
        <span
          className="inline-flex items-center justify-center mx-0.5 h-5 px-1.5 rounded-full bg-maroon/10
            text-[10px] font-mono text-maroon align-middle"
          title="Sajdah — a prostration is prescribed on reciting or hearing this ayah"
        >
          سجدة
        </span>
      )}
    </span>
  );
}
