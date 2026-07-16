import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.models.organization import PLAN_DEFAULTS, Organization

"""
Phase 32: real Stripe billing — an admin can actually pay to upgrade an
organization's plan, rather than plan changes only ever happening via a
manual DB edit (see Organization's docstring for the before/after).

Two real, separate flows:

1. `create_checkout_session` — an admin clicks "Upgrade to Pro", this
   creates a real Stripe Checkout Session and returns its URL; the
   browser redirects there, Stripe hosts the actual payment form (this
   app never touches card details — Checkout is Stripe-hosted precisely
   so this app doesn't need PCI compliance).

2. `handle_webhook_event` — Stripe calls back into
   `POST /webhooks/stripe` when something happens (checkout completed,
   subscription renewed/canceled/payment failed). This is the ONLY place
   `Organization.plan` actually changes as a result of payment — the
   Checkout redirect itself doesn't upgrade anything, since a user
   landing back on a "success" URL doesn't prove Stripe actually charged
   the card yet. Trusting the webhook, not the redirect, is deliberate.

Stated, real limitations — not fixed here:
  - No proration, seat-based billing, or annual plans — one flat "pro"
    monthly price, matching PLAN_DEFAULTS' current two-tier model.
  - No dunning/retry customization — relies entirely on Stripe's own
    default retry schedule for failed payments.
  - No invoice/receipt UI in this app — an admin gets Stripe's own emailed
    receipts; there's no in-app billing history page.
  - Webhook handler updates `plan`/`subscription_status` but does NOT
    email anyone about the change — Phase 16's notification system isn't
    wired to billing events yet.
"""


class BillingNotConfigured(Exception):
    pass


class BillingError(Exception):
    pass


def _require_stripe_configured() -> None:
    if not settings.stripe_secret_key:
        raise BillingNotConfigured(
            "Billing isn't configured on this deployment yet (STRIPE_SECRET_KEY is unset)."
        )
    stripe.api_key = settings.stripe_secret_key


def create_checkout_session(db: Session, organization: Organization, success_url: str, cancel_url: str) -> str:
    """
    Returns a Stripe-hosted Checkout URL for upgrading `organization` to
    the "pro" plan. Creates a Stripe Customer for this org on first use
    (stored on the org so future checkouts/portal sessions reuse it
    instead of creating a duplicate customer every time).
    """
    _require_stripe_configured()
    if not settings.stripe_pro_price_id:
        raise BillingNotConfigured("STRIPE_PRO_PRICE_ID isn't set — create a Price in the Stripe Dashboard first.")

    if organization.stripe_customer_id is None:
        customer = stripe.Customer.create(
            name=organization.name,
            metadata={"organization_id": organization.id},
        )
        organization.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=organization.stripe_customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_pro_price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"organization_id": organization.id},
    )
    return session.url


def create_billing_portal_session(db: Session, organization: Organization, return_url: str) -> str:
    """
    Stripe's own hosted page for an admin to update their card, view past
    invoices, or cancel — this app doesn't build any of that UI itself.
    Requires the org to already have a Stripe customer (i.e. has checked
    out at least once).
    """
    _require_stripe_configured()
    if organization.stripe_customer_id is None:
        raise BillingError("This organization has no billing history yet — nothing to manage.")

    portal_session = stripe.billing_portal.Session.create(
        customer=organization.stripe_customer_id,
        return_url=return_url,
    )
    return portal_session.url


def verify_webhook_signature(payload: bytes, signature_header: str) -> "stripe.Event":
    """
    Raises stripe.error.SignatureVerificationError (not caught here — the
    router catches it) if `signature_header` doesn't match what Stripe
    would have actually sent for this exact payload. Never process a
    webhook body without calling this first.
    """
    _require_stripe_configured()
    if not settings.stripe_webhook_secret:
        raise BillingNotConfigured("STRIPE_WEBHOOK_SECRET isn't set — cannot verify incoming webhooks.")
    return stripe.Webhook.construct_event(payload, signature_header, settings.stripe_webhook_secret)


def handle_webhook_event(db: Session, event: "stripe.Event") -> None:
    """
    The real source of truth for plan changes — see module docstring for
    why this, and not the Checkout success redirect, is what actually
    changes `Organization.plan`.
    """
    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        organization_id = data_object.get("metadata", {}).get("organization_id")
        organization = db.get(Organization, organization_id) if organization_id else None
        if organization is None:
            return  # A checkout for an org this app doesn't recognize — nothing to update.
        organization.stripe_subscription_id = data_object.get("subscription")
        organization.plan = "pro"
        organization.max_students = PLAN_DEFAULTS["pro"]["max_students"]
        organization.max_teachers = PLAN_DEFAULTS["pro"]["max_teachers"]
        organization.subscription_status = "active"
        db.commit()

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        subscription_id = data_object.get("id")
        organization = (
            db.query(Organization).filter(Organization.stripe_subscription_id == subscription_id).first()
        )
        if organization is None:
            return
        organization.subscription_status = data_object.get("status", "canceled")
        # A subscription that's no longer active drops the org back to
        # free-plan limits — real enforcement, not just a status label
        # nobody reads. Existing students/teachers over the free cap are
        # NOT removed (this app never deletes users for a billing lapse);
        # the org just can't add new ones until it upgrades again or
        # drops below the free cap on its own.
        if organization.subscription_status not in ("active", "trialing"):
            organization.plan = "free"
            organization.max_students = PLAN_DEFAULTS["free"]["max_students"]
            organization.max_teachers = PLAN_DEFAULTS["free"]["max_teachers"]
        db.commit()
