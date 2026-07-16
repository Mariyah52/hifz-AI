import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';
import { homeRouteForRole } from '@/routes/roleHome';
import { ApiError } from '@/services/apiClient';
import type { UserRole } from '@/types/user';

type Mode = 'login' | 'register';

const inputClass =
  'rounded-lg border border-ink/10 bg-paper-dim px-3 py-2 font-body text-sm text-ink w-full';

export function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<UserRole>('student');
  const [organizationSlug, setOrganizationSlug] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [staySignedIn, setStaySignedIn] = useState(true);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const user =
        mode === 'login'
          ? await login({ email, password, staySignedIn })
          : await register(
              role === 'admin'
                ? { email, password, name, role, organizationName }
                : { email, password, name, role, organizationSlug },
            );

      const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname;
      navigate(from ?? homeRouteForRole(user.role), { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-full bg-paper flex items-center justify-center px-5 py-12">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="font-display text-2xl font-semibold text-ink">HifzAI</h1>
          <p className="text-sm text-ink-soft font-body mt-1">
            {mode === 'login' ? 'Log in to continue your Hifz journey.' : 'Create an account to get started.'}
          </p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            {mode === 'register' && (
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                Name
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className={inputClass}
                />
              </label>
            )}

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

            <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
              Password
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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

            {mode === 'login' && (
              <div className="flex items-center justify-between -mt-1">
                <label className="flex items-center gap-1.5 text-xs text-ink-soft font-body cursor-pointer">
                  <input
                    type="checkbox"
                    checked={staySignedIn}
                    onChange={(e) => setStaySignedIn(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-ink/20 accent-teal"
                  />
                  Stay signed in
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-ink-soft font-body hover:text-ink transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
            )}

            {mode === 'register' && (
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                I am a
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  className={inputClass}
                >
                  <option value="student">Student</option>
                  <option value="parent">Parent</option>
                  <option value="teacher">Teacher</option>
                  <option value="admin">Admin — create a new institution</option>
                </select>
              </label>
            )}

            {mode === 'register' && role === 'admin' && (
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                Institution name
                <input
                  type="text"
                  required
                  placeholder="e.g. Green Valley Madrasa"
                  value={organizationName}
                  onChange={(e) => setOrganizationName(e.target.value)}
                  className={inputClass}
                />
                <span className="text-[11px] text-ink-soft">
                  This creates a brand-new institution with you as its first admin.
                </span>
              </label>
            )}

            {mode === 'register' && role !== 'admin' && (
              <label className="flex flex-col gap-1 text-xs text-ink-soft font-body">
                Organization code
                <input
                  type="text"
                  required
                  placeholder="e.g. hifzai-demo"
                  value={organizationSlug}
                  onChange={(e) => setOrganizationSlug(e.target.value)}
                  className={inputClass}
                />
                <span className="text-[11px] text-ink-soft">
                  Ask your institution's admin for this code.
                </span>
              </label>
            )}

            {error && <p className="text-xs text-maroon font-body">{error}</p>}

            <Button type="submit" disabled={isSubmitting} className="mt-1 justify-center">
              {isSubmitting ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}
            </Button>
          </form>
        </Card>

        <button
          onClick={() => {
            setError(null);
            setMode((m) => (m === 'login' ? 'register' : 'login'));
          }}
          className="w-full text-center text-xs text-ink-soft font-body mt-4 hover:text-ink transition-colors"
        >
          {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Log in'}
        </button>

      </div>
    </div>
  );
}
