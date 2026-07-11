import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { requestPasswordReset } from '@/services/authService';

const inputClass =
  'rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink w-full';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await requestPasswordReset(email);
    } finally {
      // Shown regardless of outcome — the backend never reveals whether
      // the email exists either, so the UI shouldn't leak that either.
      setIsSubmitting(false);
      setIsSubmitted(true);
    }
  }

  return (
    <div className="min-h-full bg-paper flex items-center justify-center px-5 py-12">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="font-display text-2xl font-semibold text-ink">Reset your password</h1>
          <p className="text-sm text-ink-soft font-body mt-1">
            Enter your account email and, if it exists, we'll send a reset link.
          </p>
        </div>

        <Card>
          {isSubmitted ? (
            <p className="font-body text-sm text-ink text-center py-2">
              If that email is registered, a reset link is on its way. Check your inbox.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                Email
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClass}
                />
              </label>
              <Button type="submit" disabled={isSubmitting} className="mt-1 justify-center">
                {isSubmitting ? 'Sending…' : 'Send reset link'}
              </Button>
            </form>
          )}
        </Card>

        <Link
          to="/login"
          className="block w-full text-center text-xs text-ink-soft font-body mt-4 hover:text-ink transition-colors"
        >
          Back to login
        </Link>
      </div>
    </div>
  );
}
