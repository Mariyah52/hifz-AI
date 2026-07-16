import { useEffect } from 'react';
import { useOrganizationBranding } from './useOrganizationBranding';
import { darkenHex } from '@/utils/color';

/**
 * Bugfix: installing a "theme" from the Marketplace already updated the
 * organization's `primaryColor` server-side, but nothing in the frontend
 * ever read it back — so the install had zero visible effect. This fetches
 * the org's branding for whoever is logged in and applies it as the same
 * `--color-teal` / `--color-teal-dark` CSS variables every `teal`-*
 * Tailwind class already resolves to (see tailwind.config.js), so an
 * installed theme now actually reskins the app. Falls back to the
 * built-in default (tokens.css) whenever no custom color is set.
 *
 * `secondaryColor` maps to `--color-gold`, the app's existing accent
 * color token, the same way `primaryColor` maps to teal.
 */
export function useOrganizationTheme(): void {
  const { data } = useOrganizationBranding();

  useEffect(() => {
    const root = document.documentElement.style;
    if (data?.primaryColor) {
      root.setProperty('--color-teal', data.primaryColor);
      root.setProperty('--color-teal-dark', darkenHex(data.primaryColor));
    } else {
      root.removeProperty('--color-teal');
      root.removeProperty('--color-teal-dark');
    }

    if (data?.secondaryColor) {
      root.setProperty('--color-gold', data.secondaryColor);
    } else {
      root.removeProperty('--color-gold');
    }
  }, [data?.primaryColor, data?.secondaryColor]);
}
