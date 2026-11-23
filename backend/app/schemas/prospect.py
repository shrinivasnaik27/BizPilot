"""Prospect Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProspectCreate(BaseModel):
    company_name: str
    website: Optional[str] = "unknown"
    industry: Optional[str] = "unknown"
    description: Optional[str] = ""
    location: Optional[str] = "unknown"
    contact_email: Optional[str] = "unknown"
    contact_phone: Optional[str] = "unknown"


class ProspectUpdate(BaseModel):
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    research_status: Optional[str] = None


class ProspectResponse(BaseModel):
    id: str
    user_id: str
    workflow_id: Optional[str] = None
    company_name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    research_confidence: Optional[float] = None
    research_status: Optional[str] = None
    is_demo: bool = False
    created_at: datetime
    lead_score: Optional[int] = None
    priority: Optional[str] = None

    model_config = {"from_attributes": True}
