import random

from sqlalchemy.orm import Session

from app.models.lesson import Sabaq
from app.models.user import StudentProfile
from app.schemas.test_modes import GeneratedQuestionOut, TestMode
from app.services.quran_text import get_ayah_positions, get_surah_ayah_texts, get_surah_list

"""
Every question generated here is built from real data: the student's own
completed Sabaqs (never invented ranges), and ayah text/juz/page/surah
metadata fetched live from the same verified source the rest of this app
uses (see quran_text.py) — never hand-typed.

Two interaction types, reused across all 12 modes rather than building a
bespoke UI per mode:
  - "recite": exactly the existing Test Mode flow (hide text, listen,
    record, self-mark) — `TestRunner` on the frontend needs zero changes
    to run any of these, it just receives a different surah/ayah range.
  - "multiple_choice": a prompt + 4 answer choices, revealed immediately
    on selection. Like the rest of Test Mode, this is a self-study tool,
    not a proctored exam — the correct answer is available to the client
    right away, the same trust model Test Mode's self-marked recitation
    already uses. No anti-cheat grading server was built, on purpose.
"""


class NoContentAvailable(Exception):
    pass


def _completed_sabaqs(db: Session, student_id: str, surah_number: int | None = None) -> list[Sabaq]:
    query = db.query(Sabaq).filter(Sabaq.student_id == student_id, Sabaq.status == "completed")
    if surah_number is not None:
        query = query.filter(Sabaq.surah_number == surah_number)
    return query.all()


def _pick_sabaq(db: Session, student_id: str, surah_number: int | None) -> Sabaq:
    sabaqs = _completed_sabaqs(db, student_id, surah_number)
    if not sabaqs:
        raise NoContentAvailable("No completed Sabaqs yet to generate a test from.")
    return random.choice(sabaqs)


async def _page_span(surah_number: int, ayah_number: int) -> tuple[int, int] | None:
    """The full [from_ayah, to_ayah] range sharing this ayah's page, within the same surah."""
    positions = await get_ayah_positions(surah_number)
    page = positions.get(ayah_number, {}).get("page")
    if page is None:
        return None
    same_page = [a for a, pos in positions.items() if pos.get("page") == page]
    return (min(same_page), max(same_page))


async def _generate_recite_question(
    db: Session, student: StudentProfile, mode: TestMode, surah_number: int | None
) -> GeneratedQuestionOut:
    sabaq = _pick_sabaq(db, student.id, surah_number)

    if mode == "continue_next_page" or mode == "page_recall":
        span = await _page_span(sabaq.surah_number, sabaq.from_ayah)
        from_ayah, to_ayah = span if span else (sabaq.from_ayah, sabaq.to_ayah)
        prompt = (
            "Recall and recite everything on this page from memory."
            if mode == "page_recall"
            else "Recite the whole page, continuing past where this Sabaq ends if the page does."
        )
    elif mode == "continue_after_random_stop":
        from_ayah = random.randint(sabaq.from_ayah, sabaq.to_ayah)
        to_ayah = sabaq.to_ayah
        prompt = f"Pick up from ayah {from_ayah} and continue reciting to the end of this Sabaq."
    elif mode == "random_ayah":
        single = random.randint(sabaq.from_ayah, sabaq.to_ayah)
        from_ayah = to_ayah = single
        prompt = "Recite this single ayah."
    elif mode == "audio_question":
        single = random.randint(sabaq.from_ayah, sabaq.to_ayah)
        from_ayah = to_ayah = single
        prompt = "Listen to the reference audio, then continue reciting from where it stops."
    elif mode == "masked_page":
        single = random.randint(sabaq.from_ayah, sabaq.to_ayah)
        from_ayah = to_ayah = single
        prompt = f"The ayah at position {single} in this Sabaq is hidden — recite it from memory."
    else:  # continue_next_ayah — the original/default Test Mode behavior
        from_ayah, to_ayah = sabaq.from_ayah, sabaq.to_ayah
        prompt = "Continue reciting this Sabaq."

    return GeneratedQuestionOut(
        mode=mode, interaction_type="recite",
        surah_number=sabaq.surah_number, surah_name=sabaq.surah_name,
        from_ayah=from_ayah, to_ayah=to_ayah, prompt=prompt,
        audio_first=(mode == "audio_question"),
    )


