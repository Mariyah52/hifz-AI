/**
 * Tajweed color legend — copied verbatim from Al Quran Cloud's own
 * published guide (https://alquran.cloud/tajweed-guide), the same live
 * text API this app already fetches all Quran text from. Not invented:
 * every color here is the one that provider documents for that rule.
 *
 * The API embeds each rule as an inline `<tajweed class="...">` tag
 * around the affected letters. We don't have one single confirmed source
 * for every exact class-name string the API emits (only a few were
 * directly verifiable), so each rule below is keyed under a few plausible
 * spelling variants — all aliases for one rule point at the exact same
 * color, so a guessed-wrong alias can only ever mean a rule renders
 * uncolored (safe), never a *wrong* color.
 */
interface TajweedRule {
  name: string;
  color: string;
}

const RULES: Record<string, TajweedRule> = {
  ham_wasl: { name: 'Hamzat ul Wasl', color: '#AAAAAA' },
  silent: { name: 'Silent', color: '#AAAAAA' },
  slnt: { name: 'Silent', color: '#AAAAAA' },
  laam_shamsiyah: { name: 'Laam Shamsiyyah', color: '#AAAAAA' },
  laam_shamsiyyah: { name: 'Laam Shamsiyyah', color: '#AAAAAA' },
  madda_normal: { name: 'Madda Normal', color: '#537FFF' },
  madda_permissible: { name: 'Madda Permissible', color: '#4050FF' },
  madda_necessary: { name: 'Madda Necessary', color: '#000EBC' },
  madda_obligatory: { name: 'Madda Obligatory', color: '#2144C1' },
  qalaqah: { name: 'Qalqalah', color: '#DD0008' },
  qalqalah: { name: 'Qalqalah', color: '#DD0008' },
  ikhafa_shafawi: { name: 'Ikhafa Shafawi', color: '#D500B7' },
  ikhfa_shafawi: { name: 'Ikhafa Shafawi', color: '#D500B7' },
  ikhafa: { name: 'Ikhafa', color: '#9400A8' },
  ikhfa: { name: 'Ikhafa', color: '#9400A8' },
  idgham_shafawi: { name: 'Idgham Shafawi', color: '#58B800' },
  iqlab: { name: 'Iqlab', color: '#26BFFD' },
  idgham_ghunnah: { name: 'Idgham With Ghunnah', color: '#169777' },
  idgham_with_ghunnah: { name: 'Idgham With Ghunnah', color: '#169777' },
  idgham_wo_ghunnah: { name: 'Idgham Without Ghunnah', color: '#169200' },
  idgham_without_ghunnah: { name: 'Idgham Without Ghunnah', color: '#169200' },
  idgham_mutajanisayn: { name: 'Idgham Mutajanisayn', color: '#A1A1A1' },
  idgham_mutaqaribayn: { name: 'Idgham Mutaqaribayn', color: '#A1A1A1' },
  ghunnah: { name: 'Ghunnah', color: '#FF7E1E' },
};

export interface TajweedSegment {
  text: string;
  color: string | null;
  ruleName: string | null;
}

/**
 * The `quran-tajweed` edition's live response was assumed (based on
 * third-party wrapper docs) to embed rules as `<tajweed class="...">` HTML
 * tags. Verified against the real running app, that assumption was wrong:
 * the API actually returns a different raw shorthand notation (rule codes
 * like `[h:9421[...]`), which this app has no confirmed, sourced mapping
 * for. Guessing at that mapping would risk showing the WRONG pronunciation
 * rule color on a letter — worse than showing no color at all, and against
 * this app's rule of never presenting unverified Quran-related data as
 * fact. So this checks the actual shape of what came back, and refuses to
 * treat unrecognized (raw-code) text as tajweed-parseable, rather than
 * silently rendering it broken or guessing at its meaning.
 */
export function isParseableTajweedText(ayahs: { text: string }[]): boolean {
  const sample = ayahs.find((a) => a.text.trim().length > 0);
  if (!sample) return false;
  return sample.text.includes('<tajweed');
}

const TAG_RE = /<tajweed class=(?:"([^"]*)"|'([^']*)'|([^\s>]*))[^>]*>([^<]*)<\/tajweed>/g;

/** Strips all `<tajweed>` markup down to plain text — used wherever exact ayah text is needed (Bismillah detection, playback, etc.), never for display. */
export function stripTajweedTags(text: string): string {
  return text.replace(TAG_RE, (_m, a, b, c, content) => content).replace(/<\/?tajweed[^>]*>/g, '');
}

/** Splits raw tajweed-tagged API text into plain/colored runs, in order, ready to render as spans. */
export function parseTajweedSegments(text: string): TajweedSegment[] {
  const segments: TajweedSegment[] = [];
  let lastIndex = 0;
  TAG_RE.lastIndex = 0;

  let match: RegExpExecArray | null;
  while ((match = TAG_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ text: text.slice(lastIndex, match.index), color: null, ruleName: null });
    }
    const className = (match[1] ?? match[2] ?? match[3] ?? '').toLowerCase();
    const rule = RULES[className];
    segments.push({ text: match[4], color: rule?.color ?? null, ruleName: rule?.name ?? null });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    segments.push({ text: text.slice(lastIndex), color: null, ruleName: null });
  }
  return segments;
}

/** For a legend/key UI — every distinct rule this app can actually color, deduplicated by color+name. */
export function getTajweedLegend(): TajweedRule[] {
  const seen = new Set<string>();
  const legend: TajweedRule[] = [];
  for (const rule of Object.values(RULES)) {
    const key = `${rule.name}:${rule.color}`;
    if (!seen.has(key)) {
      seen.add(key);
      legend.push(rule);
    }
  }
  return legend;
}
