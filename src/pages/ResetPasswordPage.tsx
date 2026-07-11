import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { resetPassword } from '@/services/authService';
import { ApiError } from '@/services/apiClient';

const inputClass =
  'rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink w-full';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDone, setIsDone] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await resetPassword(token, newPassword);
      setIsDone(true);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong. The link may have expired — request a new one.',
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-full bg-paper flex items-center justify-center px-5 py-12">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="font-display text-2xl font-semibold text-ink">Set a new password</h1>
        </div>

        <Card>
          {!token ? (
            <p className="font-body text-sm text-maroon text-center py-2">
              This link is missing its reset token. Request a new one from the login page.
            </p>
          ) : isDone ? (
            <div className="flex flex-col items-center gap-3 py-2">
              <p className="font-body text-sm text-ink text-center">
                Your password has been reset. You can log in with it now.
              </p>
              <Button onClick={() => navigate('/login')} className="justify-center">
                Go to login
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                New password
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className={`${inputClass} pr-9`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-soft hover:text-ink transition-colors"
                  >
                    {showPassword ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
              </label>
              {error && <p className="text-xs text-maroon font-body">{error}</p>}
              <Button type="submit" disabled={isSubmitting} className="mt-1 justify-center">
                {isSubmitting ? 'Saving…' : 'Save new password'}
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
