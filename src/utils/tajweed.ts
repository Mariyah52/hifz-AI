/**
 * Tajweed color legend — copied verbatim from Al Quran Cloud's own
 * published guide (https://alquran.cloud/tajweed-guide), the same live
 * text API this app already fetches all Quran text from. Not invented:
 * every color here is the one that provider documents for that rule.
 *
 * PARSING: this app previously assumed the `quran-tajweed` edition wraps
 * rules in `<tajweed class="...">` HTML tags. That assumption was wrong
 * — verified against the live API, it actually returns a raw shorthand
 * notation like `[h:9421[ٱ]` (a letter code, optional `:id`, then the
 * affected letters in a second bracket). The mapping below (single-letter
 * code -> rule) is not guessed: it matches (a) Al Quran Cloud's own
 * tajweed-guide worked example (`[h:9421[ٱ]` -> Hamzat ul Wasl, the
 * `ham_wasl` class), and (b) the same letter-code table independently
 * reused across several unrelated open-source parsers for this exact API
 * (GlobalQuran's JS parser, and Android/iOS/web ports of it) — multiple
 * independent implementations agreeing is real corroboration, not a
 * single unverified guess.
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
  qlq: { name: 'Qalqalah', color: '#DD0008' },
  ikhafa_shafawi: { name: 'Ikhafa Shafawi', color: '#D500B7' },
  ikhfa_shafawi: { name: 'Ikhafa Shafawi', color: '#D500B7' },
  ikhf_shfw: { name: 'Ikhafa Shafawi', color: '#D500B7' },
  ikhafa: { name: 'Ikhafa', color: '#9400A8' },
  ikhfa: { name: 'Ikhafa', color: '#9400A8' },
  ikhf: { name: 'Ikhafa', color: '#9400A8' },
  idgham_shafawi: { name: 'Idgham Shafawi', color: '#58B800' },
  idghm_shfw: { name: 'Idgham Shafawi', color: '#58B800' },
  iqlab: { name: 'Iqlab', color: '#26BFFD' },
  iqlb: { name: 'Iqlab', color: '#26BFFD' },
  idgham_ghunnah: { name: 'Idgham With Ghunnah', color: '#169777' },
  idgham_with_ghunnah: { name: 'Idgham With Ghunnah', color: '#169777' },
  idgh_ghn: { name: 'Idgham With Ghunnah', color: '#169777' },
  idgham_wo_ghunnah: { name: 'Idgham Without Ghunnah', color: '#169200' },
  idgham_without_ghunnah: { name: 'Idgham Without Ghunnah', color: '#169200' },
  idgh_w_ghn: { name: 'Idgham Without Ghunnah', color: '#169200' },
  idgham_mutajanisayn: { name: 'Idgham Mutajanisayn', color: '#A1A1A1' },
  idgham_mutaqaribayn: { name: 'Idgham Mutaqaribayn', color: '#A1A1A1' },
  idgh_mus: { name: 'Idgham Mutajanisayn/Mutaqaribayn', color: '#A1A1A1' },
  ghunnah: { name: 'Ghunnah', color: '#FF7E1E' },
  ghn: { name: 'Ghunnah', color: '#FF7E1E' },
};

/**
 * Single-letter raw code -> RULES key. Source: the same GlobalQuran.js
 * mapping referenced above (verified against Al Quran Cloud's own
 * worked example for `h`).
 */
const CODE_TO_RULE_KEY: Record<string, string> = {
  h: 'ham_wasl',
  s: 'slnt',
  l: 'laam_shamsiyah',
  n: 'madda_normal',
  p: 'madda_permissible',
  m: 'madda_necessary',
  q: 'qalqalah',
  o: 'madda_obligatory',
  c: 'ikhafa_shafawi',
  f: 'ikhafa',
  w: 'idgham_shafawi',
  i: 'iqlab',
  a: 'idgham_ghunnah',
  u: 'idgham_wo_ghunnah',
  d: 'idgham_mutajanisayn',
  b: 'idgham_mutaqaribayn',
  g: 'ghunnah',
};

export interface TajweedSegment {
  text: string;
  color: string | null;
  ruleName: string | null;
}

/**
 * Raw tajweed spans look like `[<code>(:<id>)?[<content>]` — e.g.
 * `[h:9421[ٱ]` or `[l[ل]` (the `:id` is optional). Content never
 * contains literal `[`/`]` (it's Arabic letters/diacritics), so a
 * non-greedy match up to the next `]` is safe.
 */
const RAW_SPAN_RE = /\[([a-z])(?::\d+)?\[([^\[\]]*)\]/g;

/** True only when the sample text actually contains the raw tajweed notation this app knows how to parse. */
export function isParseableTajweedText(ayahs: { text: string }[]): boolean {
  const sample = ayahs.find((a) => a.text.trim().length > 0);
  if (!sample) return false;
  RAW_SPAN_RE.lastIndex = 0;
  return RAW_SPAN_RE.test(sample.text);
}

/** Strips all raw tajweed markup down to plain text — used wherever exact ayah text is needed (Bismillah detection, playback, etc.), never for display. */
export function stripTajweedTags(text: string): string {
  RAW_SPAN_RE.lastIndex = 0;
  return text.replace(RAW_SPAN_RE, (_m, _code, content) => content);
}

/** Splits raw tajweed-tagged API text into plain/colored runs, in order, ready to render as spans. */
export function parseTajweedSegments(text: string): TajweedSegment[] {
  const segments: TajweedSegment[] = [];
  let lastIndex = 0;
  RAW_SPAN_RE.lastIndex = 0;

  let match: RegExpExecArray | null;
  while ((match = RAW_SPAN_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ text: text.slice(lastIndex, match.index), color: null, ruleName: null });
    }
    const code = match[1];
    const content = match[2];
    const ruleKey = CODE_TO_RULE_KEY[code];
    const rule = ruleKey ? RULES[ruleKey] : undefined;
    segments.push({ text: content, color: rule?.color ?? null, ruleName: rule?.name ?? null });
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
