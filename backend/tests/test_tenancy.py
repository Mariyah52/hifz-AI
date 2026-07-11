def _register_admin(client, org_name, email, org_slug=None):
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


def test_admin_registration_creates_a_new_organization(client):
    response = _register_admin(client, "Green Valley Academy", "admin1@example.com", org_slug="green-valley")
    assert response.status_code == 201

    public = client.get("/organizations/green-valley/public")
    assert public.status_code == 200
    assert public.json()["name"] == "Green Valley Academy"


def test_admin_registration_requires_organization_name(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "noorg@example.com", "password": "correct-horse-battery-staple",
            "name": "Admin", "role": "admin",
        },
    )
    assert response.status_code == 400


def test_student_registration_requires_a_valid_organization_slug(client):
    response = _register_student(client, "does-not-exist", "student1@example.com")
    assert response.status_code == 404


def test_student_can_join_an_existing_organization(client):
    _register_admin(client, "Blue Ridge School", "admin2@example.com", org_slug="blue-ridge")
    response = _register_student(client, "blue-ridge", "student2@example.com")
    assert response.status_code == 201
    assert response.json()["organizationSlug"] == "blue-ridge"


def test_registration_rejected_once_student_plan_limit_reached(client, db_session):
    _register_admin(client, "Small School", "admin3@example.com", org_slug="small-school")

    from app.models.organization import Organization

    org = db_session.query(Organization).filter(Organization.slug == "small-school").first()
    org.max_students = 1
    db_session.commit()

    first = _register_student(client, "small-school", "s1@example.com")
    assert first.status_code == 201

    second = _register_student(client, "small-school", "s2@example.com")
    assert second.status_code == 402


def test_admin_only_sees_students_from_their_own_organization(client):
    admin_a = _register_admin(client, "Org A", "admina@example.com", org_slug="org-a").json()
    admin_b = _register_admin(client, "Org B", "adminb@example.com", org_slug="org-b").json()

    _register_student(client, "org-a", "student-a@example.com")
    _register_student(client, "org-b", "student-b@example.com")
    _register_student(client, "org-b", "student-b2@example.com")

    response_a = client.get("/admin/students", headers=_auth_header(admin_a["accessToken"]))
    assert response_a.status_code == 200
    assert len(response_a.json()) == 1

    response_b = client.get("/admin/students", headers=_auth_header(admin_b["accessToken"]))
    assert response_b.status_code == 200
    assert len(response_b.json()) == 2


def test_admin_analytics_are_scoped_to_own_organization(client):
    admin_a = _register_admin(client, "Org C", "adminc@example.com", org_slug="org-c").json()
    admin_b = _register_admin(client, "Org D", "admind@example.com", org_slug="org-d").json()

    _register_student(client, "org-c", "c-student@example.com")
    for i in range(3):
        _register_student(client, "org-d", f"d-student-{i}@example.com")

    analytics_a = client.get("/admin/analytics", headers=_auth_header(admin_a["accessToken"])).json()
    analytics_b = client.get("/admin/analytics", headers=_auth_header(admin_b["accessToken"])).json()

    assert analytics_a["totalStudents"] == 1
    assert analytics_b["totalStudents"] == 3


def test_admin_cannot_assign_class_to_a_bogus_or_cross_org_teacher_id(client):
    admin_a = _register_admin(client, "Org E", "admine@example.com", org_slug="org-e").json()

    response = client.post(
        "/admin/classes",
        json={"name": "Cross-org class", "teacherId": "definitely-not-a-real-teacher-id"},
        headers=_auth_header(admin_a["accessToken"]),
    )
    assert response.status_code == 404


def test_organization_public_endpoint_never_exposes_plan_or_counts(client):
    _register_admin(client, "Private Numbers Academy", "adminp@example.com", org_slug="private-numbers")
    response = client.get("/organizations/private-numbers/public")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"name", "slug", "primaryColor", "logoUrl"}


def test_admin_organization_view_shows_real_usage_counts(client):
    admin = _register_admin(client, "Usage Academy", "adminu@example.com", org_slug="usage-academy").json()
    _register_student(client, "usage-academy", "usage-student@example.com")

    response = client.get("/admin/organization", headers=_auth_header(admin["accessToken"]))
    assert response.status_code == 200
    body = response.json()
    assert body["currentStudentCount"] == 1
    assert body["plan"] == "free"
    assert body["maxStudents"] == 30
