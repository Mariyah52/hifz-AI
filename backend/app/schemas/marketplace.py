from datetime import datetime

from app.schemas.base import CamelModel


class MarketplaceItemOut(CamelModel):
    id: str
    category: str
    name: str
    description: str
    price_cents: int
    is_premium: bool


class InstalledMarketplaceItemOut(CamelModel):
    id: str
    item: MarketplaceItemOut
    installed_at: datetime


class InstallMarketplaceItemRequest(CamelModel):
    item_id: str
