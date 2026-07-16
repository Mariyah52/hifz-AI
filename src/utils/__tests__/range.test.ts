import { describe, it, expect } from 'vitest';
import { rangeArray } from '@/utils/range';

describe('rangeArray', () => {
  it('returns an inclusive range', () => {
    expect(rangeArray(1, 5)).toEqual([1, 2, 3, 4, 5]);
  });

  it('returns a single-element array when from equals to', () => {
    expect(rangeArray(3, 3)).toEqual([3]);
  });

  it('returns an empty array when to < from', () => {
    expect(rangeArray(5, 1)).toEqual([]);
  });

  it('handles a large ayah-count-sized range without off-by-one errors', () => {
    const result = rangeArray(1, 286); // Al-Baqarah's ayah count
    expect(result).toHaveLength(286);
    expect(result[0]).toBe(1);
    expect(result[285]).toBe(286);
  });

  it('handles negative bounds correctly', () => {
    expect(rangeArray(-2, 2)).toEqual([-2, -1, 0, 1, 2]);
  });
});
