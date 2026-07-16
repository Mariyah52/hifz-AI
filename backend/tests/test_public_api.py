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


# --- Write endpoints (Phase 31) — previously had zero test coverage -----


def _make_write_key(client, admin_token: str, name: str = "Write integration") -> dict:
    return client.post(
        "/admin/api-keys", json={"name": name, "scopes": "read,write"}, headers=_auth_header(admin_token)
    ).json()


def test_default_scoped_key_cannot_call_write_endpoints(client):
    admin = _register_admin(client, "Scope Org", "scope-admin@example.com", "scope-org").json()
    read_only_key = client.post(
        "/admin/api-keys", json={"name": "Read only"}, headers=_auth_header(admin["accessToken"])
    ).json()

    response = client.post(
        "/v1/students",
        json={"email": "blocked@example.com", "name": "Blocked Student"},
        headers={"X-API-Key": read_only_key["apiKey"]},
    )
    assert response.status_code == 403


def test_write_scoped_key_can_create_a_student(client):
    admin = _register_admin(client, "Create Org", "create-admin@example.com", "create-org").json()
    write_key = _make_write_key(client, admin["accessToken"])

    response = client.post(
        "/v1/students",
        json={"email": "newstudent@example.com", "name": "New Student"},
        headers={"X-API-Key": write_key["apiKey"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newstudent@example.com"
    assert body["temporaryPassword"]  # a real usable password was generated

    # The created student is real and actually logs in with it.
    login = client.post(
        "/auth/login", json={"email": "newstudent@example.com", "password": body["temporaryPassword"]}
    )
    assert login.status_code == 200


def test_creating_a_student_with_a_duplicate_email_is_rejected(client):
    admin = _register_admin(client, "Dup Org", "dup-admin@example.com", "dup-org").json()
    _register_student(client, "dup-org", "dupe@example.com")
    write_key = _make_write_key(client, admin["accessToken"])

    response = client.post(
        "/v1/students", json={"email": "dupe@example.com", "name": "Dupe"}, headers={"X-API-Key": write_key["apiKey"]}
    )
    assert response.status_code == 409


def test_write_scoped_key_can_update_a_student_name(client):
    admin = _register_admin(client, "Update Org", "update-admin@example.com", "update-org").json()
    write_key = _make_write_key(client, admin["accessToken"])
    created = client.post(
        "/v1/students",
        json={"email": "torename@example.com", "name": "Old Name"},
        headers={"X-API-Key": write_key["apiKey"]},
    ).json()

    response = client.patch(
        f"/v1/students/{created['id']}", json={"name": "New Name"}, headers={"X-API-Key": write_key["apiKey"]}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_write_key_cannot_update_a_student_in_another_organization(client):
    admin_a = _register_admin(client, "Wa Org", "wa-admin@example.com", "wa-org").json()
    admin_b = _register_admin(client, "Wb Org", "wb-admin@example.com", "wb-org").json()
    write_key_a = _make_write_key(client, admin_a["accessToken"])
    student_b = client.post(
        "/v1/students",
        json={"email": "wbstudent@example.com", "name": "Org B Student"},
        headers={"X-API-Key": _make_write_key(client, admin_b["accessToken"])["apiKey"]},
    ).json()

    response = client.patch(
        f"/v1/students/{student_b['id']}", json={"name": "Hijacked"}, headers={"X-API-Key": write_key_a["apiKey"]}
    )
    assert response.status_code == 404


def test_write_scoped_key_can_push_attendance(client):
    admin = _register_admin(client, "Att Org", "att-admin@example.com", "att-org").json()
    write_key = _make_write_key(client, admin["accessToken"])
    student = client.post(
        "/v1/students",
        json={"email": "attstudent@example.com", "name": "Attendance Student"},
        headers={"X-API-Key": write_key["apiKey"]},
    ).json()

    response = client.post(
        f"/v1/students/{student['id']}/attendance",
        json={"sessionDate": "2026-07-14", "status": "present", "sourceLabel": "External LMS"},
        headers={"X-API-Key": write_key["apiKey"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "present"
    assert body["sourceLabel"] == "External LMS"


def test_write_scoped_key_can_push_a_grade(client):
    admin = _register_admin(client, "Grade Org", "grade-admin@example.com", "grade-org").json()
    write_key = _make_write_key(client, admin["accessToken"])
    student = client.post(
        "/v1/students",
        json={"email": "gradestudent@example.com", "name": "Grade Student"},
        headers={"X-API-Key": write_key["apiKey"]},
    ).json()

    response = client.post(
        f"/v1/students/{student['id']}/grades",
        json={"label": "Midterm Tajweed Exam", "score": 87, "maxScore": 100, "recordedDate": "2026-07-14"},
        headers={"X-API-Key": write_key["apiKey"]},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["score"] == 87
    assert body["label"] == "Midterm Tajweed Exam"


def test_attendance_endpoint_rejects_a_student_from_another_organization(client):
    admin_a = _register_admin(client, "Attiso A", "attiso-admina@example.com", "attiso-org-a").json()
    admin_b = _register_admin(client, "Attiso B", "attiso-adminb@example.com", "attiso-org-b").json()
    write_key_a = _make_write_key(client, admin_a["accessToken"])
    student_b = client.post(
        "/v1/students",
        json={"email": "attisob@example.com", "name": "Org B Student"},
        headers={"X-API-Key": _make_write_key(client, admin_b["accessToken"])["apiKey"]},
    ).json()

    response = client.post(
        f"/v1/students/{student_b['id']}/attendance",
        json={"sessionDate": "2026-07-14", "status": "present"},
        headers={"X-API-Key": write_key_a["apiKey"]},
    )
    assert response.status_code == 404
