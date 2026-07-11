import hashlib
import secrets

from sqlalchemy.orm import Session

from app.models.api_access import ApiKey
from app.models.user import utcnow

# Not a security boundary by itself (anyone can read this constant) — it's
# purely a recognizable, greppable prefix, the same idea GitHub/Stripe
# tokens use so a leaked key is identifiable as "a HifzAI key" on sight.
KEY_PREFIX = "hfz_live_"


class ApiKeyError(Exception):
    pass


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _generate_raw_key() -> str:
    return f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"


def create_api_key(db: Session, organization_id: str, created_by_user_id: str, name: str) -> tuple[ApiKey, str]:
    """
    Returns the persisted row plus the one-time raw key. Only the row's
    `hashed_key` is ever committed to the database — the raw value the
    caller returns to the admin isn't retrievable again after this
    function returns, by construction, not by policy.
    """
    raw_key = _generate_raw_key()
    record = ApiKey(
        organization_id=organization_id,
        name=name,
        key_prefix=raw_key[: len(KEY_PREFIX) + 6],
        hashed_key=_hash_key(raw_key),
        created_by_user_id=created_by_user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, raw_key


def list_api_keys(db: Session, organization_id: str) -> list[ApiKey]:
    return (
        db.query(ApiKey)
        .filter(ApiKey.organization_id == organization_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


def revoke_api_key(db: Session, organization_id: str, key_id: str) -> None:
    key = db.get(ApiKey, key_id)
    if key is None or key.organization_id != organization_id:
        raise ApiKeyError("API key not found.")
    if key.revoked_at is None:
        key.revoked_at = utcnow()
        db.commit()


def authenticate(db: Session, raw_key: str) -> ApiKey | None:
    """
    Looks up a key by the hash of the presented value (never by the raw
    value itself — there's no query that could leak a timing signal
    about which raw key exists) and returns it only if it hasn't been
    revoked. Updates `last_used_at` on every successful call, the only
    mutation this otherwise read-only public API makes.
    """
    hashed = _hash_key(raw_key)
    key = db.query(ApiKey).filter(ApiKey.hashed_key == hashed).first()
    if key is None or key.revoked_at is not None:
        return None
    key.last_used_at = utcnow()
    db.commit()
    return key
