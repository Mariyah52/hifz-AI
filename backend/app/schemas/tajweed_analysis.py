from app.schemas.base import CamelModel


class ElongationFlagOut(CamelModel):
    word: str
    ayah_number: int
    rule: str
    expected_minimum_seconds: float
    actual_seconds: float


class TajweedAnalysisOut(CamelModel):
    flags: list[ElongationFlagOut]
    words_checked_for_elongation: int
    note: str = (
        "This checks elongation (madd) timing only, using the student's own "
        "recording as its baseline. It does not check ghunnah, qalqalah, "
        "articulation points, or any other tajweed rule — those need "
        "acoustic analysis this feature doesn't attempt yet."
    )
