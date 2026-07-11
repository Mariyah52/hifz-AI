import { toArabicNumerals } from '@/utils/arabicNumerals';

interface MushafPageAyahSpanProps {
  surahNumber: number;
  ayahNumber: number;
  text: string;
  isSajda: boolean;
}

export function MushafPageAyahSpan({ surahNumber, ayahNumber, text, isSajda }: MushafPageAyahSpanProps) {
  return (
    <span id={`page-ayah-${surahNumber}-${ayahNumber}`}>
      {text}
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
