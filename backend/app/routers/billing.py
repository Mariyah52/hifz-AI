import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.organization import Organization
from app.models.user import User
from app.schemas.billing import (
    BillingPortalOut,
    BillingPortalRequest,
    BillingStatusOut,
    CheckoutSessionOut,
    CheckoutSessionRequest,
)
from app.services.billing import (
    BillingError,
    BillingNotConfigured,
    create_billing_portal_session,
    create_checkout_session,
    handle_webhook_event,
    verify_webhook_signature,
)

router = APIRouter(tags=["billing"])


@router.get("/admin/billing/status", response_model=BillingStatusOut)
def get_billing_status(
    admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> BillingStatusOut:
    organization = db.get(Organization, admin.organization_id)
    return BillingStatusOut(
        plan=organization.plan,
        subscription_status=organization.subscription_status,
        max_students=organization.max_students,
        max_teachers=organization.max_teachers,
        has_billing_history=organization.stripe_customer_id is not None,
    )


@router.post("/admin/billing/checkout-session", response_model=CheckoutSessionOut)
def post_checkout_session(
    payload: CheckoutSessionRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> CheckoutSessionOut:
    organization = db.get(Organization, admin.organization_id)
    try:
        checkout_url = create_checkout_session(db, organization, payload.success_url, payload.cancel_url)
    except BillingNotConfigured as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    return CheckoutSessionOut(checkout_url=checkout_url)


@router.post("/admin/billing/portal-session", response_model=BillingPortalOut)
def post_billing_portal_session(
    payload: BillingPortalRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> BillingPortalOut:
    organization = db.get(Organization, admin.organization_id)
    try:
        portal_url = create_billing_portal_session(db, organization, payload.return_url)
    except BillingNotConfigured as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except BillingError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return BillingPortalOut(portal_url=portal_url)


@router.post("/webhooks/stripe", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> None:
    """
    No auth dependency — Stripe itself calls this, not a logged-in user.
    Authenticity instead comes entirely from `verify_webhook_signature`,
    which rejects anything not actually signed by Stripe with this app's
    own webhook secret. Never trust `request.body()` here without that
    check passing first.
    """
    payload = await request.body()
    signature_header = request.headers.get("stripe-signature", "")

    try:
        event = verify_webhook_signature(payload, signature_header)
    except BillingNotConfigured as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid webhook signature: {exc}") from exc

    handle_webhook_event(db, event)
