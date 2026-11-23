"""Approval Pydantic schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApprovalResponse(BaseModel):
    id: str
    workflow_id: str
    action_type: str
    action_description: str
    target_company: Optional[str] = None
    target_email: Optional[str] = None
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    draft_id: Optional[str] = None
    draft_subject: Optional[str] = None
    draft_body: Optional[str] = None

    model_config = {"from_attributes": True}


class ApproveRequest(BaseModel):
    edited_subject: Optional[str] = None
    edited_body: Optional[str] = None


class RejectRequest(BaseModel):
    reason: Optional[str] = ""
