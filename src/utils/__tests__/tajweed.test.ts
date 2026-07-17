import { describe, it, expect } from 'vitest';
import {
  isParseableTajweedText,
  stripTajweedTags,
  parseTajweedSegments,
  getTajweedLegend,
} from '@/utils/tajweed';

describe('isParseableTajweedText', () => {
  it('returns true when the sample ayah contains the API\'s real raw notation', () => {
    const ayahs = [{ text: 'بِسْمِ [h:9421[اَلَّهُ]' }];
    expect(isParseableTajweedText(ayahs)).toBe(true);
  });

  it('returns false for plain text with no tajweed markup', () => {
    const ayahs = [{ text: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحيمِ' }];
    expect(isParseableTajweedText(ayahs)).toBe(false);
  });

  it('returns false for the HTML tag format this app previously (wrongly) assumed the API used', () => {
    const ayahs = [{ text: 'بِسْمِ <tajweed class="ham_wasl">اللَّهِ</tajweed>' }];
    expect(isParseableTajweedText(ayahs)).toBe(false);
  });

  it('returns false when every ayah is empty/whitespace', () => {
    expect(isParseableTajweedText([{ text: '' }, { text: '   ' }])).toBe(false);
  });

  it('skips leading empty ayahs to find the first non-empty sample', () => {
    const ayahs = [{ text: '' }, { text: '[g[نَّ]' }];
    expect(isParseableTajweedText(ayahs)).toBe(true);
  });
});

describe('stripTajweedTags', () => {
  it('removes raw notation and keeps only the inner content', () => {
    const input = 'بِسْمِ [h:9421[اَلَّهِ] الرَّحْمَٰنِ';
    expect(stripTajweedTags(input)).toBe('بِسْمِ اَلَّهِ الرَّحْمَٰنِ');
  });

  it('returns plain text unchanged when there is no markup', () => {
    const input = 'بِسْمِ اللَّهِ';
    expect(stripTajweedTags(input)).toBe(input);
  });

  it('handles multiple spans in one string', () => {
    const input = '[g[أ]ب[q[ج]';
    expect(stripTajweedTags(input)).toBe('أبج');
  });
});

describe('parseTajweedSegments', () => {
  it('splits plain and colored runs in order', () => {
    const input = 'بِسْمِ [h:9421[اَلَّهِ] الرَّحْمَٰنِ';
    const segments = parseTajweedSegments(input);

    expect(segments).toHaveLength(3);
    expect(segments[0]).toEqual({ text: 'بِسْمِ ', color: null, ruleName: null });
    expect(segments[1]).toEqual({ text: 'اَلَّهِ', color: '#AAAAAA', ruleName: 'Hamzat ul Wasl' });
    expect(segments[2]).toEqual({ text: ' الرَّحْمَٰنِ', color: null, ruleName: null });
  });

  it('resolves every documented raw letter code to a real, colored rule', () => {
    const codes = ['h', 's', 'l', 'n', 'p', 'm', 'q', 'o', 'c', 'f', 'w', 'i', 'a', 'u', 'd', 'b', 'g'];
    for (const code of codes) {
      const segments = parseTajweedSegments(`[${code}[ن]`);
      expect(segments[0].color, `code "${code}" should resolve to a color`).not.toBeNull();
    }
  });

  it('renders an unrecognized letter code as uncolored rather than guessing', () => {
    const segments = parseTajweedSegments('[z[نَّ]');
    expect(segments[0].color).toBeNull();
    expect(segments[0].ruleName).toBeNull();
  });

  it('returns a single plain segment for text with no raw spans', () => {
    const segments = parseTajweedSegments('بِسْمِ اللَّهِ');
    expect(segments).toEqual([{ text: 'بِسْمِ اللَّهِ', color: null, ruleName: null }]);
  });

  it('is safe to call repeatedly (regex lastIndex does not leak state across calls)', () => {
    const input = '[g[نَّ]';
    const first = parseTajweedSegments(input);
    const second = parseTajweedSegments(input);
    expect(first).toEqual(second);
  });
});

describe('getTajweedLegend', () => {
  it('deduplicates aliased rules down to one legend entry per unique name+color', () => {
    const legend = getTajweedLegend();
    const keys = legend.map((r) => `${r.name}:${r.color}`);
    const uniqueKeys = new Set(keys);
    expect(keys.length).toBe(uniqueKeys.size);
  });

  it('includes Qalqalah exactly once despite aliased spellings in the source map', () => {
    const legend = getTajweedLegend();
    const qalqalahEntries = legend.filter((r) => r.name === 'Qalqalah');
    expect(qalqalahEntries).toHaveLength(1);
    expect(qalqalahEntries[0].color).toBe('#DD0008');
  });
});
