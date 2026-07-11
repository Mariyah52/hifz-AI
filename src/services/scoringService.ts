import type { PaceEstimate } from '@/types/practice';

/**
 * Local, non-AI pace estimate: compares a recording's duration against a
 * rough expected range for the number of ayahs recited, based on typical
 * tarteel (unhurried, clear) recitation speed.
 *
 * This is deliberately the ONLY local "scoring" this app does — it
 * can't detect mispronunciation or fluency, and never will locally; that
 * needs real audio/acoustic analysis this file isn't the place for.
 * Missing/extra/substituted-word detection is real, but lives server-side
 * (Phase 14's `POST /me/practice-attempts/{id}/analyze`, via Whisper
 * transcription + a text diff) — not here, and not from the pace alone.
 * Do not extend this file to fabricate pronunciation/fluency numbers;
 * those still have no real signal behind them anywhere in this app.
 */
const SECONDS_PER_AYAH_FAST = 5; // brisk but unhurried
const SECONDS_PER_AYAH_SLOW = 12; // deliberate tarteel pace
const TOLERANCE = 0.4; // 40% slack on either side of the expected range

export function estimatePace(ayahCount: number, actualSeconds: number): PaceEstimate {
  const safeAyahCount = Math.max(1, ayahCount);
  const expectedSecondsRange: [number, number] = [
    safeAyahCount * SECONDS_PER_AYAH_FAST,
    safeAyahCount * SECONDS_PER_AYAH_SLOW,
  ];
  const [low, high] = expectedSecondsRange;
  const withinExpectedRange = actualSeconds >= low * (1 - TOLERANCE) && actualSeconds <= high * (1 + TOLERANCE);

  return { expectedSecondsRange, actualSeconds, withinExpectedRange };
}
