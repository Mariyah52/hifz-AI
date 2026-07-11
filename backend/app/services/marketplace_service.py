import json

from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceItem, OrganizationMarketplaceInstall
from app.models.organization import Organization


class MarketplaceError(Exception):
    pass


def list_catalog(db: Session) -> list[MarketplaceItem]:
    return db.query(MarketplaceItem).order_by(MarketplaceItem.category, MarketplaceItem.name).all()


def list_installed(db: Session, organization_id: str) -> list[OrganizationMarketplaceInstall]:
    return (
        db.query(OrganizationMarketplaceInstall)
        .filter(OrganizationMarketplaceInstall.organization_id == organization_id)
        .order_by(OrganizationMarketplaceInstall.installed_at.desc())
        .all()
    )


def install_item(db: Session, organization_id: str, item_id: str, user_id: str) -> OrganizationMarketplaceInstall:
    item = db.get(MarketplaceItem, item_id)
    if item is None:
        raise MarketplaceError("This catalog item does not exist.")

    existing = (
        db.query(OrganizationMarketplaceInstall)
        .filter(
            OrganizationMarketplaceInstall.organization_id == organization_id,
            OrganizationMarketplaceInstall.item_id == item_id,
        )
        .first()
    )
    if existing is not None:
        raise MarketplaceError("This item is already installed.")

    install = OrganizationMarketplaceInstall(
        organization_id=organization_id, item_id=item_id, installed_by_user_id=user_id
    )
    db.add(install)

    # The one category with a real, wired-up effect today — see
    # MarketplaceItem's docstring for why the other four categories stop
    # at catalog browsing + install-state tracking.
    if item.category == "theme" and item.config_json:
        config = json.loads(item.config_json)
        primary_color = config.get("primaryColor")
        if primary_color:
            organization = db.get(Organization, organization_id)
            if organization is not None:
                organization.primary_color = primary_color

    db.commit()
    db.refresh(install)
    return install


def uninstall_item(db: Session, organization_id: str, item_id: str) -> None:
    install = (
        db.query(OrganizationMarketplaceInstall)
        .filter(
            OrganizationMarketplaceInstall.organization_id == organization_id,
            OrganizationMarketplaceInstall.item_id == item_id,
        )
        .first()
    )
    if install is None:
        raise MarketplaceError("This item isn't installed.")
    db.delete(install)
    db.commit()
