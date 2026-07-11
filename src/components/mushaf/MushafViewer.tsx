import { useEffect, useRef } from 'react';
import { MushafAyah } from './MushafAyah';
import { TajweedAyahText } from './TajweedAyahText';
import { splitBismillah, splitBismillahTagged } from '@/utils/bismillah';
import { parseTajweedSegments, stripTajweedTags } from '@/utils/tajweed';
import type { AyahText } from '@/types/quran';

interface MushafViewerProps {
  ayahs: AyahText[];
  activeAyah: number;
  onSelectAyah: (ayahNumber: number) => void;
  /** When set and non-empty, renders tajweed-colored text instead of plain ink — see utils/tajweed.ts. */
  tajweedAyahs?: AyahText[] | null;
}

export function MushafViewer({ ayahs, activeAyah, onSelectAyah, tajweedAyahs }: MushafViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const useTajweed = Boolean(tajweedAyahs && tajweedAyahs.length > 0);
  const sourceAyahs = useTajweed ? tajweedAyahs! : ayahs;

  useEffect(() => {
    const el = document.getElementById(`ayah-${activeAyah}`);
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [activeAyah]);

  // Ayah 1 of every surah except At-Tawbah (9) carries the Bismillah baked
  // into its text — split it into its own header line so it doesn't run
  // straight into the surah body. Display-only: ayah numbers/text used for
  // playback, scoring, and analysis elsewhere are untouched.
  const firstAyah = sourceAyahs[0];
  const opensWithBismillah = firstAyah?.ayahNumber === 1 && firstAyah.surahNumber !== 9;

  const { bismillah, rest } = opensWithBismillah
    ? useTajweed
      ? splitBismillahTagged(firstAyah.text, stripTajweedTags(firstAyah.text))
      : splitBismillah(firstAyah.text)
    : { bismillah: null, rest: firstAyah?.text ?? '' };

  const bodyAyahs = bismillah
    ? sourceAyahs.map((a, i) => (i === 0 ? { ...a, text: rest } : a)).filter((a) => a.text.trim().length > 0)
    : sourceAyahs;

  return (
    <div
      ref={containerRef}
      dir="rtl"
      className="rounded-card bg-paper border border-ink/[0.06] shadow-folio p-5"
    >
      {bismillah && (
        <p
          onClick={() => onSelectAyah(1)}
          className={`cursor-pointer text-center font-arabic text-2xl text-ink mb-2 rounded-md transition-colors duration-200 ${
            activeAyah === 1 ? 'bg-gold/20' : 'hover:bg-sage/40'
          }`}
        >
          {useTajweed
            ? parseTajweedSegments(bismillah).map((segment, i) =>
                segment.color ? (
                  <span key={i} style={{ color: segment.color }}>
                    {segment.text}
                  </span>
                ) : (
                  <span key={i}>{segment.text}</span>
                ),
              )
            : bismillah}
        </p>
      )}
      <div className="font-arabic text-2xl leading-[2.6] text-ink text-justify [text-align-last:center]">
        {bodyAyahs.map((ayah) =>
          useTajweed ? (
            <TajweedAyahText
              key={ayah.ayahNumber}
              ayahNumber={ayah.ayahNumber}
              text={ayah.text}
              isActive={ayah.ayahNumber === activeAyah}
              onSelect={() => onSelectAyah(ayah.ayahNumber)}
            />
          ) : (
            <MushafAyah
              key={ayah.ayahNumber}
              ayahNumber={ayah.ayahNumber}
              text={ayah.text}
              isActive={ayah.ayahNumber === activeAyah}
              onSelect={() => onSelectAyah(ayah.ayahNumber)}
            />
          ),
        )}
      </div>
    </div>
  );
}
