import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

from app.services.webhooks import _sign_payload


def _register_admin(client, org_name, email, org_slug):
    return client.post(
        "/auth/register",
        json={
            "email": email, "password": "correct-horse-battery-staple", "name": "Admin",
            "role": "admin", "organizationName": org_name, "organizationSlug": org_slug,
        },
    )


def _register_teacher(client, org_slug, email):
    return client.post(
        "/auth/register",
        json={
            "email": email, "password": "correct-horse-battery-staple", "name": "Teacher",
            "role": "teacher", "organizationSlug": org_slug,
        },
    )


def _register_student(client, org_slug, email, class_id=None):
    payload = {
        "email": email, "password": "correct-horse-battery-staple", "name": "Student",
        "role": "student", "organizationSlug": org_slug,
    }
    if class_id:
        payload["classId"] = class_id
    return client.post("/auth/register", json=payload)


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_sign_payload_is_deterministic_hmac_sha256():
    secret = "whsec_test"
    body = b'{"eventType":"sabaq.completed"}'
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    assert _sign_payload(secret, body) == expected


def test_create_webhook_returns_secret_exactly_once(client):
    admin = _register_admin(client, "WH Org", "wh-admin@example.com", "wh-org").json()
    response = client.post(
        "/admin/webhooks",
        json={"url": "https://example.com/hooks/hifzai", "eventTypes": ["sabaq.completed"]},
        headers=_auth_header(admin["accessToken"]),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["secret"].startswith("whsec_")

    listed = client.get("/admin/webhooks", headers=_auth_header(admin["accessToken"])).json()
    assert len(listed) == 1
    assert "secret" not in listed[0]


def test_create_webhook_rejects_non_https_url(client):
    admin = _register_admin(client, "HTTP Org", "http-admin@example.com", "http-org").json()
    response = client.post(
        "/admin/webhooks",
        json={"url": "http://example.com/hooks", "eventTypes": ["sabaq.completed"]},
        headers=_auth_header(admin["accessToken"]),
    )
    assert response.status_code == 400


def test_create_webhook_rejects_unknown_event_type(client):
    admin = _register_admin(client, "Bad Event Org", "badevent-admin@example.com", "badevent-org").json()
    response = client.post(
        "/admin/webhooks",
        json={"url": "https://example.com/hooks", "eventTypes": ["not_a_real_event"]},
        headers=_auth_header(admin["accessToken"]),
    )
    assert response.status_code == 400


def test_dispatch_event_calls_subscribed_webhook_with_valid_signature(db_session):
    from app.models.organization import Organization
    from app.models.user import new_id
    from app.models.webhook import Webhook, WebhookDeliveryLog
    from app.services.webhooks import dispatch_event

    org = Organization(name="Dispatch Org", slug="dispatch-org", plan="free", max_students=30, max_teachers=5)
    db_session.add(org)
    db_session.flush()

    webhook = Webhook(
        organization_id=org.id, url="https://example.com/hook", secret="whsec_abc123",
        event_types="sabaq.completed,certificate.issued", created_by_user_id=new_id("u"),
    )
    db_session.add(webhook)
    db_session.commit()

    mock_response = MagicMock(status_code=200, text="ok")
    with patch("app.services.webhooks.httpx.post", return_value=mock_response) as mock_post:
        dispatch_event(db_session, org.id, "sabaq.completed", {"sabaqId": "sbq_1"})

    assert mock_post.call_count == 1
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["X-HifzAI-Event"] == "sabaq.completed"

    sent_body = call_kwargs["content"]
    expected_signature = hmac.new(b"whsec_abc123", sent_body, hashlib.sha256).hexdigest()
    assert call_kwargs["headers"]["X-HifzAI-Signature"] == expected_signature
    assert json.loads(sent_body)["data"]["sabaqId"] == "sbq_1"

    logs = db_session.query(WebhookDeliveryLog).filter(WebhookDeliveryLog.webhook_id == webhook.id).all()
    assert len(logs) == 1
    assert logs[0].success is True
    assert logs[0].status_code == 200


def test_dispatch_event_skips_webhooks_not_subscribed_to_that_event(db_session):
    from app.models.organization import Organization
    from app.models.user import new_id
    from app.models.webhook import Webhook
    from app.services.webhooks import dispatch_event

    org = Organization(name="Skip Org", slug="skip-org", plan="free", max_students=30, max_teachers=5)
    db_session.add(org)
    db_session.flush()

    webhook = Webhook(
        organization_id=org.id, url="https://example.com/hook", secret="whsec_x",
        event_types="certificate.issued", created_by_user_id=new_id("u"),
    )
    db_session.add(webhook)
    db_session.commit()

    with patch("app.services.webhooks.httpx.post") as mock_post:
        dispatch_event(db_session, org.id, "sabaq.completed", {"sabaqId": "sbq_1"})

    mock_post.assert_not_called()


def test_dispatch_event_skips_inactive_webhooks(db_session):
    from app.models.organization import Organization
    from app.models.user import new_id
    from app.models.webhook import Webhook
    from app.services.webhooks import dispatch_event

    org = Organization(name="Inactive Org", slug="inactive-org", plan="free", max_students=30, max_teachers=5)
    db_session.add(org)
    db_session.flush()

    webhook = Webhook(
        organization_id=org.id, url="https://example.com/hook", secret="whsec_x",
        event_types="sabaq.completed", is_active=False, created_by_user_id=new_id("u"),
    )
    db_session.add(webhook)
    db_session.commit()

    with patch("app.services.webhooks.httpx.post") as mock_post:
        dispatch_event(db_session, org.id, "sabaq.completed", {"sabaqId": "sbq_1"})

    mock_post.assert_not_called()


def test_dispatch_event_records_failure_on_connection_error(db_session):
    import httpx

    from app.models.organization import Organization
    from app.models.user import new_id
    from app.models.webhook import Webhook, WebhookDeliveryLog
    from app.services.webhooks import dispatch_event

    org = Organization(name="Fail Org", slug="fail-org", plan="free", max_students=30, max_teachers=5)
    db_session.add(org)
    db_session.flush()

    webhook = Webhook(
        organization_id=org.id, url="https://unreachable.example.com/hook", secret="whsec_x",
        event_types="sabaq.completed", created_by_user_id=new_id("u"),
    )
    db_session.add(webhook)
    db_session.commit()

    with patch("app.services.webhooks.httpx.post", side_effect=httpx.ConnectError("connection refused")):
        dispatch_event(db_session, org.id, "sabaq.completed", {"sabaqId": "sbq_1"})

    logs = db_session.query(WebhookDeliveryLog).filter(WebhookDeliveryLog.webhook_id == webhook.id).all()
    assert len(logs) == 1
    assert logs[0].success is False
    assert logs[0].status_code is None


def test_completing_a_sabaq_dispatches_the_real_webhook_end_to_end(client, db_session):
    """
    Full path: teacher assigns a Sabaq, admin registers a webhook for
    'sabaq.completed', student marks it completed — verifies the actual
    router-level BackgroundTasks wiring, not just the service in isolation.
    """
    admin = _register_admin(client, "E2E Org", "e2e-admin@example.com", "e2e-org").json()
    client.post(
        "/admin/webhooks",
        json={"url": "https://example.com/hook", "eventTypes": ["sabaq.completed"]},
        headers=_auth_header(admin["accessToken"]),
    )

    teacher = _register_teacher(client, "e2e-org", "e2e-teacher@example.com").json()
    teacher_profile_id = _teacher_profile_id(db_session, "e2e-teacher@example.com")
    class_response = client.post(
        "/admin/classes",
        json={"name": "E2E Class", "teacherId": teacher_profile_id},
        headers=_auth_header(admin["accessToken"]),
    ).json()

    student = _register_student(client, "e2e-org", "e2e-student@example.com", class_id=class_response["id"]).json()

    sabaq = client.post(
        f"/teacher/students/{_student_profile_id(db_session, 'e2e-student@example.com')}/sabaq",
        json={"surahNumber": 67, "surahName": "Al-Mulk", "fromAyah": 1, "toAyah": 5},
        headers=_auth_header(teacher["accessToken"]),
    ).json()

    mock_response = MagicMock(status_code=200, text="ok")
    with patch("app.services.webhooks.httpx.post", return_value=mock_response) as mock_post:
        response = client.post(
            f"/me/sabaq/{sabaq['id']}/status?status_value=completed",
            headers=_auth_header(student["accessToken"]),
        )
    assert response.status_code == 200
    assert mock_post.call_count == 1
    sent_body = json.loads(mock_post.call_args.kwargs["content"])
    assert sent_body["eventType"] == "sabaq.completed"
    assert sent_body["data"]["sabaqId"] == sabaq["id"]


def _student_profile_id(db_session, email: str) -> str:
    from app.models.user import StudentProfile, User

    return (
        db_session.query(StudentProfile)
        .join(User, User.id == StudentProfile.user_id)
        .filter(User.email == email)
        .first()
        .id
    )


def _teacher_profile_id(db_session, email: str) -> str:
    from app.models.user import TeacherProfile, User

    return (
        db_session.query(TeacherProfile)
        .join(User, User.id == TeacherProfile.user_id)
        .filter(User.email == email)
        .first()
        .id
    )
