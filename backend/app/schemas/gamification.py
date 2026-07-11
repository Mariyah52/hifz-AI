from datetime import datetime

from app.schemas.base import CamelModel


class AchievementOut(CamelModel):
    key: str
    name: str
    description: str
    earned_at: datetime | None = None  # None only in the "locked" list


class GamificationSummary(CamelModel):
    xp: int
    level: int
    xp_into_level: int
    xp_to_next_level: int
    earned_achievements: list[AchievementOut]
    locked_achievements: list[AchievementOut]


class LeaderboardEntryOut(CamelModel):
    rank: int
    student_id: str
    name: str
    xp: int
    level: int
    is_current_student: bool
