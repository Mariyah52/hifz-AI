from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.base import to_camel
from app.schemas.data_privacy import DeleteAccountRequest, DeleteAccountSummary, RetentionPolicyOut
from app.security import verify_password
from app.services.data_privacy import RETENTION_POLICY, anonymize_and_delete_account, export_user_data

router = APIRouter(prefix="/me/privacy", tags=["privacy"])


def _camel_case_keys(value):
    """
    Recursively converts dict keys from snake_case to camelCase, matching
    every other response in this app (see schemas/base.py's CamelModel).
    export_user_data() returns plain dicts rather than Pydantic models
    (its shape is genuinely dynamic per role), so that conversion has to
    happen here instead of via a schema's alias_generator.
    """
    if isinstance(value, dict):
        return {to_camel(k): _camel_case_keys(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_camel_case_keys(v) for v in value]
    return value


@router.get("/retention-policy", response_model=RetentionPolicyOut)
def get_retention_policy() -> RetentionPolicyOut:
    """
    Real, current retention defaults this app's code actually enforces —
    see services/data_privacy.py's module docstring for the honest caveat
    that these are engineering defaults, not a reviewed legal policy.
    """
    return RetentionPolicyOut(**RETENTION_POLICY)


@router.get("/export")
def export_my_data(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> JSONResponse:
    """
    Right-to-access/portability: every row this app stores that's tied to
    the requesting user, as a downloadable JSON file. Available to any
    authenticated role, not just students — see export_user_data for
    exactly what's included per role.
    """
    data = export_user_data(db, user)
    return JSONResponse(
        content=_camel_case_keys(data),
        headers={"Content-Disposition": f'attachment; filename="hifzai-data-export-{user.id}.json"'},
    )


@router.post("/delete-account", response_model=DeleteAccountSummary)
def delete_my_account(
    payload: DeleteAccountRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DeleteAccountSummary:
    """
    Right-to-erasure, self-service. Requires the user's current password
    (proof of intent — this is destructive and immediate, no undo) and an
    explicit `confirm: true` from the frontend, which should only be
    reachable after a real "this is permanent" warning is shown, not a
    default-checked box.

    See services/data_privacy.py's anonymize_and_delete_account docstring
    for exactly what "deletion" means here — it's real, but it's
    anonymization-in-place, not a hard row delete, for reasons explained
    there.
    """
    if not payload.confirm:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You must confirm this action before it can proceed.")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    summary = anonymize_and_delete_account(db, user)
    db.commit()
    return DeleteAccountSummary(**summary)
