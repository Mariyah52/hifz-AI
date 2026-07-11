def _register_and_login(client, db_session, email="notes@example.com"):
    from tests.conftest import make_organization

    make_organization(db_session)
    response = client.post(
        "/auth/register",
        json={
            "email": email, "password": "correct-horse-battery-staple", "name": "Student",
            "role": "student", "organizationSlug": "test-org",
        },
    )
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['accessToken']}"}


def test_create_note_and_list(client, db_session):
    headers = _register_and_login(client, db_session)

    response = client.post("/me/notes", json={"content": "Remember the pause at ayah 5"}, headers=headers)
    assert response.status_code == 201
    assert response.json()["content"] == "Remember the pause at ayah 5"

    listed = client.get("/me/notes", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_create_note_idempotent_on_retry(client, db_session):
    headers = _register_and_login(client, db_session, email="notes2@example.com")
    payload = {"content": "duplicate-safe note", "clientMutationId": "fixed-mutation-id-1"}

    first = client.post("/me/notes", json=payload, headers=headers)
    second = client.post("/me/notes", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    listed = client.get("/me/notes", headers=headers).json()
    assert len(listed) == 1


def test_delete_note(client, db_session):
    headers = _register_and_login(client, db_session, email="notes3@example.com")
    created = client.post("/me/notes", json={"content": "temp"}, headers=headers).json()

    delete_response = client.delete(f"/me/notes/{created['id']}", headers=headers)
    assert delete_response.status_code == 204

    listed = client.get("/me/notes", headers=headers).json()
    assert listed == []


def test_test_session_idempotent_on_retry(client, db_session):
    headers = _register_and_login(client, db_session, email="notes4@example.com")
    payload = {
        "surahNumber": 1, "surahName": "Al-Fatihah", "fromAyah": 1, "toAyah": 2,
        "results": [{"ayahNumber": 1, "selfMark": "correct", "durationSeconds": 5}],
        "scorePercent": 100, "clientMutationId": "fixed-mutation-id-2",
    }

    first = client.post("/me/test-sessions", json=payload, headers=headers)
    second = client.post("/me/test-sessions", json=payload, headers=headers)

    assert first.status_code == 201
    assert first.json()["id"] == second.json()["id"]

    listed = client.get("/me/test-sessions", headers=headers).json()
    assert len(listed) == 1
