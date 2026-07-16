import difflib
import os
import statistics
from dataclasses import dataclass

from app.config import settings
from app.models.practice import PracticeAttempt
from app.services.arabic_text import normalize_arabic
from app.services.quran_text import ELONGATION_RULE_MIN_COUNTS, TajweedWord, get_tajweed_annotated_words
from app.services.transcription import TranscriptionError, WordTiming, transcribe_audio_with_word_timestamps

"""
Phase 34: AI Tajweed analysis -- v1, elongation (madd) only.

READ THIS BEFORE ASSUMING THIS DETECTS TAJWEED MISTAKES IN GENERAL. It
detects exactly one thing: whether a word tajweed scholarship requires
to be elongated (a madd rule) was actually held for a plausible length,
using real timing data. It does NOT detect, and makes no attempt at:

  - Ghunnah (nasalization) -- needs acoustic/spectral analysis of nasal
    resonance, not just timing. Out of scope for this module entirely.
  - Qalqalah (the "bounce"/plosive release on letters at a stop) --
    needs detecting a specific acoustic event, not timing. Out of scope.
  - Idgham, ikhfa, iqlab, or any other assimilation/nasalization rule --
    same reason, all need acoustic analysis this module doesn't do.
  - Correct articulation point (makhraj) of any letter -- needs phonetic
    classification of the actual sound produced, not timing.
  - Precise mora/harakah counting -- a real qari holds a madd for an
    exact count (2, 4, or 6 harakahs at a specific tempo). This module
    can only tell you a word's elongation was RELATIVELY short compared
    to the student's own other words in the same recording, not that it
    was exactly N harakahs. It is a rushedness signal, not a metronome.

WHY THIS IS STILL A REAL, HONEST v1 AND NOT A GUESS: both of its inputs
are real, not estimated --
  1. WHICH words need elongation, and by how much, comes from the same
     tajweed-tagged Quran text this app's own frontend already displays
     (quran_text.py's get_tajweed_annotated_words) -- real scholarly
     annotation, not this app's invention.
  2. HOW LONG the student actually held each word comes from Whisper's
     real word-level timestamps (transcription.py's
     transcribe_audio_with_word_timestamps) -- real measured audio timing,
     not estimated by dividing total duration evenly across words.

METHOD: compute the median duration of the student's own non-elongated
matched words in this recording as a personal baseline (so a naturally
fast or slow reciter is compared against themselves, not a fixed
absolute threshold). For each matched word that carries an elongation
rule, its expected minimum duration is
`baseline_duration * ELONGATION_RULE_MIN_COUNTS[rule] / 2` (the "/2"
because a plain, non-elongated syllable is itself roughly 1-2 harakahs;
dividing by 2 keeps this conservative and biased toward NOT flagging,
since false alarms erode trust in a coaching tool faster than an
occasional missed flag). A word is flagged only if its actual duration
falls below `expected_minimum * FLAG_TOLERANCE`.
"""

FLAG_TOLERANCE = 0.75  # actual duration must be below 75% of the (already conservative) expected minimum to flag


@dataclass
class ElongationFlag:
    word: str
    ayah_number: int
    rule: str
    expected_minimum_seconds: float
    actual_seconds: float


def _align_reference_to_timings(
    tajweed_words: list[TajweedWord], word_timings: list[WordTiming]
) -> list[tuple[TajweedWord, WordTiming]]:
    """
    Same difflib word-level alignment approach as arabic_text.align(),
    reused here for consistency rather than inventing a second alignment
    algorithm -- but returning matched (reference, timing) PAIRS instead
    of just a mistake list, since duration-checking needs both sides of
    a match, not just whether it matched.
    """
    reference_normalized = [normalize_arabic(w.word) for w in tajweed_words]
    transcribed_normalized = [normalize_arabic(t.word) for t in word_timings]

    matcher = difflib.SequenceMatcher(None, reference_normalized, transcribed_normalized, autojunk=False)
    pairs: list[tuple[TajweedWord, WordTiming]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                pairs.append((tajweed_words[i1 + offset], word_timings[j1 + offset]))
    return pairs


def analyze_elongation(
    tajweed_words: list[TajweedWord], word_timings: list[WordTiming]
) -> list[ElongationFlag]:
    matched_pairs = _align_reference_to_timings(tajweed_words, word_timings)
    if not matched_pairs:
        return []

    non_elongated_durations = [
        timing.end_seconds - timing.start_seconds
        for ref, timing in matched_pairs
        if ref.elongation_rule is None
    ]
    if len(non_elongated_durations) < 3:
        # Too little data for a personal baseline to mean anything --
        # deliberately returns no flags rather than guessing off a
        # near-empty sample. A short recording (a single ayah with
        # mostly elongated words) is exactly the case where this matters
        # most.
        return []
    baseline_duration = statistics.median(non_elongated_durations)

    flags: list[ElongationFlag] = []
    for ref, timing in matched_pairs:
        if ref.elongation_rule is None:
            continue
        min_counts = ELONGATION_RULE_MIN_COUNTS[ref.elongation_rule]
        expected_minimum = baseline_duration * min_counts / 2
        actual = timing.end_seconds - timing.start_seconds
        if actual < expected_minimum * FLAG_TOLERANCE:
            flags.append(
                ElongationFlag(
                    word=ref.word, ayah_number=ref.ayah_number, rule=ref.elongation_rule,
                    expected_minimum_seconds=round(expected_minimum, 2), actual_seconds=round(actual, 2),
                )
            )
    return flags


class TajweedAnalysisError(Exception):
    pass


@dataclass
class TajweedAnalysisResult:
    """
    Not persisted to the database -- computed fresh on each call. A
    deliberate v1 simplification: this feature is new enough, and its
    methodology likely to be refined (see FLAG_TOLERANCE and the "/2"
    conservatism factor above), that persisting results now would mean
    either a migration to re-run old analyses later or stale flags stuck
    in the database under an outdated methodology. Revisit persistence
    once the approach has proven itself with real usage.
    """
    flags: list[ElongationFlag]
    words_checked_for_elongation: int


async def analyze_tajweed_for_attempt(attempt: PracticeAttempt) -> TajweedAnalysisResult:
    if not attempt.audio_url:
        raise TajweedAnalysisError("This attempt has no uploaded recording to analyze.")
    relative_path = attempt.audio_url.removeprefix("/media/")
    audio_path = os.path.join(settings.media_root, relative_path)
    if not os.path.isfile(audio_path):
        raise TajweedAnalysisError("No audio file found for this attempt.")

    try:
        tajweed_words = await get_tajweed_annotated_words(
            attempt.surah_number, attempt.from_ayah, attempt.to_ayah
        )
        word_timings = await transcribe_audio_with_word_timestamps(audio_path)
    except TranscriptionError as exc:
        raise TajweedAnalysisError(str(exc)) from exc

    flags = analyze_elongation(tajweed_words, word_timings)
    words_with_elongation_rules = sum(1 for w in tajweed_words if w.elongation_rule is not None)
    return TajweedAnalysisResult(flags=flags, words_checked_for_elongation=words_with_elongation_rules)
