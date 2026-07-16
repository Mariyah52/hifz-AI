import { describe, it, expect } from 'vitest';
import { mulberry32 } from '@/utils/seededRandom';

describe('mulberry32', () => {
  it('produces the same sequence for the same seed (deterministic)', () => {
    const seqA = Array.from({ length: 5 }, mulberry32(42));
    const seqB = Array.from({ length: 5 }, mulberry32(42));
    expect(seqA).toEqual(seqB);
  });

  it('produces a different sequence for a different seed', () => {
    const gen1 = mulberry32(1);
    const gen2 = mulberry32(2);
    const seq1 = [gen1(), gen1(), gen1()];
    const seq2 = [gen2(), gen2(), gen2()];
    expect(seq1).not.toEqual(seq2);
  });

  it('always returns a number in [0, 1)', () => {
    const gen = mulberry32(123);
    for (let i = 0; i < 200; i++) {
      const value = gen();
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThan(1);
    }
  });

  it('does not repeat the exact same value on consecutive calls (basic sanity, not a real randomness proof)', () => {
    const gen = mulberry32(7);
    const first = gen();
    const second = gen();
    expect(first).not.toEqual(second);
  });
});
