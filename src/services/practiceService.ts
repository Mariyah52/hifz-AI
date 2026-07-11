import { apiFetch } from './apiClient';
import { generateClientMutationId, submitMultipartOrQueue } from './offlineSyncService';
import type { PracticeAttempt } from '@/types/practice';

export interface SaveAttemptInput {
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  durationSeconds: number;
  expectedMinSeconds: number;
  expectedMaxSeconds: number;
  /** The actual recording, if the browser captured one — uploaded and stored server-side. */
  audioBlob?: Blob | null;
}

/**
 * Real backend calls now — this used to read/write a flat array in
 * `localStorage`. Recordings are uploaded for real too: `audioBlob`, if
 * present, is sent as multipart form data and saved to disk server-side
 * (see `backend/app/services/media.py`), which is the actual storage
 * Phase 7's README flagged as missing.
 */
export function getAttemptsForSurah(surahNumber: number): Promise<PracticeAttempt[]> {
  // Note: this is a plain FastAPI query param (not a JSON body), so it
  // isn't camelCase-aliased like the rest of the API — it's genuinely
  // named `surah_number` server-side.
  return apiFetch<PracticeAttempt[]>('/me/practice-attempts', { query: { surah_number: surahNumber } });
}

/**
 * Phase 26: if the request can't reach the server at all (offline), this
 * queues it for later sync instead of throwing, and returns a clearly-
 * marked local placeholder (`isPendingSync: true`) so the UI can show
 * something immediately rather than losing the recording. A real network
 * error unrelated to connectivity (e.g. a validation failure) still
 * throws normally — only genuine offline-ness gets queued.
 */
export async function saveAttempt(input: SaveAttemptInput): Promise<PracticeAttempt> {
  const clientMutationId = generateClientMutationId();

  const outcome = await submitMultipartOrQueue<PracticeAttempt>({
    clientMutationId,
    endpoint: '/me/practice-attempts',
    formFields: {
      surah_number: String(input.surahNumber),
      surah_name: input.surahName,
      from_ayah: String(input.fromAyah),
      to_ayah: String(input.toAyah),
      duration_seconds: String(input.durationSeconds),
      expected_min_seconds: String(input.expectedMinSeconds),
      expected_max_seconds: String(input.expectedMaxSeconds),
      client_mutation_id: clientMutationId,
    },
    audioBlob: input.audioBlob,
  });

  if (outcome.status === 'submitted') return outcome.result;

  return {
    id: `local_${clientMutationId}`,
    surahNumber: input.surahNumber,
    surahName: input.surahName,
    fromAyah: input.fromAyah,
    toAyah: input.toAyah,
    recordedAt: new Date().toISOString(),
    durationSeconds: input.durationSeconds,
    status: 'recorded',
    pace: {
      expectedSecondsRange: [input.expectedMinSeconds, input.expectedMaxSeconds],
      actualSeconds: input.durationSeconds,
      withinExpectedRange:
        input.durationSeconds >= input.expectedMinSeconds && input.durationSeconds <= input.expectedMaxSeconds,
    },
    audioUrl: null,
    analysisStatus: 'not_analyzed',
    mistakes: [],
    isPendingSync: true,
  };
}

/**
 * Phase 14: transcribes the recording (Whisper) and word-diffs it against
 * the real ayah text — an explicit action, not automatic, since it calls
 * a paid external API and can take a few seconds. See the backend's
 * `services/arabic_text.py` for exactly what this can and can't detect.
 */
export function analyzeAttempt(attemptId: string): Promise<PracticeAttempt> {
  return apiFetch<PracticeAttempt>(`/me/practice-attempts/${attemptId}/analyze`, { method: 'POST' });
}
