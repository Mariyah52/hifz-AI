import { apiFetch } from './apiClient';
import type { ApiKey, ApiKeyCreated } from '@/types/apiKey';

export function getApiKeys(): Promise<ApiKey[]> {
  return apiFetch<ApiKey[]>('/admin/api-keys');
}

export function createApiKey(name: string): Promise<ApiKeyCreated> {
  return apiFetch<ApiKeyCreated>('/admin/api-keys', { method: 'POST', body: { name } });
}

export function revokeApiKey(keyId: string): Promise<void> {
  return apiFetch<void>(`/admin/api-keys/${keyId}`, { method: 'DELETE' });
}
