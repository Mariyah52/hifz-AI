"""
Populates the database with real rows equivalent to the mock fixtures the
frontend used through Phases 1, 7, 8, and 9 (`mockDashboard.ts`,
`mockStudents.ts`, `mockTeachers.ts`) — same people, same numbers, just
persisted for real instead of hardcoded in TypeScript. Safe to re-run:
it skips seeding if the demo teacher account already exists.

Usage (from backend/):
    alembic upgrade head   # Phase 17: schema comes from migrations now,
                           # not an auto-create call in this script
    python -m app.seed
"""

from datetime import date, timedelta

from app.database import SessionLocal
from app.models.classroom import ClassRoom, ParentChildLink
from app.models.feedback import TeacherFeedback
from app.models.lesson import Sabaq
from app.models.practice import PracticeAttempt
from app.models.organization import Organization
from app.models.review import ReviewSchedule
from app.models.test import TestResult, TestSession
from app.models.user import ParentProfile, StudentProfile, TeacherProfile, User
from app.security import hash_password

DEMO_PASSWORD = "hifzai-demo-2026"


def seed() -> None:
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == "bilal.teacher@hifzai.demo").first():
            print("Seed data already present — skipping.")
            return

        # --- Organization (Phase 18) ----------------------------------------
        demo_org = Organization(
            name="HifzAI Demo Academy", slug="hifzai-demo", plan="free", max_students=30, max_teachers=5,
        )
        db.add(demo_org)
        db.flush()

        # --- Teachers -------------------------------------------------
        bilal_user = User(
            organization_id=demo_org.id,
            email="bilal.teacher@hifzai.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            name="Ustadh Bilal Rahman",
            role="teacher",
        )
        maryam_user = User(
            organization_id=demo_org.id,
            email="maryam.teacher@hifzai.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            name="Ustadha Maryam Yusuf",
            role="teacher",
        )
        db.add_all([bilal_user, maryam_user])
        db.flush()

        bilal = TeacherProfile(user_id=bilal_user.id)
        maryam = TeacherProfile(user_id=maryam_user.id)
        db.add_all([bilal, maryam])
        db.flush()

        # --- Classes ----------------------------------------------------
        class_1 = ClassRoom(name="Halaqah 1 — Morning", teacher_id=bilal.id, organization_id=demo_org.id)
        class_2 = ClassRoom(name="Halaqah 2 — Afternoon", teacher_id=maryam.id, organization_id=demo_org.id)
        db.add_all([class_1, class_2])
        db.flush()

        # --- Students -----------------------------------------------------
        yusuf_user = User(
            organization_id=demo_org.id,
            email="yusuf.student@hifzai.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            name="Yusuf Ahmed",
            role="student",
        )
        amina_user = User(
            organization_id=demo_org.id,
            email="amina.student@hifzai.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            name="Amina Khalil",
            role="student",
        )
        omar_user = User(
            organization_id=demo_org.id,
            email="omar.student@hifzai.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            name="Omar Siddiqui",
            role="student",
        )
        db.add_all([yusuf_user, amina_user, omar_user])
        db.flush()

        yusuf = StudentProfile(
            user_id=yusuf_user.id, class_id=class_1.id,
            current_streak=12, longest_streak=21, last_active_date=date.today(), freezes_available=2,
        )
        amina = StudentProfile(
            user_id=amina_user.id, class_id=class_1.id,
            current_streak=21, longest_streak=21, last_active_date=date.today(), freezes_available=1,
        )
        omar = StudentProfile(
            user_id=omar_user.id, class_id=class_2.id,
            current_streak=0, longest_streak=6, last_active_date=date.today() - timedelta(days=6),
            freezes_available=0,
        )
        db.add_all([yusuf, amina, omar])
        db.flush()

        # --- Parent, linked to Yusuf --------------------------------------
        parent_user = User(
            organization_id=demo_org.id,
            email="parent@hifzai.demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            name="Ahmed family",
            role="parent",
        )
        db.add(parent_user)
        db.flush()
        parent_profile = ParentProfile(user_id=parent_user.id)
        db.add(parent_profile)
        db.flush()
        db.add(ParentChildLink(parent_id=parent_profile.id, student_id=yusuf.id))

        # --- Admin --------------------------------------------------------
        db.add(
            User(
                organization_id=demo_org.id,
                email="admin@hifzai.demo",
                hashed_password=hash_password(DEMO_PASSWORD),
                name="Institution Admin",
                role="admin",
            )
        )

        # --- Sabaq history --------------------------------------------------
        yusuf_sabaq_today = Sabaq(
            student_id=yusuf.id, surah_number=2, surah_name="Al-Baqarah",
            from_ayah=142, to_ayah=152, assigned_date=date.today(), status="in_progress",
        )
        yusuf_sabaq_2days = Sabaq(
            student_id=yusuf.id, surah_number=2, surah_name="Al-Baqarah",
            from_ayah=130, to_ayah=141, assigned_date=date.today() - timedelta(days=2),
            status="completed", score=92,
        )
        yusuf_sabaq_3days = Sabaq(
            student_id=yusuf.id, surah_number=2, surah_name="Al-Baqarah",
            from_ayah=118, to_ayah=129, assigned_date=date.today() - timedelta(days=3),
            status="completed", score=88,
        )
        yusuf_sabaq_4days = Sabaq(
            student_id=yusuf.id, surah_number=2, surah_name="Al-Baqarah",
            from_ayah=105, to_ayah=117, assigned_date=date.today() - timedelta(days=4),
            status="completed", score=95,
        )
        yusuf_sabaq_3weeks = Sabaq(
            student_id=yusuf.id, surah_number=2, surah_name="Al-Baqarah",
            from_ayah=90, to_ayah=104, assigned_date=date.today() - timedelta(days=21),
            status="completed", score=90,
        )
        amina_sabaq_today = Sabaq(
            student_id=amina.id, surah_number=18, surah_name="Al-Kahf",
            from_ayah=1, to_ayah=10, assigned_date=date.today(), status="not_started",
        )
        db.add_all(
            [
                yusuf_sabaq_today,
                yusuf_sabaq_2days,
                yusuf_sabaq_3days,
                yusuf_sabaq_4days,
                yusuf_sabaq_3weeks,
                amina_sabaq_today,
            ]

        )
        db.flush()

        # --- Spaced-repetition schedules (Phase 13) -------------------------
        # A few completed Sabaqs already in SM-2 rotation, so the demo
        # accounts show real due/overdue reviews instead of an empty state:
        #  - the 2-days-ago Sabaq: reviewed once already, due today
        #  - the 4-days-ago Sabaq: never reviewed since completion, overdue
        #  - the 3-weeks-ago Sabaq: several successful reviews in, longer
        #    interval, still overdue — this is the "Manzil" (older) slot
        #  - the 3-days-ago Sabaq: deliberately left with NO schedule yet,
        #    to demonstrate it only enters rotation once actually reviewed
        db.add_all(
            [
                ReviewSchedule(
                    sabaq_id=yusuf_sabaq_2days.id, student_id=yusuf.id,
                    repetition_number=1, ease_factor=2.5, interval_days=1,
                    due_date=date.today(), last_reviewed_date=date.today() - timedelta(days=1),
                ),
                ReviewSchedule(
                    sabaq_id=yusuf_sabaq_4days.id, student_id=yusuf.id,
                    repetition_number=0, ease_factor=2.5, interval_days=0,
                    due_date=date.today() - timedelta(days=1), last_reviewed_date=None,
                ),
                ReviewSchedule(
                    sabaq_id=yusuf_sabaq_3weeks.id, student_id=yusuf.id,
                    repetition_number=3, ease_factor=2.6, interval_days=15,
                    due_date=date.today() - timedelta(days=2),
                    last_reviewed_date=date.today() - timedelta(days=17),
                ),
            ]
        )

        # --- Practice attempts ---------------------------------------------
        db.add(
            PracticeAttempt(
                student_id=yusuf.id, surah_number=2, surah_name="Al-Baqarah",
                from_ayah=130, to_ayah=141, duration_seconds=74,
                expected_min_seconds=60, expected_max_seconds=144, within_expected_range=True,
            )
        )

        # --- Test sessions + results -----------------------------------------
        yusuf_session = TestSession(
            student_id=yusuf.id, surah_number=2, surah_name="Al-Baqarah",
            from_ayah=118, to_ayah=120, score_percent=67, analysis_status="completed",
        )
        db.add(yusuf_session)
        db.flush()
        db.add_all(
            [
                TestResult(session_id=yusuf_session.id, ayah_number=118, mark="correct", matched_word_count=8, total_word_count=8),
                TestResult(session_id=yusuf_session.id, ayah_number=119, mark="correct", matched_word_count=10, total_word_count=10),
                TestResult(session_id=yusuf_session.id, ayah_number=120, mark="missed", matched_word_count=6, total_word_count=9),
            ]
        )

        amina_session = TestSession(
            student_id=amina.id, surah_number=18, surah_name="Al-Kahf",
            from_ayah=1, to_ayah=5, score_percent=100, analysis_status="completed",
        )
        db.add(amina_session)
        db.flush()
        db.add_all(
            [
                TestResult(session_id=amina_session.id, ayah_number=n, mark="correct", matched_word_count=10, total_word_count=10)
                for n in range(1, 6)
            ]
        )

        # --- Teacher feedback --------------------------------------------
        db.add_all(
            [
                TeacherFeedback(
                    student_id=amina.id, teacher_id=bilal.id,
                    note="Excellent tajweed on the madd letters this week — keep it up.",
                ),
                TeacherFeedback(
                    student_id=omar.id, teacher_id=maryam.id,
                    note="Hasn't logged a Sabaq in 5 days — worth a check-in.",
                ),
            ]
        )

        db.commit()
        print("Seed data created. Demo accounts (all use the same password):")
        print(f"  organization: {demo_org.name} (slug: {demo_org.slug})")
        print(f"  password: {DEMO_PASSWORD}")
        print("  teacher:  bilal.teacher@hifzai.demo / maryam.teacher@hifzai.demo")
        print("  student:  yusuf.student@hifzai.demo / amina.student@hifzai.demo / omar.student@hifzai.demo")
        print("  parent:   parent@hifzai.demo  (linked to Yusuf Ahmed)")
        print("  admin:    admin@hifzai.demo")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
