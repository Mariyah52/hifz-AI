import { Link } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { useUnreadNotificationCount } from '@/hooks/useUnreadNotificationCount';

interface NotificationBellButtonProps {
  sizeClass?: string;
}

export function NotificationBellButton({ sizeClass = 'h-10 w-10' }: NotificationBellButtonProps) {
  const { data: unreadCount } = useUnreadNotificationCount();

  return (
    <Link
      to="/notifications"
      aria-label={unreadCount ? `Notifications (${unreadCount} unread)` : 'Notifications'}
      className={`relative grid ${sizeClass} place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors`}
    >
      <Bell size={18} />
      {!!unreadCount && (
        <span className="absolute top-1 right-1 grid h-4 w-4 place-items-center rounded-full bg-maroon text-paper text-[9px] font-mono font-bold">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </Link>
  );
}
