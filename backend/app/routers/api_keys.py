from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models.user import User
from app.schemas.api_access import ApiKeyCreatedOut, ApiKeyOut, CreateApiKeyRequest
from app.services.api_key_service import ApiKeyError, create_api_key, list_api_keys, revoke_api_key

router = APIRouter(prefix="/admin/api-keys", tags=["api-keys"], dependencies=[Depends(require_role("admin"))])


@router.get("", response_model=list[ApiKeyOut])
def get_api_keys(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> list[ApiKeyOut]:
    return [ApiKeyOut.model_validate(k) for k in list_api_keys(db, admin.organization_id)]


@router.post("", response_model=ApiKeyCreatedOut, status_code=status.HTTP_201_CREATED)
def post_api_key(
    payload: CreateApiKeyRequest, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)
) -> ApiKeyCreatedOut:
    record, raw_key = create_api_key(db, admin.organization_id, admin.id, payload.name)
    return ApiKeyCreatedOut(
        id=record.id,
        name=record.name,
        key_prefix=record.key_prefix,
        created_at=record.created_at,
        last_used_at=record.last_used_at,
        revoked_at=record.revoked_at,
        api_key=raw_key,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(key_id: str, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)) -> None:
    try:
        revoke_api_key(db, admin.organization_id, key_id)
    except ApiKeyError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
