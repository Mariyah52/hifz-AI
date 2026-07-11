// Arabic diacritics (harakat/tanween/shadda/sukun U+064B-U+065F), the
// Quranic superscript alef (U+0670), small Quranic annotation marks
// (U+06D6-U+06ED), and the kashida/elongation character (U+0640) — same
// ranges the backend's arabic_text.py normalizes against, kept in sync
// deliberately since both compare Quran text for equality.
const DIACRITICS_RE = /[ً-ٰٟۖ-ۭـ]/g;

// The four Uthmani words of the Bismillah, diacritics stripped, used only
// to *detect* the prefix — the returned text below keeps the original
// diacritics from the source, nothing here is hand-typed as scripture.
const BISMILLAH_WORDS_NORMALIZED = ['بسم', 'الله', 'الرحمن', 'الرحيم'];

// Same letter normalization the backend's arabic_text.py applies before
// comparing Quran text. Matters here specifically because "الله" (and
// other word-initial alefs) render with alef-wasla (ٱ) instead of a plain
// alef (ا) whenever the preceding word ends in a vowel — true right after
// "بِسْمِ" and "يَا أَيُّهَا" — so without this mapping the detector below
// silently never matched, and Bismillah never got split off anywhere.
const LETTER_NORMALIZATION: Record<string, string> = {
  'أ': 'ا', // أ -> ا
  'إ': 'ا', // إ -> ا
  'آ': 'ا', // آ -> ا
  'ٱ': 'ا', // ٱ (alef wasla) -> ا
  'ى': 'ي', // ى -> ي
  'ة': 'ه', // ة -> ه
};

function normalizeWord(word: string): string {
  let normalized = word.replace(DIACRITICS_RE, '');
  for (const [from, to] of Object.entries(LETTER_NORMALIZATION)) {
    normalized = normalized.split(from).join(to);
  }
  return normalized;
}

/**
 * Al Quran Cloud's Uthmani text bakes the Bismillah into ayah 1 of every
 * surah except At-Tawbah (9) — as the *entire* text for Al-Fatiha (where
 * it's genuinely its own counted ayah), or as a literal prefix glued onto
 * ayah 1's real content for every other surah. Mushaf/Learn viewers split
 * it out here so it can render as its own header line instead of running
 * straight into the surah body — display-only: the ayah text/numbering
 * used for scoring, analysis, and playback elsewhere in the app is never
 * touched by this.
 */
export function splitBismillah(text: string): { bismillah: string | null; rest: string } {
  const words = text.split(/\s+/).filter(Boolean);
  if (words.length < BISMILLAH_WORDS_NORMALIZED.length) return { bismillah: null, rest: text };

  const isPrefixMatch = BISMILLAH_WORDS_NORMALIZED.every(
    (expected, i) => normalizeWord(words[i]) === expected,
  );
  if (!isPrefixMatch) return { bismillah: null, rest: text };

  return {
    bismillah: words.slice(0, BISMILLAH_WORDS_NORMALIZED.length).join(' '),
    rest: words.slice(BISMILLAH_WORDS_NORMALIZED.length).join(' '),
  };
}

/**
 * Same split, but for tajweed-tagged text (see utils/tajweed.ts) — each
 * "word" may have `<tajweed class="...">` markup wrapped around part of
 * it, which would break splitBismillah's plain-text word comparison. This
 * detects the prefix against a *tag-stripped* copy (word count only, tags
 * never introduce extra whitespace so word boundaries match 1:1 either
 * way), then cuts the original *tagged* word array at that same count —
 * so the returned bismillah/rest keep their tajweed coloring intact.
 */
export function splitBismillahTagged(
  taggedText: string,
  strippedText: string,
): { bismillah: string | null; rest: string } {
  const { bismillah: strippedBismillah } = splitBismillah(strippedText);
  if (!strippedBismillah) return { bismillah: null, rest: taggedText };

  const wordCount = strippedBismillah.split(/\s+/).filter(Boolean).length;
  const taggedWords = taggedText.split(/\s+/).filter(Boolean);

  return {
    bismillah: taggedWords.slice(0, wordCount).join(' '),
    rest: taggedWords.slice(wordCount).join(' '),
  };
}
