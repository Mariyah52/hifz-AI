import type { UserRole } from '@/types/user';

export function homeRouteForRole(role: UserRole): string {
  switch (role) {
    case 'student':
      return '/';
    case 'teacher':
      return '/teacher';
    case 'parent':
      return '/parent';
    case 'admin':
      return '/admin';
  }
}
