from app.schemas.base import CamelModel


class CheckoutSessionRequest(CamelModel):
    success_url: str
    cancel_url: str


class CheckoutSessionOut(CamelModel):
    checkout_url: str


class BillingPortalRequest(CamelModel):
    return_url: str


class BillingPortalOut(CamelModel):
    portal_url: str


class BillingStatusOut(CamelModel):
    plan: str
    subscription_status: str | None
    max_students: int
    max_teachers: int
    has_billing_history: bool
