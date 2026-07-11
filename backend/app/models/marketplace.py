from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id, utcnow

MARKETPLACE_CATEGORIES = ("question_bank", "revision_plan", "reciter", "theme", "plugin")


class MarketplaceItem(Base):
    """
    The marketplace catalog (Phase 29): question banks, revision plans,
    premium reciters, themes, and plugins an institute can add on top of
    the base app. Catalog rows are seeded once, by migration
    0009_marketplace.py — there's no vendor-facing "list your product"
    flow or admin-facing catalog editor. That's a deliberate scope cut,
    the same one Phase 18 made for billing: a real, enforced data model
    with a fixed, curated set of rows, not a live marketplace supply side.

    `config_json` is a small opaque JSON string interpreted only by the
    one category with a real, wired-up effect today: installing a
    `theme` item copies its `primaryColor` into the org's existing
    Phase 18 branding field (see `services/marketplace_service.py`).
    Every other category — question_bank, revision_plan, reciter,
    plugin — is real catalog browsing + install-state tracking with
    **no consumer wired up yet**. That's the same "real data model, no
    consumer" pattern Phase 18 used for `Organization.primaryColor`/
    `logoUrl` before any page rendered them, stated plainly rather than
    implied.
    """

    __tablename__ = "marketplace_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("mkt"))
    category: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    price_cents: Mapped[int] = mapped_column(Integer, default=0)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OrganizationMarketplaceInstall(Base):
    """
    One row per organization that has installed one catalog item.
    **No payment is actually collected** for premium items — installing
    one is instant, exactly like installing a free one. See
    `MarketplaceItem`'s docstring and the root README's Phase 29 notes
    for why: this app has never built real billing (Phase 18 said so
    first, about plan upgrades), and a marketplace "buy" flow would need
    the same real payment-processor integration that was out of scope
    there too.
    """

    __tablename__ = "organization_marketplace_installs"
    __table_args__ = (UniqueConstraint("organization_id", "item_id", name="uq_org_marketplace_item"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("mktinst"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("marketplace_items.id"), index=True)
    installed_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    item: Mapped["MarketplaceItem"] = relationship()
