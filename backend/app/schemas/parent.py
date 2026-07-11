from app.schemas.base import CamelModel
from app.schemas.lesson import SabaqOut
from app.schemas.progress import ProgressSummary
from app.schemas.teacher import TeacherFeedbackOut
from app.schemas.user import StreakInfo


class ChildOverviewOut(CamelModel):
    student_id: str
    name: str
    class_id: str | None
    streak: StreakInfo
    todays_sabaq: SabaqOut | None
    recent_sabaqs: list[SabaqOut]
    progress: ProgressSummary
    feedback: list[TeacherFeedbackOut]
