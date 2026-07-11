from datetime import date

from app.schemas.base import CamelModel
from app.schemas.lesson import SabaqOut


class ReviewScheduleOut(CamelModel):
    repetition_number: int
    ease_factor: float
    interval_days: int
    due_date: date
    last_reviewed_date: date | None


class DueReviewOut(CamelModel):
    sabaq: SabaqOut
    schedule: ReviewScheduleOut
