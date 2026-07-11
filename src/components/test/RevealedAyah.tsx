import { toArabicNumerals } from '@/utils/arabicNumerals';

interface RevealedAyahProps {
  ayahNumber: number;
  text: string | null;
  error: string | null;
}

export function RevealedAyah({ ayahNumber, text, error }: RevealedAyahProps) {
  if (error) {
    return (
      <div className="rounded-card bg-paper-dim border border-ink/[0.06] py-8 text-center">
        <p className="font-body text-sm text-ink-soft">{error}</p>
      </div>
    );
  }

  return (
    <div
      dir="rtl"
      className="font-arabic text-2xl leading-[2.6] text-ink text-justify [text-align-last:center]
        rounded-card bg-paper border border-ink/[0.06] shadow-folio p-5"
    >
      {text ?? '…'}
      <span
        className="inline-flex items-center justify-center mx-1 h-6 w-6 rounded-full border border-gold/50
          text-[11px] font-arabic text-gold align-middle"
        aria-hidden
      >
        {toArabicNumerals(ayahNumber)}
      </span>
    </div>
  );
}
