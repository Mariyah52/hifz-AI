import { useNavigate } from 'react-router-dom';
import { ChevronLeft, Bell, BellOff } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useNotifications } from '@/hooks/useNotifications';
import { usePushNotifications } from '@/hooks/usePushNotifications';
import { useAuth } from '@/hooks/useAuth';
import { homeRouteForRole } from '@/routes/roleHome';
import type { AppNotification } from '@/types/notification';

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function NotificationRow({ notification, onRead }: { notification: AppNotification; onRead: () => void }) {
  return (
    <button
      onClick={onRead}
      className={`w-full text-left rounded-2xl px-4 py-3 transition-colors ${
        notification.isRead ? 'bg-paper-dim' : 'bg-teal/10 hover:bg-teal/15'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="font-body font-semibold text-ink text-sm">{notification.title}</p>
        <span className="font-mono text-[11px] text-ink-soft shrink-0">{timeAgo(notification.createdAt)}</span>
      </div>
      <p className="font-body text-xs text-ink-soft mt-1">{notification.body}</p>
    </button>
  );
}

export function NotificationsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { notifications, isLoading, markRead, markAllRead } = useNotifications();
  const { isSupported, isSubscribed, isBusy, error, subscribe, unsubscribe } = usePushNotifications();

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <>
      <header className="flex items-center justify-between gap-3 px-5 pt-6 pb-2">
        <div className="flex items-center gap-3">
          <button
            aria-label="Back"
            onClick={() => navigate(user ? homeRouteForRole(user.role) : '/')}
            className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
          >
            <ChevronLeft size={18} />
          </button>
          <div>
            <p className="text-sm text-ink-soft font-body">Notifications</p>
            <h1 className="font-display text-xl font-semibold text-ink">
              {isLoading ? 'Loading…' : unreadCount > 0 ? `${unreadCount} unread` : 'All caught up'}
            </h1>
          </div>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={() => markAllRead()}
            className="text-xs font-body font-semibold text-teal-dark hover:text-teal-dark/80 transition-colors"
          >
            Mark all read
          </button>
        )}
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-4">
        <Card>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {isSubscribed ? <Bell size={16} className="text-teal-dark" /> : <BellOff size={16} className="text-ink-soft" />}
              <p className="font-body text-sm text-ink">Push notifications</p>
            </div>
            <button
              onClick={() => (isSubscribed ? unsubscribe() : subscribe())}
              disabled={isBusy || !isSupported}
              className="text-xs font-body font-semibold text-teal-dark hover:text-teal-dark/80 transition-colors disabled:opacity-50"
            >
              {isBusy ? 'Working…' : isSubscribed ? 'Turn off' : 'Turn on'}
            </button>
          </div>
          {!isSupported && (
            <p className="font-body text-xs text-ink-soft mt-2">Not supported in this browser.</p>
          )}
          {error && <p className="font-body text-xs text-maroon mt-2">{error}</p>}
        </Card>

        {!isLoading && notifications.length === 0 && (
          <Card className="text-center py-8">
            <p className="font-body text-sm text-ink-soft">Nothing here yet.</p>
          </Card>
        )}

        <div className="flex flex-col gap-2">
          {notifications.map((n) => (
            <NotificationRow key={n.id} notification={n} onRead={() => !n.isRead && markRead(n.id)} />
          ))}
        </div>
      </main>
    </>
  );
}
