import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { toArabicNumerals } from '@/utils/arabicNumerals';
import { mulberry32 } from '@/utils/seededRandom';
import type { MushafPageAyah } from '@/types/quran';

export type HideLevel = 'word' | 'line' | 'multiLine' | 'halfPage' | 'fullPage';

interface WordToken {
  id: string;
  text: string;
  surahNumber: number;
  ayahNumber: number;
}

interface WordMaskedPageViewerProps {
  ayahs: MushafPageAyah[];
  hideLevel: HideLevel;
  /** Bump this to regenerate which word(s)/line(s) are hidden at the current level. */
  maskSeed: number;
}

/**
 * Honest limitation worth stating up front, in code and in the UI: "line"
 * here means a visual line as reflowed by THIS browser at its current
 * width — not the fixed line of a specific printed mushaf edition. A real
 * hafiz's "hide line 3" technique depends on having memorized a fixed
 * page image, which this app doesn't render (see Phase 12's notes on why
 * true line-for-line reproduction needs page-specific glyph fonts, not
 * text reflow). This is still a real, useful digital variant of the
 * technique — words that visually wrap together right now get hidden
 * together — just not tied to one canonical page layout, and it will
 * regroup differently on a different screen width.
 */
export function WordMaskedPageViewer({ ayahs, hideLevel, maskSeed }: WordMaskedPageViewerProps) {
  const words = useMemo<WordToken[]>(() => {
    const list: WordToken[] = [];
    ayahs.forEach((ayah) => {
      ayah.text.split(' ').forEach((w, i) => {
        if (w) list.push({ id: `${ayah.surahNumber}-${ayah.ayahNumber}-${i}`, text: w, surahNumber: ayah.surahNumber, ayahNumber: ayah.ayahNumber });
      });
    });
    return list;
  }, [ayahs]);

  const wordRefs = useRef<Map<string, HTMLSpanElement>>(new Map());
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [lineByWord, setLineByWord] = useState<Map<string, number>>(new Map());

  useLayoutEffect(() => {
    function measure() {
      const map = new Map<string, number>();
      const tops: number[] = [];
      wordRefs.current.forEach((el) => tops.push(Math.round(el.offsetTop)));
      const uniqueTops = Array.from(new Set(tops)).sort((a, b) => a - b);
      wordRefs.current.forEach((el, id) => {
        map.set(id, uniqueTops.indexOf(Math.round(el.offsetTop)));
      });
      setLineByWord(map);
    }
    measure();
    const observer = new ResizeObserver(measure);
    if (containerRef.current) observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [words]);

  const maskedIds = useMemo(() => {
    // "word" / "halfPage" / "fullPage" only need the word list itself —
    // gating them behind `lineByWord` (only actually needed by "line" and
    // "multiLine") meant that if the ResizeObserver measurement pass ever
    // ran late or came back empty, masking silently did nothing at all,
    // even in the default "word" mode. Each branch below now only
    // requires the data it actually uses.
    if (words.length === 0) return new Set<string>();
    const rng = mulberry32(maskSeed);

    if (hideLevel === 'word') {
      const idx = Math.floor(rng() * words.length);
      return new Set([words[idx].id]);
    }
    if (hideLevel === 'fullPage') {
      return new Set(words.map((w) => w.id));
    }
    if (hideLevel === 'halfPage') {
      const half = Math.floor(words.length / 2);
      const slice = rng() > 0.5 ? words.slice(half) : words.slice(0, half);
      return new Set(slice.map((w) => w.id));
    }

    if (lineByWord.size === 0) return new Set<string>();
    const totalLines = Math.max(...Array.from(lineByWord.values())) + 1;
    const spanLines = hideLevel === 'multiLine' ? Math.min(3, totalLines) : 1;
    const startLine = Math.floor(rng() * Math.max(1, totalLines - spanLines + 1));
    const targetLines = new Set(Array.from({ length: spanLines }, (_, i) => startLine + i));
    return new Set(words.filter((w) => targetLines.has(lineByWord.get(w.id) ?? -1)).map((w) => w.id));
  }, [hideLevel, maskSeed, words, lineByWord]);

  const [revealedIds, setRevealedIds] = useState<Set<string>>(new Set());
  useEffect(() => {
    setRevealedIds(new Set());
  }, [hideLevel, maskSeed]);

  function revealWord(id: string) {
    setRevealedIds((prev) => new Set(prev).add(id));
  }

  const groups: { surahNumber: number; ayahs: MushafPageAyah[] }[] = [];
  for (const ayah of ayahs) {
    const last = groups[groups.length - 1];
    if (last && last.surahNumber === ayah.surahNumber) last.ayahs.push(ayah);
    else groups.push({ surahNumber: ayah.surahNumber, ayahs: [ayah] });
  }

  return (
    <div ref={containerRef} className="rounded-card bg-paper border border-ink/[0.06] shadow-folio p-5 flex flex-col gap-4">
      {groups.map((group) => (
        <div key={`${group.surahNumber}-${group.ayahs[0].ayahNumber}`}>
          {(groups.length > 1 || group.ayahs[0].ayahNumber === 1) && (
            <p className="text-center font-mono text-[11px] uppercase tracking-widest text-ink-soft mb-2">
              Surah {group.ayahs[0].surahName}
            </p>
          )}
          <div dir="rtl" className="font-arabic text-2xl leading-[2.6] text-ink text-justify [text-align-last:center]">
            {group.ayahs.map((ayah) => (
              <span key={ayah.ayahNumber}>
                {ayah.text.split(' ').map((text, i) => {
                  if (!text) return null;
                  const id = `${ayah.surahNumber}-${ayah.ayahNumber}-${i}`;
                  const isMasked = maskedIds.has(id) && !revealedIds.has(id);
                  return (
                    <span
                      key={id}
                      ref={(el) => {
                        if (el) wordRefs.current.set(id, el);
                        else wordRefs.current.delete(id);
                      }}
                      onClick={() => isMasked && revealWord(id)}
                      className={isMasked ? 'cursor-pointer select-none blur-sm hover:blur-[3px] transition-all' : undefined}
                    >
                      {text}{' '}
                    </span>
                  );
                })}
                <span
                  className="inline-flex items-center justify-center mx-1 h-6 w-6 rounded-full border border-gold/50
                    text-[11px] font-arabic text-gold align-middle"
                  aria-hidden
                >
                  {toArabicNumerals(ayah.ayahNumber)}
                </span>
                {ayah.isSajda && (
                  <span
                    className="inline-flex items-center justify-center mx-0.5 h-5 px-1.5 rounded-full bg-maroon/10
                      text-[10px] font-mono text-maroon align-middle"
                  >
                    سجدة
                  </span>
                )}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
