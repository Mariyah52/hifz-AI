from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.user import new_id, utcnow


class ApiKey(Base):
    """
    Phase 30: one row per organization-issued public API key. Only
    `hashed_key` (SHA-256, see `services/api_key_service.py`) is ever
    stored — the raw key is shown to the admin exactly once, at creation
    time, the same "hash it, never store it" principle Phase 17 applied
    to refresh tokens. `key_prefix` (the raw key's first several
    characters) is stored in the clear purely so an admin can tell keys
    apart in a list without the actual secret ever touching a database
    row a second time.
    """

    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("key"))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    key_prefix: Mapped[str] = mapped_column(String)
    hashed_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
