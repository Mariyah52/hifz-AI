import { LogOut } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useOrganizationBranding } from '@/hooks/useOrganizationBranding';
import { NotificationBellButton } from '@/components/shared/NotificationBellButton';

interface HeaderProps {
  greeting: string;
  name: string;
}

export function Header({ greeting, name }: HeaderProps) {
  const { logout } = useAuth();
  const { data: branding } = useOrganizationBranding();

  return (
    <header className="flex items-center justify-between px-5 pt-6 pb-2">
      <div className="flex items-center gap-3 animate-rise-in">
        {branding?.logoUrl && (
          <img
            src={branding.logoUrl}
            alt={`${branding.name} logo`}
            className="h-10 w-10 rounded-full object-cover border border-ink/10"
          />
        )}
        <div>
          <p className="text-sm text-ink-soft font-body">{greeting}</p>
          <h1 className="heading-page">{name}</h1>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <NotificationBellButton />
        <button
          aria-label="Log out"
          onClick={logout}
          className="grid h-10 w-10 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
