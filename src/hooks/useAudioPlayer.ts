import { useEffect, useRef, useState } from 'react';
import { getPlayableAyahUrl } from '@/services/audioCacheService';
import type { RepeatMode } from '@/types/lesson';

interface UseAudioPlayerArgs {
  surahNumber: number;
  /** All ayah numbers available to play, in order (e.g. 1..ayahCount). */
  ayahNumbers: number[];
  /** Bounds for 'range' repeat mode. Defaults to the full ayahNumbers span. */
  rangeStart?: number;
  rangeEnd?: number;
}

export const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 2] as const;
export type PlaybackRate = (typeof PLAYBACK_RATES)[number];

export const REPEAT_GAP_OPTIONS_SECONDS = [0, 1, 2, 3, 5] as const;

export function useAudioPlayer({ surahNumber, ayahNumbers, rangeStart, rangeEnd }: UseAudioPlayerArgs) {
  const [audio] = useState(() => new Audio());
  const [currentAyah, setCurrentAyah] = useState<number>(rangeStart ?? ayahNumbers[0]);
  const [isPlaying, setIsPlayingState] = useState(false);
  const [isBuffering, setIsBuffering] = useState(false);
  const [playbackRate, setPlaybackRate] = useState<PlaybackRate>(1);
  const [repeatGapSeconds, setRepeatGapSeconds] = useState<number>(0);

  const [repeatMode, setRepeatMode] = useState<RepeatMode>('single');

  const objectUrlRef = useRef<string | null>(null);
  const gapTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function clearPendingGap() {
    if (gapTimeoutRef.current !== null) {
      clearTimeout(gapTimeoutRef.current);
      gapTimeoutRef.current = null;
    }
  }

  // Resolve and load the current ayah's audio whenever surah/ayah changes.
  // Async now (Phase 11): checks the offline cache first via
  // `getPlayableAyahUrl` (IndexedDB) and falls back to the live CDN URL —
  // same behavior online, and actually playable offline once downloaded.
  useEffect(() => {
    let cancelled = false;
    clearPendingGap();
    setIsBuffering(true);

    getPlayableAyahUrl(surahNumber, currentAyah).then((url) => {
      if (cancelled) {
        // A newer ayah change already superseded this lookup — if we just
        // created a blob URL for it, release it immediately rather than
        // leaking it (it was never assigned anywhere, so nothing else
        // will ever revoke it).
        if (url.startsWith('blob:')) URL.revokeObjectURL(url);
        return;
      }
      // Revoke the previous object URL (if any) now that we're done with it —
      // network URLs are left alone since there's nothing to revoke.
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
      if (url.startsWith('blob:')) objectUrlRef.current = url;

      audio.src = url;
      audio.playbackRate = playbackRate;
      setIsBuffering(false);
      if (isPlaying) {
        audio.play().catch(() => setIsPlayingState(false));
      }
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audio, surahNumber, currentAyah]);

  // Keep the <audio> element's rate in sync without needing a new source load.
  useEffect(() => {
    audio.playbackRate = playbackRate;
  }, [audio, playbackRate]);

  // Repeat-mode logic: what happens when the current ayah's audio ends,
  // after waiting `repeatGapSeconds` (Phase 11 — previously instant).
  useEffect(() => {
    const start = rangeStart ?? ayahNumbers[0];
    const end = rangeEnd ?? ayahNumbers[ayahNumbers.length - 1];

    function advance() {
      if (repeatMode === 'single') {
        audio.currentTime = 0;
        audio.play().catch(() => setIsPlayingState(false));
        return;
      }
      const next = currentAyah + 1;
      if (repeatMode === 'range') {
        setCurrentAyah(next > end ? start : next);
        return;
      }
      // continuous: play through to the end of the surah, then loop from the start
      const lastAyah = ayahNumbers[ayahNumbers.length - 1];
      setCurrentAyah(next > lastAyah ? ayahNumbers[0] : next);
    }

    function handleEnded() {
      if (repeatGapSeconds <= 0) {
        advance();
        return;
      }
      gapTimeoutRef.current = setTimeout(advance, repeatGapSeconds * 1000);
    }

    audio.addEventListener('ended', handleEnded);
    return () => audio.removeEventListener('ended', handleEnded);
  }, [audio, repeatMode, currentAyah, rangeStart, rangeEnd, ayahNumbers, repeatGapSeconds]);

  // Stop audio and clean up on unmount (e.g. navigating away).
  useEffect(() => {
    return () => {
      audio.pause();
      clearPendingGap();
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audio]);

  function play() {
    setIsPlayingState(true);
    audio.play().catch(() => setIsPlayingState(false));
  }

  function pause() {
    setIsPlayingState(false);
    clearPendingGap();
    audio.pause();
  }

  function toggle() {
    if (isPlaying) pause();
    else play();
  }

  function goToAyah(ayahNumber: number) {
    clearPendingGap();
    setCurrentAyah(ayahNumber);
  }

  return {
    currentAyah,
    isPlaying,
    isBuffering,
    repeatMode,
    setRepeatMode,
    playbackRate,
    setPlaybackRate,
    repeatGapSeconds,
    setRepeatGapSeconds,
    play,
    pause,
    toggle,
    goToAyah,
  };
}
