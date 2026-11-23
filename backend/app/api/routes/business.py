"""Business profile routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone
from ...database import get_db
from ...api.dependencies import get_current_user
from ...schemas.business_profile import BusinessProfileCreate, BusinessProfileResponse
from ...models.business_profile import BusinessProfile
from ...models.user import User

router = APIRouter(prefix="/api/business", tags=["Business Profile"])


@router.get("/profile", response_model=BusinessProfileResponse)
async def get_profile(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    profile = (
        db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first()
    )
    if not profile:
        raise HTTPException(404, "Business profile not found. Please create one first.")
    return profile


@router.post("/profile", response_model=BusinessProfileResponse, status_code=201)
async def create_profile(
    data: BusinessProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first()
    )
    if existing:
        raise HTTPException(400, "Profile already exists. Use PUT to update.")
    profile = BusinessProfile(id=str(uuid.uuid4()), user_id=current_user.id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/profile", response_model=BusinessProfileResponse)
async def update_profile(
    data: BusinessProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (
        db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first()
    )
    if not profile:
        raise HTTPException(404, "Profile not found. Create one first.")
    for k, v in data.model_dump().items():
        setattr(profile, k, v)
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile
