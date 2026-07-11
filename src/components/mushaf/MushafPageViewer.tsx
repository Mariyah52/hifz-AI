import { MushafPageAyahSpan } from './MushafPageAyahSpan';
import { MushafPageAyahSpanTajweed } from './MushafPageAyahSpanTajweed';
import { splitBismillah, splitBismillahTagged } from '@/utils/bismillah';
import { parseTajweedSegments, stripTajweedTags } from '@/utils/tajweed';
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
 */
export function MushafPageViewer({ ayahs, tajweedAyahs }: MushafPageViewerProps) {
  const useTajweed = Boolean(tajweedAyahs && tajweedAyahs.length > 0);
  const sourceAyahs = useTajweed ? tajweedAyahs! : ayahs;

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
        const { bismillah, rest } = opensWithBismillah
          ? useTajweed
            ? splitBismillahTagged(firstAyah.text, stripTajweedTags(firstAyah.text))
            : splitBismillah(firstAyah.text)
          : { bismillah: null, rest: firstAyah.text };
        const bodyAyahs = bismillah
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
