import { useCallback, useEffect, useRef, useState } from 'react';
import { useOnlineStatus } from './useOnlineStatus';
import { flushQueue, getPendingSyncCount } from '@/services/offlineSyncService';

const PERIODIC_RETRY_MS = 60_000;

export function useOfflineSync() {
  const isOnline = useOnlineStatus();
  const [pendingCount, setPendingCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const isFlushingRef = useRef(false);

  const refreshPendingCount = useCallback(async () => {
    setPendingCount(await getPendingSyncCount());
  }, []);

  const syncNow = useCallback(async () => {
    if (isFlushingRef.current) return;
    isFlushingRef.current = true;
    setIsSyncing(true);
    try {
      await flushQueue();
    } catch {
      // flushQueue already leaves failed-for-real-reasons items queued;
      // a thrown error here just means the attempt itself didn't complete cleanly.
    } finally {
      await refreshPendingCount();
      isFlushingRef.current = false;
      setIsSyncing(false);
    }
  }, [refreshPendingCount]);

  useEffect(() => {
    refreshPendingCount();
  }, [refreshPendingCount]);

  useEffect(() => {
    if (isOnline) syncNow();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOnline]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (isOnline) syncNow();
    }, PERIODIC_RETRY_MS);
    return () => clearInterval(interval);
  }, [isOnline, syncNow]);

  return { isOnline, pendingCount, isSyncing, syncNow };
}
