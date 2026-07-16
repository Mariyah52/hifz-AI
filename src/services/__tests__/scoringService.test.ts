import { describe, it, expect } from 'vitest';
import { estimatePace } from '@/services/scoringService';

describe('estimatePace', () => {
  it('flags a recording within the expected range as within range', () => {
    // 7 ayahs at a reasonable tarteel pace, e.g. ~8s/ayah = 56s
    const result = estimatePace(7, 56);
    expect(result.withinExpectedRange).toBe(true);
  });

  it('flags a suspiciously fast recording as outside the expected range', () => {
    // 7 ayahs read in 2 seconds total is not a real recitation
    const result = estimatePace(7, 2);
    expect(result.withinExpectedRange).toBe(false);
  });

  it('flags a suspiciously slow / stalled recording as outside the expected range', () => {
    // 7 ayahs "recorded" for 10 minutes
    const result = estimatePace(7, 600);
    expect(result.withinExpectedRange).toBe(false);
  });

  it('treats an ayahCount of 0 the same as 1 (guards against divide-by-nonsense ranges)', () => {
    const zeroResult = estimatePace(0, 6);
    const oneResult = estimatePace(1, 6);
    expect(zeroResult.expectedSecondsRange).toEqual(oneResult.expectedSecondsRange);
  });

  it('scales the expected range linearly with ayah count', () => {
    const oneAyah = estimatePace(1, 5);
    const tenAyahs = estimatePace(10, 5);
    expect(tenAyahs.expectedSecondsRange[0]).toBe(oneAyah.expectedSecondsRange[0] * 10);
    expect(tenAyahs.expectedSecondsRange[1]).toBe(oneAyah.expectedSecondsRange[1] * 10);
  });

  it('always returns the actualSeconds it was given, unmodified', () => {
    const result = estimatePace(5, 42.5);
    expect(result.actualSeconds).toBe(42.5);
  });
});
