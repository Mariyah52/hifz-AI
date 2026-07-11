export interface ApiKey {
  id: string;
  name: string;
  keyPrefix: string;
  createdAt: string;
  lastUsedAt: string | null;
  revokedAt: string | null;
}

/** Only returned once, from the create call — the raw key is never fetchable again after this. */
export interface ApiKeyCreated extends ApiKey {
  apiKey: string;
}
