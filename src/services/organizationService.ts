import { apiFetch } from './apiClient';

export interface OrganizationPublic {
  name: string;
  slug: string;
  primaryColor: string | null;
  secondaryColor: string | null;
  logoUrl: string | null;
  welcomeMessage: string | null;
}

/** Public branding only — name + colors, safe to call before login (see backend's organizations.py). */
export function getOrganizationPublic(slug: string): Promise<OrganizationPublic> {
  return apiFetch<OrganizationPublic>(`/organizations/${slug}/public`);
}
