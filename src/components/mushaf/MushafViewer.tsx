import { useEffect, useRef, useState } from 'react';
import { MushafAyah } from './MushafAyah';
import { TajweedAyahText } from './TajweedAyahText';
import { splitBismillah } from '@/utils/bismillah';
import { parseTajweedSegments } from '@/utils/tajweed';
import { getSurahTajweedText } from '@/services/quranTextService';
import type { AyahText } from '@/types/quran';

interface MushafViewerProps {
  ayahs: AyahText[];
  activeAyah: number;
  onSelectAyah: (ayahNumber: number) => void;
  /** When set and non-empty, renders tajweed-colored text instead of plain ink — see utils/tajweed.ts. */
  tajweedAyahs?: AyahText[] | null;
}

/**
 * Bismillah handling differs by edition, verified against the live API:
 * `quran-uthmani` bakes the Bismillah into ayah 1's text for every surah
 * except At-Tawbah (9) (see splitBismillah). `quran-tajweed` does NOT —
 * confirmed by fetching a real ayah (e.g. 4:1 on quran-tajweed): it starts
 * directly with the surah's actual first words, no Bismillah prefix at
 * all. So in tajweed mode there's nothing to split out of the current
 * surah's own ayah 1 — instead this fetches Al-Fatiha's own ayah 1 (which
 * genuinely *is* the Bismillah, its own counted verse) once, cached, and
 * reuses that same tajweed-colored text as the heading for every surah
 * that opens with Bismillah, rather than guessing at markup that isn't
 * there.
 */
export function MushafViewer({ ayahs, activeAyah, onSelectAyah, tajweedAyahs }: MushafViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const useTajweed = Boolean(tajweedAyahs && tajweedAyahs.length > 0);
  const sourceAyahs = useTajweed ? tajweedAyahs! : ayahs;

  useEffect(() => {
    const el = document.getElementById(`ayah-${activeAyah}`);
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [activeAyah]);

  const firstAyah = sourceAyahs[0];
  const opensWithBismillah = firstAyah?.ayahNumber === 1 && firstAyah.surahNumber !== 9;

  const [tajweedBismillah, setTajweedBismillah] = useState<string | null>(null);
  useEffect(() => {
    if (!useTajweed || !opensWithBismillah) {
      setTajweedBismillah(null);
      return;
    }
    let cancelled = false;
    getSurahTajweedText(1)
      .then((alFatihaAyahs) => {
        if (cancelled) return;
        const ayah1 = alFatihaAyahs.find((a) => a.ayahNumber === 1);
        setTajweedBismillah(ayah1?.text ?? null);
      })
      .catch(() => {
        if (!cancelled) setTajweedBismillah(null);
      });
    return () => {
      cancelled = true;
    };
  }, [useTajweed, opensWithBismillah]);

  const { bismillah, rest } = !opensWithBismillah
    ? { bismillah: null, rest: firstAyah?.text ?? '' }
    : useTajweed
      ? { bismillah: tajweedBismillah, rest: firstAyah?.text ?? '' }
      : splitBismillah(firstAyah.text);

  // Al-Fatiha's own ayah 1 IS the Bismillah (its own counted verse, both
  // editions) — already shown as the heading above, so it's dropped from
  // the body here to avoid showing it twice. Every other surah's tajweed
  // ayah 1 is real, distinct content (see the component docstring for
  // why), so it's never filtered in tajweed mode.
  const isAlFatihaBismillahAyah = firstAyah?.surahNumber === 1 && firstAyah.ayahNumber === 1;
  const bodyAyahs =
    bismillah && (!useTajweed || isAlFatihaBismillahAyah)
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
            activeAyah === 1 ? 'bg-gold/25' : 'hover:bg-sage/40'
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
