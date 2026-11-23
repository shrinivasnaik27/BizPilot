"""LangGraph workflow definition and orchestrator."""
import asyncio, uuid, json
from typing import Optional
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from ..graph.state import WorkflowState
from ..graph.nodes import (research_node, analysis_node, marketing_node, crm_node,
                           approval_node, reporting_node, should_continue_after_research,
                           should_continue_after_crm)
from ..models.workflow import Workflow
from ..models.business_profile import BusinessProfile
from ..database import SessionLocal
from ..utils.logger import get_logger

logger = get_logger(__name__)

def build_workflow_graph() -> StateGraph:
    """Build the LangGraph state machine."""
    graph = StateGraph(WorkflowState)
    
    # Add nodes
    graph.add_node("research", research_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("marketing", marketing_node)
    graph.add_node("crm", crm_node)
    graph.add_node("approval", approval_node)
    graph.add_node("reporting", reporting_node)
    
    # Set entry point
    graph.set_entry_point("research")
    
    # Add conditional edges
    graph.add_conditional_edges(
        "research",
        should_continue_after_research,
        {
            "continue": "analysis",
            "no_prospects": "reporting",
            "failed": END
        }
    )
    
    graph.add_edge("analysis", "marketing")
    graph.add_edge("marketing", "crm")
    
    graph.add_conditional_edges(
        "crm",
        should_continue_after_crm,
        {
            "needs_approval": "approval",
            "skip_approval": "reporting",
            "failed": END
        }
    )
    
    # After approval node: workflow PAUSES (returns PAUSED state)
    graph.add_edge("approval", END)  
    # Reporting leads to end
    graph.add_edge("reporting", END)
    
    return graph.compile()

class BizPilotOrchestrator:
    """Central orchestrator for BizPilot AI workflows."""
    
    def __init__(self):
        self._graph = None
    
    @property
    def graph(self):
        if self._graph is None:
            self._graph = build_workflow_graph()
        return self._graph
    
    def _get_business_profile(self, db: Session, user_id: str) -> dict:
        """Get user's business profile."""
        profile = db.query(BusinessProfile).filter(BusinessProfile.user_id == user_id).first()
        if profile:
            return {
                "business_name": profile.business_name,
                "description": profile.description,
                "services": profile.services,
                "target_industries": profile.target_industries,
                "target_locations": profile.target_locations,
                "ideal_customer": profile.ideal_customer,
                "tone": profile.tone,
            }
        return {
            "business_name": "Your Company",
            "description": "Business automation services",
            "services": "AI-powered automation",
            "target_industries": "Technology, Healthcare, Finance",
            "target_locations": "India",
            "ideal_customer": "Growing startups and SMBs",
            "tone": "professional",
        }
    
    async def start_workflow(self, db: Session, workflow_id: str, user_id: str, 
                              instruction: str, target_count: int = 5, min_lead_score: int = 40) -> WorkflowState:
        """Start a new workflow."""
        logger.info(f"Orchestrator: Starting workflow {workflow_id}")
        
        # Update workflow status
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if workflow:
            workflow.status = "RUNNING"
            workflow.started_at = datetime.now(timezone.utc)
            workflow.current_step = "RESEARCH"
            db.commit()
        
        business_profile = self._get_business_profile(db, user_id)
        
        initial_state: WorkflowState = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "instruction": instruction,
            "workflow_title": workflow.title if workflow else "Workflow",
            "business_profile": business_profile,
            "research_result": None,
            "analysis_result": None,
            "marketing_result": None,
            "crm_result": None,
            "approval_ids": [],
            "report_id": None,
            "current_step": "RESEARCH",
            "status": "RUNNING",
            "error_message": None,
            "target_count": target_count,
            "min_lead_score": min_lead_score,
            "execution_logs": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
        
        try:
            final_state = await asyncio.wait_for(
                self.graph.ainvoke(initial_state),
                timeout=300  # 5 minute timeout
            )
            
            # Persist final state
            if workflow:
                workflow.metadata_ = json.dumps({
                    "research_result": final_state.get("research_result"),
                    "analysis_result": final_state.get("analysis_result"),
                    "approval_ids": final_state.get("approval_ids", []),
                    "report_id": final_state.get("report_id"),
                })
                db.commit()
            
            return final_state
            
        except asyncio.TimeoutError:
            logger.error(f"Workflow {workflow_id} timed out")
            if workflow:
                workflow.status = "FAILED"
                workflow.error_message = "Workflow timed out after 5 minutes"
                db.commit()
            raise
    
    async def resume_workflow(self, db: Session, workflow_id: str, user_id: str) -> WorkflowState:
        """Resume workflow after approvals - run reporting."""
        logger.info(f"Orchestrator: Resuming workflow {workflow_id} for reporting")
        
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Update status
        workflow.status = "RUNNING"
        workflow.current_step = "REPORTING"
        db.commit()
        
        # Run only the reporting node
        from ..graph.nodes import reporting_node
        
        # Reconstruct state from DB metadata
        metadata = json.loads(workflow.metadata_ or '{}')
        
        state: WorkflowState = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "instruction": workflow.instruction,
            "workflow_title": workflow.title,
            "business_profile": self._get_business_profile(db, user_id),
            "research_result": metadata.get("research_result"),
            "analysis_result": metadata.get("analysis_result"),
            "marketing_result": metadata.get("marketing_result"),
            "crm_result": metadata.get("crm_result"),
            "approval_ids": metadata.get("approval_ids", []),
            "report_id": None,
            "current_step": "REPORTING",
            "status": "RUNNING",
            "error_message": None,
            "target_count": 5,
            "min_lead_score": 40,
            "execution_logs": [],
            "started_at": workflow.started_at.isoformat() if workflow.started_at else datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
        }
        
        final_state = await reporting_node(state)
        
        # Persist report_id
        if final_state.get("report_id") and workflow:
            meta = json.loads(workflow.metadata_ or '{}')
            meta["report_id"] = final_state["report_id"]
            workflow.metadata_ = json.dumps(meta)
            db.commit()
        
        return final_state

orchestrator = BizPilotOrchestrator()
