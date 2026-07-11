import type { ReactNode } from 'react';
import { BottomNav } from './BottomNav';
import { OfflineBanner } from '@/components/shared/OfflineBanner';
import { useAuth } from '@/hooks/useAuth';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { user } = useAuth();
  const showBottomNav = user?.role === 'student';

  return (
    <div className="min-h-full bg-paper">
      <OfflineBanner />
      <div className={`mx-auto max-w-md min-h-full ${showBottomNav ? 'pb-24' : ''}`}>{children}</div>
      {showBottomNav && <BottomNav />}
    </div>
  );
}
