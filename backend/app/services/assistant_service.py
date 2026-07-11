from datetime import date

from sqlalchemy.orm import Session

from app.models.chat import ChatConversation, ChatMessage
from app.models.user import StudentProfile
from app.schemas.assistant import ChatMessageOut
from app.services.analytics import build_advanced_analytics
from app.services.llm_service import LLMError, run_chat_with_tools
from app.services.progress_analytics import build_progress_summary
from app.services.spaced_repetition import get_due_reviews
from app.services.student_view import get_todays_sabaq, to_streak_info

"""
The point of this file is the boundary it draws: the LLM is allowed to
call these tools to learn real facts about the student, and is
instructed (via SYSTEM_PROMPT) to answer questions about the student's
own progress ONLY using what a tool actually returns — never inventing a
missed-page count, a streak, or a "generated" revision schedule that
isn't the real one from spaced_repetition.get_due_reviews. General
Quran/tajweed knowledge questions ("explain this rule") are answered from
the model's own training, with an explicit caveat that it isn't a
substitute for a qualified teacher's in-person correction — this app has
never claimed AI authority over recitation correctness (see Phase 14's
recitation-analysis limits), and the assistant doesn't get to claim it either.
"""

SYSTEM_PROMPT = """You are HifzAI's study assistant, helping a student who is memorizing the Quran (Hifz).

Rules you must follow:
1. When asked about the student's own progress, weak spots, streak, due reviews, or "what should I revise" — ALWAYS call the relevant tool first and base your answer only on what it returns. Never invent a page number, streak length, or accuracy figure.
2. If asked to "generate a revision schedule" or similar, call get_due_reviews and present those real due Sabaqs as the schedule. Do not invent a schedule that isn't grounded in that real data. If nothing is due, say so honestly rather than making something up to revise.
3. You may explain general Quran/tajweed concepts (e.g. idgham, qalqalah, madd rules) from your own knowledge. Always make clear this is general educational information, not a certified ruling on the student's own recitation — a qualified teacher should verify that in person.
4. Be warm, concise, and encouraging, like a caring tutor — not a long lecture unless asked to explain something in depth.
5. If a tool reports there's no data yet (e.g. no completed Sabaqs, no due reviews), say that plainly and encouragingly rather than guessing.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weak_spots",
            "description": (
                "Get the student's real weakest juz, weakest surah, weakest pages, and "
                "most-forgotten ayah, computed from their actual Test Mode history."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_due_reviews",
            "description": (
                "Get the student's real list of Sabaqs currently due for spaced-repetition "
                "review, most overdue first — use this for any 'what should I revise' or "
                "'generate a revision schedule' request."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress_summary",
            "description": (
                "Get the student's real current streak, longest streak, memorized-ayah "
                "completion percentage, and recent practice/test activity counts."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def _execute_tool(db: Session, student: StudentProfile, name: str, _args: dict) -> dict:
    if name == "get_weak_spots":
        analytics = await build_advanced_analytics(db, student)
        return analytics.model_dump()

    if name == "get_due_reviews":
        due = get_due_reviews(db, student.id)
        today = date.today()
        return {
            "dueCount": len(due),
            "items": [
                {
                    "surahName": sabaq.surah_name,
                    "fromAyah": sabaq.from_ayah,
                    "toAyah": sabaq.to_ayah,
                    "daysOverdue": (today - schedule.due_date).days,
                }
                for sabaq, schedule in due
            ],
        }

    if name == "get_progress_summary":
        progress = build_progress_summary(db, student)
        streak = to_streak_info(student)
        todays_sabaq = get_todays_sabaq(db, student.id)
        return {
            "currentStreak": streak.current_streak,
            "longestStreak": streak.longest_streak,
            "completionPercent": progress.completion_percent,
            "totalPracticeAttempts": progress.total_practice_attempts,
            "totalTestSessions": progress.total_test_sessions,
            "overallAverageTestScore": progress.overall_average_test_score,
            "todaysSabaq": (
                f"{todays_sabaq.surah_name} {todays_sabaq.from_ayah}-{todays_sabaq.to_ayah}"
                if todays_sabaq
                else None
            ),
        }

    return {"error": f"unknown tool '{name}'"}


def get_or_create_conversation(db: Session, student: StudentProfile) -> ChatConversation:
    existing = db.query(ChatConversation).filter(ChatConversation.student_id == student.id).first()
    if existing:
        return existing

    conversation = ChatConversation(student_id=student.id)
    db.add(conversation)
    db.flush()
    return conversation


def get_message_history(db: Session, conversation: ChatConversation, limit: int = 30) -> list[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


async def send_message(db: Session, student: StudentProfile, user_text: str) -> ChatMessage:
    conversation = get_or_create_conversation(db, student)
    history = get_message_history(db, conversation)

    db.add(ChatMessage(conversation_id=conversation.id, role="user", content=user_text))
    db.commit()

    llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    llm_messages += [{"role": m.role, "content": m.content} for m in history]
    llm_messages.append({"role": "user", "content": user_text})

    async def execute(name: str, args: dict) -> dict:
        return await _execute_tool(db, student, name, args)

    try:
        reply_text, tools_called = await run_chat_with_tools(llm_messages, TOOLS, execute)
    except LLMError as exc:
        reply_text, tools_called = str(exc), []

    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        tools_called=",".join(tools_called) if tools_called else None,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message


def to_message_out(message: ChatMessage) -> ChatMessageOut:
    return ChatMessageOut(
        id=message.id,
        role=message.role,
        content=message.content,
        tools_called=message.tools_called.split(",") if message.tools_called else [],
        created_at=message.created_at,
    )
