import { useEffect, useMemo, useState } from 'react';
import { useSurah } from '@/hooks/useQuranData';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';
import { useRecorder } from '@/hooks/useRecorder';
import { submitTestSession, retryTestSessionAnalysis } from '@/services/testService';
import { rangeArray } from '@/utils/range';
import type { TestSession } from '@/types/test';

export type TestPhase = 'setup' | 'analyzing' | 'complete';

interface UseTestSessionArgs {
  surahNumber: number;
  surahName: string;
  fromAyah: number;
  toAyah: number;
}

/**
 * One continuous recording across the whole from_ayah..to_ayah range,
 * analyzed by the backend's real Whisper + word-diff pipeline (see
 * services/test_analysis.py) — replaces the old per-ayah listen-recite-
 * reveal-and-self-mark loop. The student records once, the AI corrects it
 * at the end; there's no student self-report step anymore.
 */
export function useTestSession({ surahNumber, surahName, fromAyah, toAyah }: UseTestSessionArgs) {
  const surah = useSurah(surahNumber);
  const ayahNumbers = useMemo(() => rangeArray(fromAyah, toAyah), [fromAyah, toAyah]);

  const [phase, setPhase] = useState<TestPhase>('setup');
  const [session, setSession] = useState<TestSession | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const player = useAudioPlayer({
    surahNumber,
    ayahNumbers: ayahNumbers.length > 0 ? ayahNumbers : [fromAyah],
    rangeStart: fromAyah,
    rangeEnd: toAyah,
  });

  // Preview plays straight through the tested range (not Learn Mode's
  // pick-any-mode picker) — this is "hear what you're about to be tested
  // on," bounded to just that range.
  useEffect(() => {
    player.setRepeatMode('range');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const recorder = useRecorder();

  function startRecording() {
    player.pause();
    setSubmitError(null);
    recorder.start();
  }

  function stopRecording() {
    recorder.stop();
  }

  // Once the one continuous recording stops, upload it and get back an
  // AI-scored result — no separate "reveal + mark yourself" step.
  useEffect(() => {
    if (recorder.status === 'stopped' && recorder.audioBlob) {
      setPhase('analyzing');
      submitTestSession({ surahNumber, surahName, fromAyah, toAyah, audioBlob: recorder.audioBlob })
        .then((result) => {
          setSession(result);
          setPhase('complete');
        })
        .catch(() => {
          setSubmitError("Couldn't submit your recording — check your connection and try again.");
          recorder.reset();
          setPhase('setup');
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recorder.status]);

  async function retryAnalysis() {
    if (!session) return;
    setPhase('analyzing');
    try {
      const updated = await retryTestSessionAnalysis(session.id);
      setSession(updated);
    } finally {
      setPhase('complete');
    }
  }

  function recordAgain() {
    recorder.reset();
    setSession(null);
    setSubmitError(null);
    setPhase('setup');
  }

  return {
    surah,
    totalAyahs: ayahNumbers.length,
    phase,
    session,
    submitError,
    isReferencePlaying: player.isPlaying,
    toggleReference: player.toggle,
    startRecording,
    stopRecording,
    retryAnalysis,
    recordAgain,
    recorder,
  };
}
