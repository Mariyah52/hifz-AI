import type { UserRole } from './user';

export interface AuthUser {
  id: string;
  name: string;
  role: UserRole;
  organizationSlug: string;
}
