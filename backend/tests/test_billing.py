from unittest.mock import MagicMock, patch

import pytest

from app.config import settings


def _register_admin(client, org_name, email, org_slug):
    return client.post(
        "/auth/register",
        json={
            "email": email, "password": "correct-horse-battery-staple", "name": "Admin",
            "role": "admin", "organizationName": org_name, "organizationSlug": org_slug,
        },
    )


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def configured_billing():
    """Billing settings only exist for the duration of a test that needs them — never a real key, just enough to exercise the code paths."""
    original = (settings.stripe_secret_key, settings.stripe_webhook_secret, settings.stripe_pro_price_id)
    settings.stripe_secret_key = "sk_test_fake"
    settings.stripe_webhook_secret = "whsec_test_fake"
    settings.stripe_pro_price_id = "price_fake123"
    yield
    settings.stripe_secret_key, settings.stripe_webhook_secret, settings.stripe_pro_price_id = original


def test_checkout_session_returns_503_when_billing_not_configured(client):
    admin = _register_admin(client, "Unconfigured Org", "unconfigured-admin@example.com", "unconfigured-org").json()
    response = client.post(
        "/admin/billing/checkout-session",
        json={"successUrl": "https://example.com/success", "cancelUrl": "https://example.com/cancel"},
        headers=_auth_header(admin["accessToken"]),
    )
    assert response.status_code == 503


def test_billing_status_reflects_free_plan_by_default(client):
    admin = _register_admin(client, "Status Org", "status-admin@example.com", "status-org").json()
    response = client.get("/admin/billing/status", headers=_auth_header(admin["accessToken"]))
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "free"
    assert body["hasBillingHistory"] is False


def test_checkout_session_creates_stripe_customer_and_session(client, db_session, configured_billing):
    admin = _register_admin(client, "Checkout Org", "checkout-admin@example.com", "checkout-org").json()

    mock_customer = MagicMock(id="cus_fake123")
    mock_session = MagicMock(url="https://checkout.stripe.com/fake-session")

    with patch("app.services.billing.stripe.Customer.create", return_value=mock_customer) as mock_create_customer, \
         patch("app.services.billing.stripe.checkout.Session.create", return_value=mock_session) as mock_create_session:
        response = client.post(
            "/admin/billing/checkout-session",
            json={"successUrl": "https://example.com/success", "cancelUrl": "https://example.com/cancel"},
            headers=_auth_header(admin["accessToken"]),
        )

    assert response.status_code == 200
    assert response.json()["checkoutUrl"] == "https://checkout.stripe.com/fake-session"
    mock_create_customer.assert_called_once()
    mock_create_session.assert_called_once()

    from app.models.organization import Organization

    organization = db_session.query(Organization).filter(Organization.slug == "checkout-org").first()
    assert organization.stripe_customer_id == "cus_fake123"


def test_checkout_session_reuses_existing_stripe_customer(client, db_session, configured_billing):
    admin = _register_admin(client, "Reuse Org", "reuse-admin@example.com", "reuse-org").json()

    from app.models.organization import Organization

    organization = db_session.query(Organization).filter(Organization.slug == "reuse-org").first()
    organization.stripe_customer_id = "cus_already_exists"
    db_session.commit()

    mock_session = MagicMock(url="https://checkout.stripe.com/fake-session-2")
    with patch("app.services.billing.stripe.Customer.create") as mock_create_customer, \
         patch("app.services.billing.stripe.checkout.Session.create", return_value=mock_session) as mock_create_session:
        client.post(
            "/admin/billing/checkout-session",
            json={"successUrl": "https://example.com/success", "cancelUrl": "https://example.com/cancel"},
            headers=_auth_header(admin["accessToken"]),
        )

    mock_create_customer.assert_not_called()
    _, call_kwargs = mock_create_session.call_args
    assert call_kwargs["customer"] == "cus_already_exists"


def test_portal_session_requires_existing_billing_history(client, configured_billing):
    admin = _register_admin(client, "Portal Org", "portal-admin@example.com", "portal-org").json()
    response = client.post(
        "/admin/billing/portal-session",
        json={"returnUrl": "https://example.com/account"},
        headers=_auth_header(admin["accessToken"]),
    )
    assert response.status_code == 400


def test_webhook_rejects_invalid_signature(client, configured_billing):
    import stripe

    with patch(
        "app.services.billing.stripe.Webhook.construct_event",
        side_effect=stripe.error.SignatureVerificationError("bad signature", "sig_header"),
    ):
        response = client.post(
            "/webhooks/stripe", content=b'{"type": "checkout.session.completed"}',
            headers={"stripe-signature": "invalid"},
        )
    assert response.status_code == 400


def test_webhook_checkout_completed_upgrades_org_to_pro(client, db_session, configured_billing):
    admin = _register_admin(client, "Upgrade Org", "upgrade-admin@example.com", "upgrade-org").json()

    from app.models.organization import Organization

    organization = db_session.query(Organization).filter(Organization.slug == "upgrade-org").first()
    assert organization.plan == "free"

    fake_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"organization_id": organization.id},
                "subscription": "sub_fake123",
            }
        },
    }
    with patch("app.services.billing.stripe.Webhook.construct_event", return_value=fake_event):
        response = client.post(
            "/webhooks/stripe", content=b"{}", headers={"stripe-signature": "whatever"},
        )
    assert response.status_code == 204

    db_session.expire_all()
    organization = db_session.query(Organization).filter(Organization.slug == "upgrade-org").first()
    assert organization.plan == "pro"
    assert organization.stripe_subscription_id == "sub_fake123"
    assert organization.subscription_status == "active"
    assert organization.max_students == 500


def test_webhook_subscription_canceled_drops_org_back_to_free(client, db_session, configured_billing):
    admin = _register_admin(client, "Cancel Org", "cancel-admin@example.com", "cancel-org").json()

    from app.models.organization import Organization

    organization = db_session.query(Organization).filter(Organization.slug == "cancel-org").first()
    organization.plan = "pro"
    organization.max_students = 500
    organization.max_teachers = 50
    organization.stripe_subscription_id = "sub_to_cancel"
    organization.subscription_status = "active"
    db_session.commit()

    fake_event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_to_cancel", "status": "canceled"}},
    }
    with patch("app.services.billing.stripe.Webhook.construct_event", return_value=fake_event):
        response = client.post(
            "/webhooks/stripe", content=b"{}", headers={"stripe-signature": "whatever"},
        )
    assert response.status_code == 204

    db_session.expire_all()
    organization = db_session.query(Organization).filter(Organization.slug == "cancel-org").first()
    assert organization.plan == "free"
    assert organization.subscription_status == "canceled"
    assert organization.max_students == 30


def test_webhook_for_unknown_organization_id_is_ignored_not_errored(client, configured_billing):
    fake_event = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"organization_id": "org_does_not_exist"}, "subscription": "sub_x"}},
    }
    with patch("app.services.billing.stripe.Webhook.construct_event", return_value=fake_event):
        response = client.post(
            "/webhooks/stripe", content=b"{}", headers={"stripe-signature": "whatever"},
        )
    assert response.status_code == 204
