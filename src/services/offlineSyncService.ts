import { apiFetch, ApiError } from './apiClient';
import {
  enqueueMutation,
  getAllQueuedMutations,
  getQueuedMutationCount,
  removeQueuedMutation,
  type QueuedMutation,
} from './offlineQueueDb';

/**
 * A real network failure (no connection, DNS failure, request never
 * reached the server) surfaces from `fetch()` as a TypeError in every
 * major browser — that's the standard, if slightly implicit, way to
 * distinguish "couldn't reach the server at all" from "reached it and
 * got an error back" (an ApiError, e.g. a validation 400 or an expired
 * session). Only the former should be queued for later — queuing a real
 * validation error would just resubmit the same invalid request forever.
 */
function isNetworkFailure(error: unknown): boolean {
  return error instanceof TypeError;
}

export function generateClientMutationId(): string {
  return crypto.randomUUID();
}

interface SubmitOrQueueJsonInput {
  clientMutationId: string;
  endpoint: string;
  jsonBody: unknown;
}

interface SubmitOrQueueMultipartInput {
  clientMutationId: string;
  endpoint: string;
  formFields: Record<string, string>;
  audioBlob?: Blob | null;
}

export type SubmitOutcome<T> = { status: 'submitted'; result: T } | { status: 'queued' };

export async function submitJsonOrQueue<T>(input: SubmitOrQueueJsonInput): Promise<SubmitOutcome<T>> {
  try {
    const result = await apiFetch<T>(input.endpoint, { method: 'POST', body: input.jsonBody });
    return { status: 'submitted', result };
  } catch (error) {
    if (!isNetworkFailure(error)) throw error;
    await enqueueMutation({
      id: input.clientMutationId,
      kind: 'json',
      endpoint: input.endpoint,
      jsonBody: input.jsonBody,
      createdAt: Date.now(),
    });
    return { status: 'queued' };
  }
}

export async function submitMultipartOrQueue<T>(input: SubmitOrQueueMultipartInput): Promise<SubmitOutcome<T>> {
  const form = new FormData();
  Object.entries(input.formFields).forEach(([key, value]) => form.set(key, value));
  if (input.audioBlob) form.set('audio', input.audioBlob, 'attempt.webm');

  try {
    const result = await apiFetch<T>(input.endpoint, { method: 'POST', formData: form });
    return { status: 'submitted', result };
  } catch (error) {
    if (!isNetworkFailure(error)) throw error;
    await enqueueMutation({
      id: input.clientMutationId,
      kind: 'multipart',
      endpoint: input.endpoint,
      formFields: input.formFields,
      audioBlob: input.audioBlob ?? undefined,
      createdAt: Date.now(),
    });
    return { status: 'queued' };
  }
}

export async function getPendingSyncCount(): Promise<number> {
  return getQueuedMutationCount();
}

async function replay(mutation: QueuedMutation): Promise<void> {
  if (mutation.kind === 'json') {
    await apiFetch(mutation.endpoint, { method: 'POST', body: mutation.jsonBody });
    return;
  }
  const form = new FormData();
  Object.entries(mutation.formFields ?? {}).forEach(([key, value]) => form.set(key, value));
  if (mutation.audioBlob) form.set('audio', mutation.audioBlob, 'attempt.webm');
  await apiFetch(mutation.endpoint, { method: 'POST', formData: form });
}

/**
 * Flushes every queued mutation, oldest first. Each one includes the same
 * clientMutationId it was queued under, so if a mutation actually
 * succeeded server-side on a previous attempt (e.g. the response was
 * lost even though the write landed), the server's idempotency check
 * returns the existing row instead of creating a duplicate — see the
 * backend's client_mutation_id columns.
 *
 * Stops at the first network failure so a temporarily-still-offline
 * state doesn't spin through every item; keeps going past a single
 * permanently-rejected item instead of blocking everything behind it.
 */
export async function flushQueue(): Promise<{ synced: number; remaining: number }> {
  const mutations = await getAllQueuedMutations();
  const ordered = [...mutations].sort((a, b) => a.createdAt - b.createdAt);

  let synced = 0;
  for (const mutation of ordered) {
    try {
      await replay(mutation);
      await removeQueuedMutation(mutation.id);
      synced += 1;
    } catch (error) {
      if (isNetworkFailure(error)) {
        break;
      }
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        await removeQueuedMutation(mutation.id);
        continue;
      }
      // A server error (5xx) — leave it queued, worth retrying later.
    }
  }

  const remaining = await getQueuedMutationCount();
  return { synced, remaining };
}
