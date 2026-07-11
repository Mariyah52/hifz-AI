import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { createApiKey, getApiKeys, revokeApiKey } from '@/services/apiKeyService';
import type { ApiKeyCreated } from '@/types/apiKey';

export function useApiKeys() {
  const queryClient = useQueryClient();
  const [justCreated, setJustCreated] = useState<ApiKeyCreated | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const keysQuery = useQuery({ queryKey: ['admin', 'api-keys'], queryFn: getApiKeys });

  async function create(name: string): Promise<ApiKeyCreated> {
    setIsCreating(true);
    try {
      const created = await createApiKey(name);
      setJustCreated(created);
      await queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] });
      return created;
    } finally {
      setIsCreating(false);
    }
  }

  async function revoke(keyId: string): Promise<void> {
    await revokeApiKey(keyId);
    await queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] });
  }

  return {
    keys: keysQuery.data ?? [],
    isLoading: keysQuery.isLoading,
    isCreating,
    justCreated,
    dismissJustCreated: () => setJustCreated(null),
    create,
    revoke,
  };
}
