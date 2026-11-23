"""Business Profile Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BusinessProfileCreate(BaseModel):
    business_name: str
    description: str
    services: str
    target_industries: Optional[str] = ""
    target_locations: Optional[str] = ""
    ideal_customer: Optional[str] = ""
    tone: Optional[str] = "professional"
    website: Optional[str] = ""
    business_email: Optional[str] = ""


class BusinessProfileResponse(BaseModel):
    id: str
    user_id: str
    business_name: str
    description: str
    services: str
    target_industries: Optional[str] = None
    target_locations: Optional[str] = None
    ideal_customer: Optional[str] = None
    tone: Optional[str] = None
    website: Optional[str] = None
    business_email: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
