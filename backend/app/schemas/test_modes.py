from typing import Literal

from app.schemas.base import CamelModel

TestMode = Literal[
    "continue_next_ayah",
    "continue_next_page",
    "continue_after_random_stop",
    "first_ayah_recognition",
    "last_ayah_recognition",
    "match_page",
    "match_surah",
    "random_ayah",
    "audio_question",
    "page_recall",
    "masked_page",
    "mixed_revision",
]

InteractionType = Literal["recite", "multiple_choice"]


class GeneratedQuestionOut(CamelModel):
    mode: TestMode
    interaction_type: InteractionType
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    prompt: str
    # Only set for interaction_type == 'multiple_choice'. The correct
    # answer is included immediately — like the rest of Test Mode, this
    # is a self-study tool, not a proctored exam (see test_modes.py's
    # module docstring).
    choices: list[str] | None = None
    correct_choice_index: int | None = None
    audio_first: bool = False


class GenerateTestRequest(CamelModel):
    mode: TestMode
    # Optional hint — most modes pick a completed Sabaq automatically if omitted.
    surah_number: int | None = None


class GeneratedTestOut(CamelModel):
    questions: list[GeneratedQuestionOut]
