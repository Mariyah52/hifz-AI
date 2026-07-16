from tests.conftest import make_organization


def _register(client, db_session, role, email, password="correct-horse-battery-staple", class_id=None):
    make_organization(db_session)
    payload = {
        "email": email, "password": password, "name": role.title(),
        "role": role, "organizationSlug": "test-org",
    }
    if class_id:
        payload["classId"] = class_id
    response = client.post("/auth/register", json=payload)
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['accessToken']}"}, tokens


def test_retention_policy_endpoint_is_public_facing_text(client):
    response = client.get("/me/privacy/retention-policy")
    assert response.status_code == 200
    body = response.json()
    assert "practiceTestAudio" in body
    assert "deletedAccounts" in body


def test_export_includes_practice_and_test_history(client, db_session):
    headers, tokens = _register(client, db_session, "student", "exportme@example.com")

    from app.models.lesson import Sabaq
    from app.models.practice import PracticeAttempt
    from app.models.user import StudentProfile, User

    user = db_session.get(User, tokens["userId"])
    student = db_session.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    db_session.add(PracticeAttempt(
        student_id=student.id, surah_number=1, surah_name="Al-Fatiha", from_ayah=1, to_ayah=7,
        duration_seconds=30.0, expected_min_seconds=20.0, expected_max_seconds=40.0, within_expected_range=True,
    ))
    db_session.commit()

    response = client.get("/me/privacy/export", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "exportme@example.com"
    assert len(data["practiceAttempts"]) == 1
    assert data["practiceAttempts"][0]["surahName"] == "Al-Fatiha"


def test_delete_account_requires_confirm_flag(client, db_session):
    headers, _tokens = _register(client, db_session, "student", "noconfirm@example.com")
    response = client.post(
        "/me/privacy/delete-account",
        json={"password": "correct-horse-battery-staple", "confirm": False},
        headers=headers,
    )
    assert response.status_code == 400


def test_delete_account_requires_correct_password(client, db_session):
    headers, _tokens = _register(client, db_session, "student", "wrongpw@example.com")
    response = client.post(
        "/me/privacy/delete-account",
        json={"password": "not-the-real-password", "confirm": True},
        headers=headers,
    )
    assert response.status_code == 401


def test_delete_account_anonymizes_user_and_removes_personal_content(client, db_session):
    headers, tokens = _register(client, db_session, "student", "deleteme@example.com")

    from app.models.note import Note
    from app.models.user import StudentProfile, User

    user = db_session.get(User, tokens["userId"])
    student = db_session.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    db_session.add(Note(student_id=student.id, content="private note"))
    db_session.commit()

    response = client.post(
        "/me/privacy/delete-account",
        json={"password": "correct-horse-battery-staple", "confirm": True},
        headers=headers,
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["rowsHardDeleted"] >= 1  # at least the Note row

    db_session.expire_all()
    reloaded = db_session.get(User, user.id)
    assert reloaded.anonymized is True
    assert reloaded.deleted_at is not None
    assert reloaded.name == "Deleted User"
    assert reloaded.email != "deleteme@example.com"
    assert db_session.query(Note).filter(Note.student_id == student.id).count() == 0


def test_deleted_account_can_no_longer_log_in(client, db_session):
    headers, _tokens = _register(client, db_session, "student", "loginafter@example.com")
    client.post(
        "/me/privacy/delete-account",
        json={"password": "correct-horse-battery-staple", "confirm": True},
        headers=headers,
    )

    login_response = client.post(
        "/auth/login", json={"email": "loginafter@example.com", "password": "correct-horse-battery-staple"}
    )
    assert login_response.status_code == 401


def test_message_content_scrubbed_but_conversation_survives_for_other_party(client, db_session):
    teacher_headers, teacher_tokens = _register(client, db_session, "teacher", "privteacher@example.com")

    from app.models.classroom import ClassRoom
    from app.models.user import TeacherProfile, User

    teacher_user = db_session.get(User, teacher_tokens["userId"])
    teacher_profile = db_session.query(TeacherProfile).filter(TeacherProfile.user_id == teacher_user.id).first()
    class_room = ClassRoom(name="Halaqah 1", teacher_id=teacher_profile.id, organization_id=teacher_user.organization_id)
    db_session.add(class_room)
    db_session.commit()

    student_headers, student_tokens = _register(
        client, db_session, "student", "privstudent@example.com", class_id=class_room.id
    )

    conv_response = client.post(
        "/me/conversations", json={"otherUserId": teacher_tokens["userId"]}, headers=student_headers
    )
    conversation_id = conv_response.json()["id"]
    client.post(
        f"/me/conversations/{conversation_id}/messages",
        data={"content": "a message the student wrote"},
        headers=student_headers,
    )

    client.post(
        "/me/privacy/delete-account",
        json={"password": "correct-horse-battery-staple", "confirm": True},
        headers=student_headers,
    )

    # Teacher's own view of the conversation should still work (row survives)
    # and the student's message content should now be scrubbed.
    messages_response = client.get(f"/me/conversations/{conversation_id}/messages", headers=teacher_headers)
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) == 1
    assert messages[0]["content"] is None
