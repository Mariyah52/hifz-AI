import { describe, it, expect } from 'vitest';
import {
  isParseableTajweedText,
  stripTajweedTags,
  parseTajweedSegments,
  getTajweedLegend,
} from '@/utils/tajweed';

describe('isParseableTajweedText', () => {
  it('returns true when the sample ayah contains a <tajweed> tag', () => {
    const ayahs = [{ text: 'بِسْمِ <tajweed class="ham_wasl">اللَّهِ</tajweed>' }];
    expect(isParseableTajweedText(ayahs)).toBe(true);
  });

  it('returns false for plain text with no tajweed markup', () => {
    const ayahs = [{ text: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ' }];
    expect(isParseableTajweedText(ayahs)).toBe(false);
  });

  it('returns false for the raw shorthand notation this app does not trust ([h:9421[...])', () => {
    const ayahs = [{ text: '[h:9421[بِسْمِ اللَّهِ' }];
    expect(isParseableTajweedText(ayahs)).toBe(false);
  });

  it('returns false when every ayah is empty/whitespace', () => {
    expect(isParseableTajweedText([{ text: '' }, { text: '   ' }])).toBe(false);
  });

  it('skips leading empty ayahs to find the first non-empty sample', () => {
    const ayahs = [{ text: '' }, { text: '<tajweed class="ghunnah">نّ</tajweed>' }];
    expect(isParseableTajweedText(ayahs)).toBe(true);
  });
});

describe('stripTajweedTags', () => {
  it('removes tags and keeps only the inner text', () => {
    const input = 'بِسْمِ <tajweed class="ham_wasl">اللَّهِ</tajweed> الرَّحْمَٰنِ';
    expect(stripTajweedTags(input)).toBe('بِسْمِ اللَّهِ الرَّحْمَٰنِ');
  });

  it('returns plain text unchanged when there is no markup', () => {
    const input = 'بِسْمِ اللَّهِ';
    expect(stripTajweedTags(input)).toBe(input);
  });

  it('handles multiple tags in one string', () => {
    const input = '<tajweed class="ghunnah">أ</tajweed>ب<tajweed class="qalqalah">ج</tajweed>';
    expect(stripTajweedTags(input)).toBe('أبج');
  });
});

describe('parseTajweedSegments', () => {
  it('splits plain and colored runs in order', () => {
    const input = 'بِسْمِ <tajweed class="ham_wasl">اللَّهِ</tajweed> الرَّحْمَٰنِ';
    const segments = parseTajweedSegments(input);

    expect(segments).toHaveLength(3);
    expect(segments[0]).toEqual({ text: 'بِسْمِ ', color: null, ruleName: null });
    expect(segments[1]).toEqual({ text: 'اللَّهِ', color: '#AAAAAA', ruleName: 'Hamzat ul Wasl' });
    expect(segments[2]).toEqual({ text: ' الرَّحْمَٰنِ', color: null, ruleName: null });
  });

  it('resolves aliased rule class names to the same color', () => {
    const idghamGhunnah = parseTajweedSegments('<tajweed class="idgham_ghunnah">نّ</tajweed>');
    const idghamWithGhunnah = parseTajweedSegments('<tajweed class="idgham_with_ghunnah">نّ</tajweed>');
    expect(idghamGhunnah[0].color).toBe(idghamWithGhunnah[0].color);
    expect(idghamGhunnah[0].ruleName).toBe(idghamWithGhunnah[0].ruleName);
  });

  it('renders an unrecognized rule class as uncolored rather than guessing', () => {
    const segments = parseTajweedSegments('<tajweed class="totally_made_up_rule">نّ</tajweed>');
    expect(segments[0].color).toBeNull();
    expect(segments[0].ruleName).toBeNull();
  });

  it('returns a single plain segment for text with no tags', () => {
    const segments = parseTajweedSegments('بِسْمِ اللَّهِ');
    expect(segments).toEqual([{ text: 'بِسْمِ اللَّهِ', color: null, ruleName: null }]);
  });

  it('is safe to call repeatedly (regex lastIndex does not leak state across calls)', () => {
    const input = '<tajweed class="ghunnah">نّ</tajweed>';
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

  it('includes Qalqalah exactly once despite two aliased spellings in the source map', () => {
    const legend = getTajweedLegend();
    const qalqalahEntries = legend.filter((r) => r.name === 'Qalqalah');
    expect(qalqalahEntries).toHaveLength(1);
    expect(qalqalahEntries[0].color).toBe('#DD0008');
  });
});
