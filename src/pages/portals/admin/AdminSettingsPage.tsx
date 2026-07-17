import { useEffect, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useAdminOrganizationSettings } from '@/hooks/useAdminOrganizationSettings';

const DEFAULT_PRIMARY = '#2f6f5e';
const DEFAULT_SECONDARY = '#b8860b';

export function AdminSettingsPage() {
  const { organization, isLoading, isSaving, save } = useAdminOrganizationSettings();

  const [name, setName] = useState('');
  const [primaryColor, setPrimaryColor] = useState(DEFAULT_PRIMARY);
  const [secondaryColor, setSecondaryColor] = useState(DEFAULT_SECONDARY);
  const [logoUrl, setLogoUrl] = useState('');
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [principalMessage, setPrincipalMessage] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!organization) return;
    setName(organization.name);
    setPrimaryColor(organization.primaryColor ?? DEFAULT_PRIMARY);
    setSecondaryColor(organization.secondaryColor ?? DEFAULT_SECONDARY);
    setLogoUrl(organization.logoUrl ?? '');
    setWelcomeMessage(organization.welcomeMessage ?? '');
    setPrincipalMessage(organization.principalMessage ?? '');
  }, [organization]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaved(false);
    await save({
      name: name.trim() || undefined,
      primaryColor,
      secondaryColor,
      logoUrl: logoUrl.trim(),
      welcomeMessage: welcomeMessage.trim(),
      principalMessage: principalMessage.trim(),
    });
    setSaved(true);
  }

  if (isLoading || !organization) {
    return <div className="p-5 text-ink-soft font-body text-sm">Loading…</div>;
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/"
          aria-label="Back to dashboard"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Admin</p>
          <h1 className="heading-section">Branding &amp; settings</h1>
        </div>
      </header>

      <main className="px-5 flex flex-col gap-4 mt-2 pb-4">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Card>
            <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-3">
              Institution
            </p>
            <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
              Name
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
              />
            </label>
          </Card>

          <Card>
            <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-3">
              Colors
            </p>
            <div className="flex items-center gap-6">
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                Primary
                <input
                  type="color"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="h-10 w-16 rounded border border-ink/10 bg-paper-dim"
                />
              </label>
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                Secondary
                <input
                  type="color"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  className="h-10 w-16 rounded border border-ink/10 bg-paper-dim"
                />
              </label>
            </div>
          </Card>

          <Card>
            <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-3">
              Logo
            </p>
            <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
              Logo URL
              <input
                type="text"
                placeholder="https://…"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
              />
            </label>
            {logoUrl && (
              <img
                src={logoUrl}
                alt="Logo preview"
                className="mt-3 h-14 w-14 rounded-full object-cover border border-ink/10"
              />
            )}
          </Card>

          <Card>
            <p className="text-[11px] uppercase tracking-widest text-ink-soft font-mono mb-3">
              Messages
            </p>
            <label className="flex flex-col gap-1 text-xs text-ink-soft font-body mb-3">
              Welcome message
              <span className="text-[11px] text-ink-soft">Shown on the login page — visible to everyone, even before signing in.</span>
              <textarea
                value={welcomeMessage}
                onChange={(e) => setWelcomeMessage(e.target.value)}
                rows={2}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink resize-none"
              />
            </label>
            <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
              Principal's message
              <span className="text-[11px] text-ink-soft">Only visible to signed-in members of your organization.</span>
              <textarea
                value={principalMessage}
                onChange={(e) => setPrincipalMessage(e.target.value)}
                rows={3}
                className="rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink resize-none"
              />
            </label>
          </Card>

          {saved && <p className="font-body text-xs text-teal-dark">Saved.</p>}

          <button
            type="submit"
            disabled={isSaving}
            className="rounded-full bg-teal text-paper font-semibold text-sm py-3 hover:bg-teal-dark transition-colors disabled:opacity-60"
          >
            {isSaving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </main>
    </>
  );
}
