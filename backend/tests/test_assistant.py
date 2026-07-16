from datetime import datetime
from app.models.chat import ChatMessage
from app.services.assistant_service import get_message_history, get_or_create_conversation, to_message_out
from tests.conftest import make_student


def test_get_or_create_conversation_is_idempotent(db_session):
    student = make_student(db_session, email="chat1@example.com")
    first = get_or_create_conversation(db_session, student)
    db_session.commit()
    second = get_or_create_conversation(db_session, student)
    assert first.id == second.id


def test_get_or_create_conversation_is_per_student(db_session):
    student_a = make_student(db_session, email="chat-a@example.com")
    student_b = make_student(db_session, email="chat-b@example.com")
    conv_a = get_or_create_conversation(db_session, student_a)
    conv_b = get_or_create_conversation(db_session, student_b)
    assert conv_a.id != conv_b.id


def test_message_history_ordered_and_scoped_to_conversation(db_session):
    student = make_student(db_session, email="chat2@example.com")
    conversation = get_or_create_conversation(db_session, student)
    db_session.commit()

    db_session.add(ChatMessage(conversation_id=conversation.id, role="user", content="first"))
    db_session.add(ChatMessage(conversation_id=conversation.id, role="assistant", content="second"))
    db_session.flush()

    history = get_message_history(db_session, conversation)
    assert [m.content for m in history] == ["first", "second"]


def test_to_message_out_splits_tools_called():
    message = ChatMessage(
        id="cmsg_1", conversation_id="conv_1", role="assistant", content="hi",
        tools_called="get_due_reviews,get_progress_summary",
        created_at=datetime.utcnow(),
    )
    out = to_message_out(message)
    assert out.tools_called == ["get_due_reviews", "get_progress_summary"]


def test_to_message_out_empty_tools_called_is_empty_list():
    message = ChatMessage(id="cmsg_2", conversation_id="conv_1", role="user", content="hi", tools_called=None, created_at=datetime.utcnow())
    out = to_message_out(message)
    assert out.tools_called == []
