from app.schemas.base import CamelModel


class DailyActivity(CamelModel):
    date: str
    practice_count: int
    test_count: int
    test_average_score: float | None


class ProgressSummary(CamelModel):
    memorized_ayah_count: int
    total_ayah_count: int
    completion_percent: float
    current_streak: int
    longest_streak: int
    total_practice_attempts: int
    total_test_sessions: int
    overall_average_test_score: float | None
    weekly_activity: list[DailyActivity]
    monthly_activity: list[DailyActivity]
