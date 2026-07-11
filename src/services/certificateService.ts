import { API_BASE_URL, apiFetch, getToken } from './apiClient';
import type { Certificate } from '@/types/certificate';

export function getMyCertificates(): Promise<Certificate[]> {
  return apiFetch<Certificate[]>('/me/certificates');
}

/**
 * The PDF endpoint returns raw bytes, not JSON, so this bypasses
 * apiFetch (which assumes a JSON body) and fetches the Blob directly
 * with the same Bearer token, then triggers a normal browser download —
 * a plain `<a href>` can't attach an Authorization header itself.
 */
export async function downloadCertificatePdf(certificateId: string, filename: string): Promise<void> {
  const token = getToken();
  const response = await fetch(new URL(`/me/certificates/${certificateId}/pdf`, API_BASE_URL), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error('Could not download this certificate.');

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}
