from tests.conftest import make_organization


def _register(client, db_session, role, email, class_id=None):
    make_organization(db_session)
    payload = {
        "email": email, "password": "correct-horse-battery-staple", "name": role.title(),
        "role": role, "organizationSlug": "test-org",
    }
    if class_id:
        payload["classId"] = class_id
    response = client.post("/auth/register", json=payload)
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['accessToken']}"}, tokens


def _make_class(db_session, teacher_tokens):
    from app.models.classroom import ClassRoom
    from app.models.user import TeacherProfile, User

    teacher_user = db_session.get(User, teacher_tokens["userId"])
    teacher_profile = db_session.query(TeacherProfile).filter(TeacherProfile.user_id == teacher_user.id).first()
    class_room = ClassRoom(name="Halaqah 1", teacher_id=teacher_profile.id, organization_id=teacher_user.organization_id)
    db_session.add(class_room)
    db_session.commit()
    return class_room.id


def test_teacher_can_message_their_own_student(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "msgteacher@example.com")
    class_id = _make_class(db_session, teacher_tokens)
    _student_headers, student_tokens = _register(client, db_session, "student", "msgstudent@example.com", class_id=class_id)

    response = client.post(
        "/me/conversations", json={"otherUserId": student_tokens["userId"]}, headers=teacher_headers
    )
    assert response.status_code == 201


def test_teacher_cannot_message_student_not_in_their_class(client, db_session):
    teacher_headers, _ = _register(client, db_session, "teacher", "outsider_teacher@example.com")
    # A student with no class at all — definitely not this teacher's.
    _student_headers, student_tokens = _register(client, db_session, "student", "unaffiliated_student@example.com")

    response = client.post(
        "/me/conversations", json={"otherUserId": student_tokens["userId"]}, headers=teacher_headers
    )
    assert response.status_code == 403


def test_two_students_cannot_message_each_other(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "msgteacher2@example.com")
    class_id = _make_class(db_session, teacher_tokens)
    student_a_headers, _ = _register(client, db_session, "student", "student_a@example.com", class_id=class_id)
    _student_b_headers, student_b_tokens = _register(client, db_session, "student", "student_b@example.com", class_id=class_id)

    response = client.post(
        "/me/conversations", json={"otherUserId": student_b_tokens["userId"]}, headers=student_a_headers
    )
    assert response.status_code == 403


def test_conversation_is_reused_regardless_of_who_initiates(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "msgteacher3@example.com")
    class_id = _make_class(db_session, teacher_tokens)
    student_headers, student_tokens = _register(client, db_session, "student", "msgstudent3@example.com", class_id=class_id)

    from_teacher = client.post(
        "/me/conversations", json={"otherUserId": student_tokens["userId"]}, headers=teacher_headers
    ).json()
    from_student = client.post(
        "/me/conversations", json={"otherUserId": teacher_tokens["userId"]}, headers=student_headers
    ).json()

    assert from_teacher["id"] == from_student["id"]


def test_send_and_read_message(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "msgteacher4@example.com")
    class_id = _make_class(db_session, teacher_tokens)
    student_headers, student_tokens = _register(client, db_session, "student", "msgstudent4@example.com", class_id=class_id)

    conversation = client.post(
        "/me/conversations", json={"otherUserId": student_tokens["userId"]}, headers=teacher_headers
    ).json()

    sent = client.post(
        f"/me/conversations/{conversation['id']}/messages",
        data={"content": "Great job today!"},
        headers=teacher_headers,
    )
    assert sent.status_code == 201
    assert sent.json()["content"] == "Great job today!"

    messages = client.get(f"/me/conversations/{conversation['id']}/messages", headers=student_headers)
    assert messages.status_code == 200
    assert len(messages.json()) == 1
