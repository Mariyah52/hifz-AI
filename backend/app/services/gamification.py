from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.gamification import Achievement
from app.models.lesson import Sabaq
from app.models.practice import PracticeAttempt
from app.models.practice_analysis import PracticeAttemptAnalysis
from app.models.test import TestSession
from app.models.user import StudentProfile, User, utcnow

"""
Every number here is computed from real rows this app already has —
practice attempts, test sessions, completed Sabaqs, streak — never a
separate mutable "XP balance" that could drift from what actually
happened. Re-deriving XP/achievements from source data on every read is
slightly more work per request than reading a cached total, but it means
there is no such thing as a wrong XP total: it's arithmetic over facts,
not state that needs to be kept in sync.

XP weights (documented here, not hidden): 5 XP per practice attempt, 10 XP
+ up to 10 bonus per test session (bonus = score_percent // 10), 100 XP
per completed Sabaq, 2 XP per day of `longest_streak` (not `current_streak`
— so XP never drops when a streak breaks, a basic gamification
expectation). These are round, easy-to-explain numbers, not tuned against
any real engagement data — there isn't any yet to tune against.
"""

XP_PER_PRACTICE_ATTEMPT = 5
XP_PER_TEST_SESSION = 10
XP_PER_COMPLETED_SABAQ = 100
XP_PER_STREAK_DAY = 2
XP_PER_LEVEL = 200


@dataclass
class XpBreakdown:
    total: int
    from_practice: int
    from_tests: int
    from_sabaqs: int
    from_streak: int


@dataclass
class LevelInfo:
    level: int
    xp_into_level: int
    xp_to_next_level: int


@dataclass
class AchievementDef:
    key: str
    name: str
    description: str


ACHIEVEMENT_DEFS: list[AchievementDef] = [
    AchievementDef("streak_7", "Week Warrior", "Reach a 7-day streak"),
    AchievementDef("streak_30", "Monthly Devotion", "Reach a 30-day streak"),
    AchievementDef("first_sabaq", "First Steps", "Complete your first Sabaq"),
    AchievementDef("ten_sabaqs", "Steady Progress", "Complete 10 Sabaqs"),
    AchievementDef("first_test", "First Test", "Complete your first Test Mode session"),
    AchievementDef("perfect_test", "Perfect Recitation", "Score 100% on a Test Mode session"),
    AchievementDef("fifty_practices", "Dedicated Practice", "Log 50 Practice Mode attempts"),
    AchievementDef("first_analysis", "AI-Assisted", "Run recitation analysis on a practice attempt"),
]
_ACHIEVEMENT_BY_KEY = {a.key: a for a in ACHIEVEMENT_DEFS}


def _counts(db: Session, student: StudentProfile) -> dict:
    practice_count = db.query(PracticeAttempt).filter(PracticeAttempt.student_id == student.id).count()
    test_sessions = db.query(TestSession).filter(TestSession.student_id == student.id).all()
    completed_sabaq_count = (
        db.query(Sabaq).filter(Sabaq.student_id == student.id, Sabaq.status == "completed").count()
    )
    has_perfect_test = any(s.score_percent == 100 for s in test_sessions)
    has_completed_analysis = (
        db.query(PracticeAttemptAnalysis)
        .join(PracticeAttempt, PracticeAttempt.id == PracticeAttemptAnalysis.attempt_id)
        .filter(PracticeAttempt.student_id == student.id, PracticeAttemptAnalysis.status == "completed")
        .first()
        is not None
    )
    return {
        "practice_count": practice_count,
        "test_sessions": test_sessions,
        "completed_sabaq_count": completed_sabaq_count,
        "has_perfect_test": has_perfect_test,
        "has_completed_analysis": has_completed_analysis,
    }


