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


def test_start_and_end_live_session(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "teacher@example.com")
    class_id = _make_class(db_session, teacher_tokens)

    start_response = client.post("/teacher/live-sessions", json={"classId": class_id}, headers=teacher_headers)
    assert start_response.status_code == 201
    session = start_response.json()
    assert session["status"] == "live"
    assert session["className"] == "Halaqah 1"

    active = client.get("/teacher/live-sessions/active", headers=teacher_headers)
    assert active.status_code == 200
    assert active.json()["id"] == session["id"]

    end_response = client.post(f"/teacher/live-sessions/{session['id']}/end", headers=teacher_headers)
    assert end_response.status_code == 200
    report = end_response.json()
    assert report["session"]["status"] == "ended"
    assert report["participants"] == []
    assert report["mistakes"] == []


def test_cannot_start_two_sessions_for_same_class(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "teacher2@example.com")
    class_id = _make_class(db_session, teacher_tokens)

    first = client.post("/teacher/live-sessions", json={"classId": class_id}, headers=teacher_headers)
    assert first.status_code == 201

    second = client.post("/teacher/live-sessions", json={"classId": class_id}, headers=teacher_headers)
    assert second.status_code == 409


def test_student_sees_active_session_for_their_class(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "teacher3@example.com")
    class_id = _make_class(db_session, teacher_tokens)

    student_headers, _ = _register(client, db_session, "student", "student1@example.com", class_id=class_id)

    none_yet = client.get("/me/live-sessions/active", headers=student_headers)
    assert none_yet.status_code == 200
    assert none_yet.json() is None

    client.post("/teacher/live-sessions", json={"classId": class_id}, headers=teacher_headers)

    now_active = client.get("/me/live-sessions/active", headers=student_headers)
    assert now_active.status_code == 200
    assert now_active.json() is not None


def test_teacher_cannot_start_session_for_class_they_dont_teach(client, db_session):
    teacher_a_headers, teacher_a_tokens = _register(client, db_session, "teacher", "teachera@example.com")
    class_id = _make_class(db_session, teacher_a_tokens)

    teacher_b_headers, _ = _register(client, db_session, "teacher", "teacherb@example.com")

    response = client.post("/teacher/live-sessions", json={"classId": class_id}, headers=teacher_b_headers)
    assert response.status_code == 409
