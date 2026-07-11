const EASTERN_ARABIC_DIGITS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];

export function toArabicNumerals(value: number): string {
  return String(value)
    .split('')
    .map((digit) => EASTERN_ARABIC_DIGITS[Number(digit)] ?? digit)
    .join('');
}
