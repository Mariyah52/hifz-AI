import { useEffect, useState } from 'react';
import { MushafPageAyahSpan } from './MushafPageAyahSpan';
import { MushafPageAyahSpanTajweed } from './MushafPageAyahSpanTajweed';
import { splitBismillah } from '@/utils/bismillah';
import { parseTajweedSegments } from '@/utils/tajweed';
import { getSurahTajweedText } from '@/services/quranTextService';
import type { MushafPageAyah } from '@/types/quran';

interface MushafPageViewerProps {
  ayahs: MushafPageAyah[];
  /** When set and non-empty, renders tajweed-colored text instead of plain ink — see utils/tajweed.ts. */
  tajweedAyahs?: MushafPageAyah[] | null;
}

/**
 * Groups the page's flat ayah list into per-surah runs — a page can open
 * mid-surah, cross into a new surah, or (rarely) span three. Rendered as
 * continuous justified RTL text, same as `MushafViewer` (Learn Mode) —
 * this reproduces the real page's *content* faithfully (verified live,
 * same source as everywhere else in this app), but deliberately does
 * NOT attempt to match the exact line-by-line layout of a printed 15-line
 * Madani mushaf. True line-for-line reproduction needs page-specific
 * glyph fonts (e.g. KFGQPC's one-font-per-page sets) or rasterized page
 * images, not text reflow — a different, larger piece of work than this
 * phase's scope. See the root README's Phase 12 notes.
 *
 * Bismillah handling differs by edition, verified against the live API:
 * `quran-uthmani` bakes the Bismillah into ayah 1's text for every surah
 * except At-Tawbah (9) (see splitBismillah). `quran-tajweed` does NOT —
 * confirmed by fetching a real ayah (e.g. 4:1 on quran-tajweed): it starts
 * directly with the surah's actual first words, no Bismillah prefix. So
 * in tajweed mode there's nothing to split out of a surah's own opening
 * ayah — instead this fetches Al-Fatiha's own ayah 1 (which genuinely
 * *is* the Bismillah) once, cached, and reuses that same tajweed-colored
 * text as the heading for every surah-opening group on this page.
 */
export function MushafPageViewer({ ayahs, tajweedAyahs }: MushafPageViewerProps) {
  const useTajweed = Boolean(tajweedAyahs && tajweedAyahs.length > 0);
  const sourceAyahs = useTajweed ? tajweedAyahs! : ayahs;

  const [tajweedBismillah, setTajweedBismillah] = useState<string | null>(null);
  useEffect(() => {
    if (!useTajweed) {
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
  }, [useTajweed]);

  const groups: { surahNumber: number; surahName: string; ayahs: MushafPageAyah[] }[] = [];
  for (const ayah of sourceAyahs) {
    const lastGroup = groups[groups.length - 1];
    if (lastGroup && lastGroup.surahNumber === ayah.surahNumber) {
      lastGroup.ayahs.push(ayah);
    } else {
      groups.push({ surahNumber: ayah.surahNumber, surahName: ayah.surahName, ayahs: [ayah] });
    }
  }

  return (
    <div className="rounded-card bg-paper border border-ink/[0.06] shadow-folio p-5 flex flex-col gap-4">
      {groups.map((group) => {
        const firstAyah = group.ayahs[0];
        const opensWithBismillah = firstAyah.ayahNumber === 1 && firstAyah.surahNumber !== 9;
        const isAlFatihaBismillahAyah = firstAyah.surahNumber === 1 && firstAyah.ayahNumber === 1;

        const { bismillah, rest } = !opensWithBismillah
          ? { bismillah: null, rest: firstAyah.text }
          : useTajweed
            ? { bismillah: tajweedBismillah, rest: firstAyah.text }
            : splitBismillah(firstAyah.text);

        const bodyAyahs =
          bismillah && (!useTajweed || isAlFatihaBismillahAyah)
            ? group.ayahs.map((a, i) => (i === 0 ? { ...a, text: rest } : a)).filter((a) => a.text.trim().length > 0)
            : group.ayahs;

        return (
          <div key={`${group.surahNumber}-${firstAyah.ayahNumber}`}>
            {(groups.length > 1 || firstAyah.ayahNumber === 1) && (
              <p className="text-center font-mono text-[11px] uppercase tracking-widest text-ink-soft mb-2">
                Surah {group.surahName}
              </p>
            )}
            {bismillah && (
              <p className="text-center font-arabic text-2xl text-ink mb-2">
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
            <div
              dir="rtl"
              className="font-arabic text-2xl leading-[2.6] text-ink text-justify [text-align-last:center]"
            >
              {bodyAyahs.map((ayah) =>
                useTajweed ? (
                  <MushafPageAyahSpanTajweed
                    key={ayah.ayahNumber}
                    surahNumber={ayah.surahNumber}
                    ayahNumber={ayah.ayahNumber}
                    text={ayah.text}
                    isSajda={ayah.isSajda}
                  />
                ) : (
                  <MushafPageAyahSpan
                    key={ayah.ayahNumber}
                    surahNumber={ayah.surahNumber}
                    ayahNumber={ayah.ayahNumber}
                    text={ayah.text}
                    isSajda={ayah.isSajda}
                  />
                ),
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
