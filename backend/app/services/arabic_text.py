import difflib
import re
from dataclasses import dataclass

"""
What this can and can't tell you, precisely, because it's easy to
overstate an NLP diff as more than it is:

- It compares WORDS, after stripping diacritics and normalizing common
  letter-shape variants (see `normalize_arabic` below). It cannot tell
  you whether the *vowelization* (tashkeel) was recited correctly —
  two words that differ only in diacritics look identical after this
  normalization. That's a real, known limitation, not an edge case.
- It relies on Whisper (a general-purpose speech-to-text model, not one
  fine-tuned for Quranic recitation or tajweed) to transcribe the
  recording accurately in the first place. General STT models are known
  to lean on their language model to "autocorrect" toward the statistically
  expected word, which can mask a real recitation mistake rather than
  surface it. This tool reports what Whisper heard, not ground truth.
- It says nothing about Tajweed correctness (elongation length, ghunnah,
  qalqalah, idgham, correct stopping points, articulation) — that needs
  acoustic/phonetic analysis of the audio itself, a different and
  substantially harder problem than word-level transcription diffing.

Given those limits, treat this as "did the words come out roughly right,
and which ones might need a second look" — a real, useful signal, not a
verdict on recitation quality.
"""

# Arabic diacritics: harakat/tanween/shadda/sukun (U+064B-U+065F), the
# Quranic superscript alef (U+0670), and the small Quranic annotation
# marks — waqf signs, small high letters, etc. (U+06D6-U+06ED).
_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL_RE = re.compile(r"\u0640")  # ـ kashida/elongation character, not a real letter
_WHITESPACE_RE = re.compile(r"\s+")

_LETTER_NORMALIZATION = {
    "\u0623": "\u0627",  # أ -> ا
    "\u0625": "\u0627",  # إ -> ا
    "\u0622": "\u0627",  # آ -> ا
    "\u0671": "\u0627",  # ٱ (alef wasla) -> ا
    "\u0649": "\u064A",  # ى -> ي
    "\u0629": "\u0647",  # ة -> ه
}


def normalize_arabic(text: str) -> str:
    text = _DIACRITICS_RE.sub("", text)
    text = _TATWEEL_RE.sub("", text)
    for src, dst in _LETTER_NORMALIZATION.items():
        text = text.replace(src, dst)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    normalized = normalize_arabic(text)
    return [w for w in normalized.split(" ") if w]


@dataclass
class ReferenceWord:
    word: str
    ayah_number: int


@dataclass
class Mistake:
    position: int
    mistake_type: str  # 'missing' | 'extra' | 'substituted'
    ayah_number: int | None
    reference_word: str | None
    transcribed_word: str | None


def align(reference: list[ReferenceWord], recited_text: str) -> tuple[int, list[Mistake]]:
    """
    Word-level alignment between the reference range and what was
    transcribed, using Python's stdlib `difflib` (a standard longest-
    matching-subsequence-based diff, the same class of algorithm behind
    most text diff tools — not something bespoke or unproven).

    Returns (matched_word_count, mistakes).
    """
    reference_words = [normalize_arabic(w.word) for w in reference]
    recited_words = tokenize(recited_text)

    matcher = difflib.SequenceMatcher(None, reference_words, recited_words, autojunk=False)
    matched = 0
    mistakes: list[Mistake] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            matched += i2 - i1
            continue

        ref_slice = reference[i1:i2]
        rec_slice = recited_words[j1:j2]

        if tag == "delete":
            for k, ref_word in enumerate(ref_slice):
                mistakes.append(
                    Mistake(
                        position=i1 + k, mistake_type="missing",
                        ayah_number=ref_word.ayah_number, reference_word=ref_word.word,
                        transcribed_word=None,
                    )
                )
        elif tag == "insert":
            for k, rec_word in enumerate(rec_slice):
                mistakes.append(
                    Mistake(
                        position=i1, mistake_type="extra",
                        ayah_number=None, reference_word=None, transcribed_word=rec_word,
                    )
                )
        elif tag == "replace":
            # Pair positionally where both sides have a word (a likely
            # substitution); anything left over on either side is a plain
            # missing/extra word, same as the delete/insert cases above.
            for k in range(max(len(ref_slice), len(rec_slice))):
                ref_word = ref_slice[k] if k < len(ref_slice) else None
                rec_word = rec_slice[k] if k < len(rec_slice) else None
                if ref_word is not None and rec_word is not None:
                    mistakes.append(
                        Mistake(
                            position=i1 + k, mistake_type="substituted",
                            ayah_number=ref_word.ayah_number, reference_word=ref_word.word,
                            transcribed_word=rec_word,
                        )
                    )
                elif ref_word is not None:
                    mistakes.append(
                        Mistake(
                            position=i1 + k, mistake_type="missing",
                            ayah_number=ref_word.ayah_number, reference_word=ref_word.word,
                            transcribed_word=None,
                        )
                    )
                elif rec_word is not None:
                    mistakes.append(
                        Mistake(
                            position=i1 + k, mistake_type="extra",
                            ayah_number=None, reference_word=None, transcribed_word=rec_word,
                        )
                    )

    mistakes.sort(key=lambda m: m.position)
    return matched, mistakes
