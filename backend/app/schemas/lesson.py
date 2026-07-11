from datetime import date
from typing import Literal

from app.schemas.base import CamelModel

LessonStatus = Literal["not_started", "in_progress", "completed"]


class SabaqOut(CamelModel):
    id: str
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
    assigned_date: date
    status: LessonStatus
    score: int | None = None


class AssignSabaqRequest(CamelModel):
    surah_number: int
    surah_name: str
    from_ayah: int
    to_ayah: int
