"""Shared workflow state for LangGraph nodes."""
from typing import TypedDict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

class WorkflowState(TypedDict):
    # Workflow identification
    workflow_id: str
    user_id: str
    instruction: str
    workflow_title: str
    
    # Business context
    business_profile: dict
    
    # Agent results
    research_result: Optional[dict]
    analysis_result: Optional[dict]
    marketing_result: Optional[dict]
    crm_result: Optional[dict]
    approval_ids: List[str]
    report_id: Optional[str]
    
    # Workflow control
    current_step: str
    status: str  # PENDING/RUNNING/PAUSED/COMPLETED/FAILED
    error_message: Optional[str]
    
    # Tracking
    target_count: int
    min_lead_score: int
    execution_logs: List[dict]
    started_at: str
    completed_at: Optional[str]
