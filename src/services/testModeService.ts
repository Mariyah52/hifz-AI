import { apiFetch } from './apiClient';
import type { GeneratedTest, TestMode } from '@/types/testModes';

export function generateTest(mode: TestMode, surahNumber?: number): Promise<GeneratedTest> {
  return apiFetch<GeneratedTest>('/me/tests/generate', {
    method: 'POST',
    body: { mode, surahNumber },
  });
}