async def _generate_first_last_ayah_question(
    db: Session, student: StudentProfile, mode: TestMode, surah_number: int | None
) -> GeneratedQuestionOut:
    sabaq = _pick_sabaq(db, student.id, surah_number)
    ayahs = await get_surah_ayah_texts(sabaq.surah_number)
    if len(ayahs) < 4:
        raise NoContentAvailable("This surah is too short to generate distractor choices.")

    target_ayah_number, target_text = ayahs[0] if mode == "first_ayah_recognition" else ayahs[-1]
    distractor_pool = [text for number, text in ayahs if number != target_ayah_number and text != target_text]
    distractors = random.sample(distractor_pool, min(3, len(distractor_pool)))

    choices = [target_text, *distractors]
    random.shuffle(choices)

    which = "first" if mode == "first_ayah_recognition" else "last"
    return GeneratedQuestionOut(
        mode=mode, interaction_type="multiple_choice",
        surah_number=sabaq.surah_number, surah_name=sabaq.surah_name,
        from_ayah=target_ayah_number, to_ayah=target_ayah_number,
        prompt=f"Which of these is the {which} ayah of Surah {sabaq.surah_name}?",
        choices=choices, correct_choice_index=choices.index(target_text),
    )


async def _generate_match_page_question(
    db: Session, student: StudentProfile, surah_number: int | None
) -> GeneratedQuestionOut:
    sabaq = _pick_sabaq(db, student.id, surah_number)
    target_ayah = random.randint(sabaq.from_ayah, sabaq.to_ayah)
    positions = await get_ayah_positions(sabaq.surah_number)
    correct_page = positions.get(target_ayah, {}).get("page")
    if correct_page is None:
        raise NoContentAvailable("Page data isn't available for this ayah right now.")

    ayahs = dict(await get_surah_ayah_texts(sabaq.surah_number))
    distractor_pages = list({correct_page + delta for delta in (-2, -1, 1, 2) if correct_page + delta > 0})
    random.shuffle(distractor_pages)
    choices_pages = [correct_page, *distractor_pages[:3]]
    random.shuffle(choices_pages)

    return GeneratedQuestionOut(
        mode="match_page", interaction_type="multiple_choice",
        surah_number=sabaq.surah_number, surah_name=sabaq.surah_name,
        from_ayah=target_ayah, to_ayah=target_ayah,
        prompt=f"Which page is this ayah on?\n{ayahs.get(target_ayah, '')}",
        choices=[str(p) for p in choices_pages], correct_choice_index=choices_pages.index(correct_page),
    )


async def _generate_match_surah_question(
    db: Session, student: StudentProfile, surah_number: int | None
) -> GeneratedQuestionOut:
    sabaq = _pick_sabaq(db, student.id, surah_number)
    target_ayah = random.randint(sabaq.from_ayah, sabaq.to_ayah)
    ayahs = dict(await get_surah_ayah_texts(sabaq.surah_number))

    all_surahs = await get_surah_list()
    other_surahs = [s for s in all_surahs if s["number"] != sabaq.surah_number]
    distractors = random.sample(other_surahs, min(3, len(other_surahs)))

    choices = [sabaq.surah_name, *[s["name"] for s in distractors]]
    random.shuffle(choices)

    return GeneratedQuestionOut(
        mode="match_surah", interaction_type="multiple_choice",
        surah_number=sabaq.surah_number, surah_name=sabaq.surah_name,
        from_ayah=target_ayah, to_ayah=target_ayah,
        prompt=f"Which surah is this ayah from?\n{ayahs.get(target_ayah, '')}",
        choices=choices, correct_choice_index=choices.index(sabaq.surah_name),
    )


async def generate_question(
    db: Session, student: StudentProfile, mode: TestMode, surah_number: int | None = None
) -> GeneratedQuestionOut:
    if mode in ("first_ayah_recognition", "last_ayah_recognition"):
        return await _generate_first_last_ayah_question(db, student, mode, surah_number)
    if mode == "match_page":
        return await _generate_match_page_question(db, student, surah_number)
    if mode == "match_surah":
        return await _generate_match_surah_question(db, student, surah_number)
    # Every other mode is a "recite" question over a different ayah range.
    return await _generate_recite_question(db, student, mode, surah_number)


async def generate_mixed_revision(
    db: Session, student: StudentProfile, count: int = 4
) -> list[GeneratedQuestionOut]:
    """
    A short sequence of varied questions across different completed
    Sabaqs — run one after another client-side, each still recorded as
    its own real Test Mode session. Modes are sampled from the ones that
    don't require a specific surah hint, so this works with whatever the
    student has actually completed.
    """
    sampleable_modes: list[TestMode] = [
        "continue_next_ayah", "random_ayah", "continue_after_random_stop",
        "first_ayah_recognition", "last_ayah_recognition", "match_surah",
    ]
    questions: list[GeneratedQuestionOut] = []
    attempts = 0
    while len(questions) < count and attempts < count * 3:
        attempts += 1
        mode = random.choice(sampleable_modes)
        try:
            questions.append(await generate_question(db, student, mode))
        except NoContentAvailable:
            continue
    if not questions:
        raise NoContentAvailable("No completed Sabaqs yet to generate a mixed revision session from.")
    return questions
