import { WifiOff, RefreshCw, CloudUpload } from 'lucide-react';
import { useOfflineSync } from '@/hooks/useOfflineSync';

export function OfflineBanner() {
  const { isOnline, pendingCount, isSyncing } = useOfflineSync();

  if (!isOnline) {
    return (
      <div className="flex items-center gap-2 justify-center bg-maroon/10 text-maroon text-xs font-body font-semibold px-4 py-2 text-center">
        <WifiOff size={14} className="shrink-0" />
        You're offline — downloaded audio and Quran text still work, and any Sabaqs, tests, or
        notes you save now will sync automatically once you're back online.
        {pendingCount > 0 && ` (${pendingCount} waiting to sync)`}
      </div>
    );
  }

  if (isSyncing || pendingCount > 0) {
    return (
      <div className="flex items-center gap-2 justify-center bg-teal/10 text-teal-dark text-xs font-body font-semibold px-4 py-2 text-center">
        {isSyncing ? <RefreshCw size={14} className="shrink-0 animate-spin" /> : <CloudUpload size={14} className="shrink-0" />}
        {isSyncing ? 'Syncing what you saved offline…' : `${pendingCount} item${pendingCount === 1 ? '' : 's'} waiting to sync`}
      </div>
    );
  }

  return null;
}