def compute_xp(db: Session, student: StudentProfile, counts: dict | None = None) -> XpBreakdown:
    counts = counts or _counts(db, student)
    from_practice = counts["practice_count"] * XP_PER_PRACTICE_ATTEMPT
    from_tests = sum(
        XP_PER_TEST_SESSION + (s.score_percent // 10) for s in counts["test_sessions"]
    )
    from_sabaqs = counts["completed_sabaq_count"] * XP_PER_COMPLETED_SABAQ
    from_streak = student.longest_streak * XP_PER_STREAK_DAY
    total = from_practice + from_tests + from_sabaqs + from_streak
    return XpBreakdown(
        total=total, from_practice=from_practice, from_tests=from_tests,
        from_sabaqs=from_sabaqs, from_streak=from_streak,
    )


def level_for_xp(xp: int) -> LevelInfo:
    level = xp // XP_PER_LEVEL + 1
    xp_into_level = xp % XP_PER_LEVEL
    return LevelInfo(level=level, xp_into_level=xp_into_level, xp_to_next_level=XP_PER_LEVEL - xp_into_level)


def _is_achievement_met(key: str, student: StudentProfile, counts: dict) -> bool:
    if key == "streak_7":
        return student.longest_streak >= 7
    if key == "streak_30":
        return student.longest_streak >= 30
    if key == "first_sabaq":
        return counts["completed_sabaq_count"] >= 1
    if key == "ten_sabaqs":
        return counts["completed_sabaq_count"] >= 10
    if key == "first_test":
        return len(counts["test_sessions"]) >= 1
    if key == "perfect_test":
        return counts["has_perfect_test"]
    if key == "fifty_practices":
        return counts["practice_count"] >= 50
    if key == "first_analysis":
        return counts["has_completed_analysis"]
    return False


def check_and_award_achievements(db: Session, student: StudentProfile) -> list[Achievement]:
    """
    Checks every achievement rule against real current data and persists
    any newly-met ones. Idempotent and safe to call on every read (see
    GET /me/gamification) rather than only from specific event hooks —
    that way it's self-healing for historical/seeded data too, instead of
    depending on having fired a hook at exactly the right past moment.
    """
    counts = _counts(db, student)
    already_earned = {
        a.achievement_key
        for a in db.query(Achievement).filter(Achievement.student_id == student.id).all()
    }

    newly_earned: list[Achievement] = []
    for definition in ACHIEVEMENT_DEFS:
        if definition.key in already_earned:
            continue
        if _is_achievement_met(definition.key, student, counts):
            achievement = Achievement(student_id=student.id, achievement_key=definition.key, earned_at=utcnow())
            db.add(achievement)
            newly_earned.append(achievement)

    if newly_earned:
        db.commit()
        for a in newly_earned:
            db.refresh(a)

    return newly_earned


def get_achievement_def(key: str) -> AchievementDef:
    return _ACHIEVEMENT_BY_KEY[key]


@dataclass
class LeaderboardEntry:
    student_id: str
    name: str
    xp: int
    level: int
    is_current_student: bool


def get_leaderboard(db: Session, student: StudentProfile, scope: str) -> list[LeaderboardEntry]:
    """
    `scope='class'` ranks only students sharing this student's class;
    `scope='all'` ranks every student in this student's organization
    (Phase 18 — previously this was every student in the whole database,
    since multi-tenancy didn't exist yet).
    """
    query = db.query(StudentProfile).join(User, User.id == StudentProfile.user_id)
    if scope == "class":
        query = query.filter(StudentProfile.class_id == student.class_id)
    else:
        query = query.filter(User.organization_id == student.user.organization_id)
    students = query.all()

    entries = []
    for s in students:
        xp = compute_xp(db, s).total
        level = level_for_xp(xp).level
        entries.append(
            LeaderboardEntry(
                student_id=s.id, name=s.user.name, xp=xp, level=level, is_current_student=s.id == student.id
            )
        )

    entries.sort(key=lambda e: e.xp, reverse=True)
    return entries
