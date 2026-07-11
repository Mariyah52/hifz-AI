from app.models.user import StudentProfile, today


def record_activity_today(student: StudentProfile) -> None:
    """
    Mutates `student` in place; caller is responsible for committing as
    part of the same transaction that records the practice/test activity.
    This is the real, server-side replacement for the frontend's old
    `progressService.recordActivityToday` — streak state now lives in one
    place (the database) instead of each browser's localStorage, and is
    updated automatically whenever real activity is recorded rather than
    needing a separate "mark active" call from the client.
    """
    today_ = today()
    if student.last_active_date == today_:
        return

    continues_streak = (
        student.last_active_date is not None and (today_ - student.last_active_date).days == 1
    )
    next_streak = student.current_streak + 1 if continues_streak else 1

    student.current_streak = next_streak
    student.longest_streak = max(student.longest_streak, next_streak)
    student.last_active_date = today_
