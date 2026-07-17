import { LogOut } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useOrganizationBranding } from '@/hooks/useOrganizationBranding';
import { NotificationBellButton } from '@/components/shared/NotificationBellButton';

interface OrganizationBannerProps {
  roleLabel: string;
  /** Overrides the org's generic welcomeMessage with something personal (e.g. "Good morning, Ahmad"). Falls back to welcomeMessage when omitted. */
  subtitle?: string;
}

/**
 * The app's "front of house" — an illuminated-manuscript letterhead for
 * top-level portal home pages (Admin/Teacher/Parent/Student). Distinct
 * from the plain `Header` used on inner tool pages (Practice, Live Coach,
 * etc.): those stay quiet and functional, this is the one place the
 * teal/gold "mushaf illumination" identity (see tokens.css) gets to be
 * bold instead of a small accent on a button or badge.
 *
 * The lattice pattern is a repeating 8-point star/diamond motif rendered
 * as an inline SVG data URI — a simplified nod to classical Islamic
 * geometric border ornament, kept at low opacity so it reads as texture,
 * not decoration competing with the name/logo.
 */
const LATTICE_SVG = `data:image/svg+xml,${encodeURIComponent(`
  <svg xmlns='http://www.w3.org/2000/svg' width='36' height='36'>
    <g fill='none' stroke='%23faf3e4' stroke-width='1'>
      <path d='M18 2 L26 10 L18 18 L10 10 Z' />
      <path d='M18 18 L26 26 L18 34 L10 26 Z' />
      <path d='M0 18 L8 10 L16 18 L8 26 Z' />
      <path d='M20 18 L28 10 L36 18 L28 26 Z' />
    </g>
  </svg>
`)}`;

export function OrganizationBanner({ roleLabel, subtitle }: OrganizationBannerProps) {
  const { logout } = useAuth();
  const { data: branding } = useOrganizationBranding();

  const orgName = branding?.name ?? 'HifzAI';
  const monogram = orgName.trim().charAt(0).toUpperCase();

  return (
    <div className="relative overflow-hidden bg-teal">
      <div className="h-[3px] bg-gold" />
      <div
        className="absolute inset-0 opacity-[0.08] pointer-events-none"
        style={{ backgroundImage: `url("${LATTICE_SVG}")`, backgroundSize: '36px 36px' }}
      />
      <div className="relative flex items-center justify-between px-5 py-5">
        <div className="flex items-center gap-3 animate-rise-in">
          {branding?.logoUrl ? (
            <img
              src={branding.logoUrl}
              alt={`${orgName} logo`}
              className="h-12 w-12 rounded-full object-cover border-2 border-gold"
            />
          ) : (
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-full border-2 border-gold text-gold font-display text-xl font-semibold">
              {monogram}
            </div>
          )}
          <div>
            <p className="text-[11px] uppercase tracking-widest text-gold font-mono">{roleLabel}</p>
            <h1 className="font-display text-2xl font-semibold text-paper">{orgName}</h1>
            {(subtitle ?? branding?.welcomeMessage) && (
              <p className="text-paper/70 text-xs font-body mt-0.5 max-w-sm">
                {subtitle ?? branding?.welcomeMessage}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <NotificationBellButton />
          <button
            aria-label="Log out"
            onClick={logout}
            className="grid h-10 w-10 place-items-center rounded-full bg-paper/15 text-paper hover:bg-paper/25 transition-colors"
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
      <div className="h-[3px] bg-gold" />
    </div>
  );
}
