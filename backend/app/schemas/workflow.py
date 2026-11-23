"""Workflow Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WorkflowCreate(BaseModel):
    instruction: str = Field(..., min_length=10, description="Natural language business instruction")
    title: Optional[str] = None
    target_count: int = Field(default=5, ge=1, le=20)
    min_lead_score: int = Field(default=40, ge=0, le=100)


class WorkflowResponse(BaseModel):
    id: str
    user_id: str
    title: str
    instruction: str
    status: str
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
