/**
 * Darkens a `#rrggbb` hex color by mixing it toward black — used to derive
 * a hover/pressed shade from an organization's single stored brand color
 * (there's only one `primaryColor` field; the app's own default palette
 * always ships a matching `-dark` variant, so an installed theme needs one
 * synthesized too, rather than looking flat on hover/press states).
 */
export function darkenHex(hex: string, amount = 0.3): string {
  const match = /^#?([0-9a-fA-F]{6})$/.exec(hex.trim());
  if (!match) return hex;

  const num = parseInt(match[1], 16);
  const r = Math.round(((num >> 16) & 0xff) * (1 - amount));
  const g = Math.round(((num >> 8) & 0xff) * (1 - amount));
  const b = Math.round((num & 0xff) * (1 - amount));

  return `#${[r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('')}`;
}
