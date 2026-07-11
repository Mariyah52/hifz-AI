const DB_NAME = 'hifzai-offline-queue';
const DB_VERSION = 1;
const QUEUE_STORE = 'mutations';

export type QueuedMutationKind = 'json' | 'multipart';

export interface QueuedMutation {
  /** Equal to the clientMutationId sent to the server — the idempotency key. */
  id: string;
  kind: QueuedMutationKind;
  endpoint: string;
  jsonBody?: unknown;
  formFields?: Record<string, string>;
  audioBlob?: Blob;
  createdAt: number;
}

/** Same vanilla-IndexedDB approach as audioCacheDb.ts — no new storage dependency for this either. */
function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) db.createObjectStore(QUEUE_STORE, { keyPath: 'id' });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function enqueueMutation(mutation: QueuedMutation): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(QUEUE_STORE, 'readwrite');
    tx.objectStore(QUEUE_STORE).put(mutation);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getAllQueuedMutations(): Promise<QueuedMutation[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const request = db.transaction(QUEUE_STORE, 'readonly').objectStore(QUEUE_STORE).getAll();
    request.onsuccess = () => resolve(request.result as QueuedMutation[]);
    request.onerror = () => reject(request.error);
  });
}

export async function removeQueuedMutation(id: string): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(QUEUE_STORE, 'readwrite');
    tx.objectStore(QUEUE_STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

export async function getQueuedMutationCount(): Promise<number> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const request = db.transaction(QUEUE_STORE, 'readonly').objectStore(QUEUE_STORE).count();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
