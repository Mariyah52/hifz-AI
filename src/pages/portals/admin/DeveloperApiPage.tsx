import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, Code2, Copy, Trash2 } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { useApiKeys } from '@/hooks/useApiKeys';

/**
 * Phase 30 — admin-only. Manages public API keys for the read-only
 * integration API (`/v1/students`, `/v1/students/:id/progress`,
 * `/v1/classes`) that lets a school's ERP, a mosque's own systems, or an
 * LMS pull real data out of HifzAI via an `X-API-Key` header. The raw
 * key is shown exactly once, right after creation — this page never
 * fetches it again afterward, because the backend never stores it
 * (see `services/api_key_service.py`).
 */
export function DeveloperApiPage() {
  const { keys, isLoading, isCreating, justCreated, dismissJustCreated, create, revoke } = useApiKeys();
  const [name, setName] = useState('');
  const [copied, setCopied] = useState(false);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await create(name.trim());
    setName('');
  }

  function copyKey() {
    if (!justCreated) return;
    navigator.clipboard.writeText(justCreated.apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <>
      <header className="flex items-center gap-3 px-5 pt-6 pb-2">
        <Link
          to="/admin"
          aria-label="Back to Admin"
          className="grid h-9 w-9 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
        >
          <ChevronLeft size={18} />
        </Link>
        <div>
          <p className="text-sm text-ink-soft font-body">Admin</p>
          <h1 className="font-display text-xl font-semibold text-ink flex items-center gap-2">
            <Code2 size={18} /> Developer API
          </h1>
        </div>
      </header>

      <main className="px-5 mt-2 pb-4 flex flex-col gap-5">
        <Card className="bg-sage/40 border-none">
          <p className="font-body text-xs text-ink-soft">
            Read-only integration API for a school ERP, a mosque's own systems, or an LMS. Send an{' '}
            <code className="font-mono">X-API-Key</code> header with each request to authenticate.
          </p>
          <p className="font-body text-xs text-ink-soft mt-3">
            Every key is scoped to this organization only. Read-only — there's no write/push API yet.
          </p>
        </Card>

        {justCreated && (
          <Card className="border-2 border-teal">
            <p className="font-body text-sm font-semibold text-ink">Key created — copy it now</p>
            <p className="font-body text-xs text-ink-soft mt-1">
              This is the only time the full key is shown. It isn't stored anywhere retrievable.
            </p>
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-paper-dim px-3 py-2">
              <code className="font-mono text-xs text-ink flex-1 truncate">{justCreated.apiKey}</code>
              <button
                onClick={copyKey}
                aria-label="Copy key"
                className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
              >
                <Copy size={13} />
              </button>
            </div>
            {copied && <p className="font-mono text-[10px] text-teal-dark mt-1">Copied.</p>}
            <button onClick={dismissJustCreated} className="mt-3 font-body text-xs text-ink-soft underline">
              Done
            </button>
          </Card>
        )}

        <Card>
          <p className="font-body font-semibold text-ink text-sm mb-2">Create a new key</p>
          <form onSubmit={handleCreate} className="flex items-center gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. School ERP integration"
              className="flex-1 rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink"
            />
            <button
              type="submit"
              disabled={isCreating || !name.trim()}
              className="rounded-full bg-teal text-paper font-semibold text-xs px-4 py-2 hover:bg-teal-dark transition-colors disabled:opacity-50"
            >
              {isCreating ? 'Creating…' : 'Create'}
            </button>
          </form>
        </Card>

        <section>
          <h3 className="font-display text-base font-semibold text-ink mb-3">Active keys</h3>
          {isLoading && <p className="text-center text-ink-soft font-body text-sm py-4">Loading…</p>}
          {!isLoading && keys.length === 0 && (
            <Card>
              <p className="font-body text-sm text-ink-soft">No API keys yet.</p>
            </Card>
          )}
          <div className="flex flex-col gap-2">
            {keys.map((key) => (
              <Card key={key.id} className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-body font-semibold text-ink text-sm truncate">{key.name}</p>
                  <p className="font-mono text-xs text-ink-soft mt-0.5">
                    {key.keyPrefix}… ·{' '}
                    {key.revokedAt
                      ? 'Revoked'
                      : key.lastUsedAt
                        ? `Last used ${new Date(key.lastUsedAt).toLocaleDateString()}`
                        : 'Never used'}
                  </p>
                </div>
                {!key.revokedAt && (
                  <button
                    onClick={() => revoke(key.id)}
                    aria-label="Revoke key"
                    className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-sage text-ink-soft hover:bg-[#d8dfcd] transition-colors"
                  >
                    <Trash2 size={15} />
                  </button>
                )}
              </Card>
            ))}
          </div>
        </section>
      </main>
    </>
  );
}
