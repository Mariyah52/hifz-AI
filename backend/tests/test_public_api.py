def _register_admin(client, org_name, email, org_slug):
    return client.post(
        "/auth/register",
        json={
            "email": email, "password": "correct-horse-battery-staple", "name": "Admin",
            "role": "admin", "organizationName": org_name, "organizationSlug": org_slug,
        },
    )


def _register_student(client, org_slug, email):
    return client.post(
        "/auth/register",
        json={
            "email": email, "password": "correct-horse-battery-staple", "name": "Student",
            "role": "student", "organizationSlug": org_slug,
        },
    )


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_creating_an_api_key_returns_the_raw_key_exactly_once(client):
    admin = _register_admin(client, "Api Org", "api-admin@example.com", "api-org").json()
    response = client.post(
        "/admin/api-keys", json={"name": "Main ERP integration"}, headers=_auth_header(admin["accessToken"])
    )
    assert response.status_code == 201
    body = response.json()
    assert body["apiKey"].startswith("hfz_live_")
    assert body["keyPrefix"] in body["apiKey"]

    listed = client.get("/admin/api-keys", headers=_auth_header(admin["accessToken"])).json()
    assert len(listed) == 1
    assert "apiKey" not in listed[0]


def test_valid_api_key_can_read_students_in_its_own_organization(client):
    admin = _register_admin(client, "Read Org", "read-admin@example.com", "read-org").json()
    _register_student(client, "read-org", "read-student@example.com")
    created = client.post(
        "/admin/api-keys", json={"name": "Integration"}, headers=_auth_header(admin["accessToken"])
    ).json()

    response = client.get("/v1/students", headers={"X-API-Key": created["apiKey"]})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_missing_api_key_is_rejected(client):
    response = client.get("/v1/students")
    assert response.status_code == 401


def test_invalid_api_key_is_rejected(client):
    response = client.get("/v1/students", headers={"X-API-Key": "hfz_live_totally-made-up"})
    assert response.status_code == 401


def test_revoked_api_key_is_rejected(client):
    admin = _register_admin(client, "Revoke Org", "revoke-admin@example.com", "revoke-org").json()
    created = client.post(
        "/admin/api-keys", json={"name": "Temp key"}, headers=_auth_header(admin["accessToken"])
    ).json()

    client.delete(f"/admin/api-keys/{created['id']}", headers=_auth_header(admin["accessToken"]))

    response = client.get("/v1/students", headers={"X-API-Key": created["apiKey"]})
    assert response.status_code == 401


def test_api_key_cannot_read_another_organizations_students(client):
    admin_a = _register_admin(client, "Isolated A", "iso-admina@example.com", "iso-org-a").json()
    _register_admin(client, "Isolated B", "iso-adminb@example.com", "iso-org-b")
    _register_student(client, "iso-org-a", "iso-student-a@example.com")
    _register_student(client, "iso-org-b", "iso-student-b1@example.com")
    _register_student(client, "iso-org-b", "iso-student-b2@example.com")

    key_a = client.post(
        "/admin/api-keys", json={"name": "Key A"}, headers=_auth_header(admin_a["accessToken"])
    ).json()

    response = client.get("/v1/students", headers={"X-API-Key": key_a["apiKey"]})
    assert response.status_code == 200
    assert len(response.json()) == 1  # only Org A's one student, never Org B's two


def test_api_key_progress_endpoint_rejects_a_student_from_another_organization(client, db_session):
    admin_a = _register_admin(client, "Prog A", "prog-admina@example.com", "prog-org-a").json()
    _register_admin(client, "Prog B", "prog-adminb@example.com", "prog-org-b")
    _register_student(client, "prog-org-b", "prog-student-b@example.com")

    key_a = client.post(
        "/admin/api-keys", json={"name": "Key A"}, headers=_auth_header(admin_a["accessToken"])
    ).json()

    from app.models.user import StudentProfile, User

    other_student = (
        db_session.query(StudentProfile)
        .join(User, User.id == StudentProfile.user_id)
        .filter(User.email == "prog-student-b@example.com")
        .first()
    )

    response = client.get(f"/v1/students/{other_student.id}/progress", headers={"X-API-Key": key_a["apiKey"]})
    assert response.status_code == 404


def test_classes_endpoint_is_scoped_to_the_keys_organization(client):
    admin_a = _register_admin(client, "Class A", "class-admina@example.com", "class-org-a").json()
    _register_admin(client, "Class B", "class-adminb@example.com", "class-org-b")

    key_a = client.post(
        "/admin/api-keys", json={"name": "Key A"}, headers=_auth_header(admin_a["accessToken"])
    ).json()
    client.post(
        "/admin/classes", json={"name": "Org A Class"}, headers=_auth_header(admin_a["accessToken"])
    )

    response = client.get("/v1/classes", headers={"X-API-Key": key_a["apiKey"]})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Org A Class"
