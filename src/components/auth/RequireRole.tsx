import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { homeRouteForRole } from '@/routes/roleHome';
import type { UserRole } from '@/types/user';

interface RequireRoleProps {
  role: UserRole;
}

export function RequireRole({ role }: RequireRoleProps) {
  const { user } = useAuth();

  // RequireAuth (always the parent route) guarantees `user` is set by the
  // time this renders, but the check keeps this component safe standalone.
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={homeRouteForRole(user.role)} replace />;

  return <Outlet />;
}
