import { getGlobalAyahNumber } from './quranService';
import { API_BASE_URL } from './apiClient';
import type { Reciter } from '@/types/quran';

export const HUSARY: Reciter = {
  id: 'husary',
  name: 'Mahmoud Khalil Al-Husary',
  arabicName: 'محمود خليل الحصري',
};

/**
 * Islamic Network / Al Quran Cloud CDN. Ayah audio is addressed by global
 * ayah number (1-6236), not surah:ayah, which is exactly what
 * quranService.getGlobalAyahNumber gives us — Phase 2 paying off here.
 *
 * RECITER_EDITION is the one thing to double-check before shipping: verify
 * it against the live, always-current list at
 * https://api.alquran.cloud/v1/edition/format/audio. If ayah audio ever
 * 404s, this is the only line that needs to change — nothing in Learn Mode
 * UI references the CDN directly.
 */
const CDN_BASE = 'https://cdn.islamic.network/quran/audio';
const RECITER_EDITION = 'ar.husary';
const DEFAULT_BITRATE = 128;

export function getReciter(): Reciter {
  return HUSARY;
}

export function getAyahAudioUrl(surahNumber: number, ayahNumber: number, bitrate = DEFAULT_BITRATE): string {
  const globalAyahNumber = getGlobalAyahNumber(surahNumber, ayahNumber);
  return `${CDN_BASE}/${bitrate}/${RECITER_EDITION}/${globalAyahNumber}.mp3`;
}

/**
 * Same audio, routed through this app's own backend instead of the CDN
 * directly — used only for offline download (see audioCacheService.ts).
 * The CDN sends no Access-Control-Allow-Origin header, so a browser
 * fetch()+blob() download is silently blocked by CORS even though an
 * <audio> tag plays the same URL fine. Playback keeps using
 * getAyahAudioUrl() above unchanged; only the download path needs this.
 */
export function getAyahAudioDownloadUrl(surahNumber: number, ayahNumber: number, bitrate = DEFAULT_BITRATE): string {
  const globalAyahNumber = getGlobalAyahNumber(surahNumber, ayahNumber);
  return new URL(`/media/quran-audio/${bitrate}/${globalAyahNumber}`, API_BASE_URL).toString();
}
