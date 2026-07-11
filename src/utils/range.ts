/** Inclusive integer range [from, to] as an array. */
export function rangeArray(from: number, to: number): number[] {
  if (to < from) return [];
  return Array.from({ length: to - from + 1 }, (_, i) => from + i);
}
