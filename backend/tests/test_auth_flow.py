from tests.conftest import make_organization


def _register(client, db_session, email="student@example.com", password="correct-horse-battery-staple"):
    make_organization(db_session)
    return client.post(
        "/auth/register",
        json={
            "email": email, "password": password, "name": "Test Student", "role": "student",
            "organizationSlug": "test-org",
        },
    )


def test_register_returns_access_and_refresh_tokens(client, db_session):
    response = _register(client, db_session)
    assert response.status_code == 201
    body = response.json()
    assert body["accessToken"]
    assert body["refreshToken"]
    assert body["role"] == "student"


def test_register_rejects_duplicate_email(client, db_session):
    _register(client, db_session, email="dupe@example.com")
    response = _register(client, db_session, email="dupe@example.com")
    assert response.status_code == 409


def test_login_succeeds_with_correct_password(client, db_session):
    _register(client, db_session, email="login@example.com", password="correct-horse-battery-staple")
    response = client.post(
        "/auth/login", json={"email": "login@example.com", "password": "correct-horse-battery-staple"}
    )
    assert response.status_code == 200
    assert response.json()["accessToken"]


def test_login_fails_with_wrong_password(client, db_session):
    _register(client, db_session, email="wrongpw@example.com", password="correct-horse-battery-staple")
    response = client.post("/auth/login", json={"email": "wrongpw@example.com", "password": "nope"})
    assert response.status_code == 401


def test_account_locks_after_max_failed_attempts(client, db_session):
    _register(client, db_session, email="lockout@example.com", password="correct-horse-battery-staple")

    for _ in range(5):
        response = client.post("/auth/login", json={"email": "lockout@example.com", "password": "wrong"})
        assert response.status_code == 401

    response = client.post(
        "/auth/login", json={"email": "lockout@example.com", "password": "correct-horse-battery-staple"}
    )
    assert response.status_code == 423


def test_successful_login_resets_failed_attempt_counter(client, db_session):
    _register(client, db_session, email="reset@example.com", password="correct-horse-battery-staple")

    for _ in range(3):
        client.post("/auth/login", json={"email": "reset@example.com", "password": "wrong"})

    response = client.post(
        "/auth/login", json={"email": "reset@example.com", "password": "correct-horse-battery-staple"}
    )
    assert response.status_code == 200

    for _ in range(2):
        client.post("/auth/login", json={"email": "reset@example.com", "password": "wrong"})
    response = client.post(
        "/auth/login", json={"email": "reset@example.com", "password": "correct-horse-battery-staple"}
    )
    assert response.status_code == 200


def test_refresh_token_issues_new_tokens_and_rotates(client, db_session):
    tokens = _register(client, db_session, email="refresh@example.com").json()

    response = client.post("/auth/refresh", json={"refreshToken": tokens["refreshToken"]})
    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["accessToken"] != tokens["accessToken"]
    assert new_tokens["refreshToken"] != tokens["refreshToken"]

    reused = client.post("/auth/refresh", json={"refreshToken": tokens["refreshToken"]})
    assert reused.status_code == 401


def test_logout_revokes_the_refresh_token(client, db_session):
    tokens = _register(client, db_session, email="logout@example.com").json()

    logout_response = client.post("/auth/logout", json={"refreshToken": tokens["refreshToken"]})
    assert logout_response.status_code == 204

    refresh_response = client.post("/auth/refresh", json={"refreshToken": tokens["refreshToken"]})
    assert refresh_response.status_code == 401


def test_password_reset_request_never_reveals_whether_email_exists(client, db_session):
    exists_response = client.post("/auth/request-password-reset", json={"email": "nope@example.com"})
    assert exists_response.status_code == 204

    _register(client, db_session, email="reset-flow@example.com")
    not_exists_response = client.post("/auth/request-password-reset", json={"email": "reset-flow@example.com"})
    assert not_exists_response.status_code == 204


def test_reset_password_rejects_invalid_token(client, db_session):
    response = client.post("/auth/reset-password", json={"token": "not-a-real-token", "newPassword": "new-pass"})
    assert response.status_code == 400
