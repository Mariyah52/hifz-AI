import { describe, it, expect } from 'vitest';
import { toArabicNumerals } from '@/utils/arabicNumerals';

describe('toArabicNumerals', () => {
  it('converts each Western digit to its Eastern Arabic equivalent', () => {
    expect(toArabicNumerals(0)).toBe('٠');
    expect(toArabicNumerals(1)).toBe('١');
    expect(toArabicNumerals(9)).toBe('٩');
  });

  it('converts a multi-digit number preserving digit order', () => {
    expect(toArabicNumerals(286)).toBe('٢٨٦');
  });

  it('converts 114 (surah count) correctly', () => {
    expect(toArabicNumerals(114)).toBe('١١٤');
  });

  it('handles zero', () => {
    expect(toArabicNumerals(0)).toBe('٠');
  });
});
