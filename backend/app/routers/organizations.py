from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.organization import OrganizationPublicOut
from app.services.tenancy import get_organization_by_slug

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/{slug}/public", response_model=OrganizationPublicOut)
def get_organization_public_info(slug: str, db: Session = Depends(get_db)) -> OrganizationPublicOut:
    """
    Deliberately minimal: name + branding only, no counts or plan info —
    this is fetched by the login page before anyone has authenticated,
    so it must never leak anything beyond "this organization exists and
    here's how it's branded."
    """
    organization = get_organization_by_slug(db, slug)
    if organization is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No organization found with that slug")

    return OrganizationPublicOut(
        name=organization.name,
        slug=organization.slug,
        primary_color=organization.primary_color,
        logo_url=organization.logo_url,
    )
