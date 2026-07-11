import { apiFetch } from './apiClient';
import { generateClientMutationId, submitMultipartOrQueue } from './offlineSyncService';
import type { TestSession } from '@/types/test';

export interface SubmitTestSessionInput {
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  /** The one continuous recording across the whole ayah range. */
  audioBlob: Blob;
}

/** Same note as practiceService: a plain FastAPI query param, genuinely snake_case server-side. */
export function getTestSessionsForSurah(surahNumber: number): Promise<TestSession[]> {
  return apiFetch<TestSession[]>('/me/test-sessions', { query: { surah_number: surahNumber } });
}

/**
 * Uploads the whole test recording and gets back an AI-scored result in
 * one round trip: the backend transcribes it (Whisper) and word-diffs it
 * against the real reference text for the range — see backend's
 * services/test_analysis.py. If the request can't reach the server at all
 * (offline), this queues it for later sync instead of losing the
 * recording, same pattern as practiceService.saveAttempt.
 */
export async function submitTestSession(input: SubmitTestSessionInput): Promise<TestSession> {
  const clientMutationId = generateClientMutationId();

  const outcome = await submitMultipartOrQueue<TestSession>({
    clientMutationId,
    endpoint: '/me/test-sessions',
    formFields: {
      surah_number: String(input.surahNumber),
      surah_name: input.surahName,
      from_ayah: String(input.fromAyah),
      to_ayah: String(input.toAyah),
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
    completedAt: new Date().toISOString(),
    results: [],
    scorePercent: 0,
    audioUrl: null,
    analysisStatus: 'pending',
    analysisError: null,
    matchedWordCount: 0,
    totalWordCount: 0,
    mistakes: [],
    isPendingSync: true,
  };
}

/** Retries analysis for a session that failed the first time (e.g. no OPENAI_API_KEY configured yet) — same recording, no re-recording needed. */
export function retryTestSessionAnalysis(sessionId: string): Promise<TestSession> {
  return apiFetch<TestSession>(`/me/test-sessions/${sessionId}/analyze`, { method: 'POST' });
}

export interface SubmitQuizTestSessionInput {
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
  isCorrect: boolean;
}

/**
 * For Test Modes' multiple-choice/recognition questions — already
 * objectively graded client-side (right/wrong against the generated
 * question's known answer), no audio involved at all. Kept separate from
 * `submitTestSession`, which always uploads and AI-analyzes a recording.
 */
export function submitQuizTestSession(input: SubmitQuizTestSessionInput): Promise<TestSession> {
  return apiFetch<TestSession>('/me/test-sessions/quiz', { method: 'POST', body: input });
}
