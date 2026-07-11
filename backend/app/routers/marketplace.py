from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.user import User
from app.schemas.marketplace import (
    InstallMarketplaceItemRequest,
    InstalledMarketplaceItemOut,
    MarketplaceItemOut,
)
from app.services.marketplace_service import (
    MarketplaceError,
    install_item,
    list_catalog,
    list_installed,
    uninstall_item,
)

router = APIRouter(prefix="/admin/marketplace", tags=["marketplace"], dependencies=[Depends(require_role("admin"))])


def _to_installed_out(install) -> InstalledMarketplaceItemOut:
    return InstalledMarketplaceItemOut(
        id=install.id, item=MarketplaceItemOut.model_validate(install.item), installed_at=install.installed_at
    )


@router.get("/catalog", response_model=list[MarketplaceItemOut])
def get_catalog(db: Session = Depends(get_db)) -> list[MarketplaceItemOut]:
    """The catalog itself isn't organization-scoped — every institute sees the same fixed list; see seed migration 0009."""
    return [MarketplaceItemOut.model_validate(item) for item in list_catalog(db)]


@router.get("/installed", response_model=list[InstalledMarketplaceItemOut])
def get_installed(
    admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> list[InstalledMarketplaceItemOut]:
    return [_to_installed_out(i) for i in list_installed(db, admin.organization_id)]


@router.post("/install", response_model=InstalledMarketplaceItemOut, status_code=status.HTTP_201_CREATED)
def post_install(
    payload: InstallMarketplaceItemRequest,
    admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> InstalledMarketplaceItemOut:
    try:
        install = install_item(db, admin.organization_id, payload.item_id, admin.id)
    except MarketplaceError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return _to_installed_out(install)


@router.delete("/installed/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_install(
    item_id: str, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> None:
    try:
        uninstall_item(db, admin.organization_id, item_id)
    except MarketplaceError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
