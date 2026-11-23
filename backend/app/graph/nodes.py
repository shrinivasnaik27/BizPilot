"""LangGraph node implementations for each agent step."""
import uuid, json, asyncio
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from ..graph.state import WorkflowState
from ..agents.research_agent import research_agent
from ..agents.analysis_agent import analysis_agent
from ..agents.marketing_agent import marketing_agent
from ..agents.crm_agent import crm_agent
from ..agents.approval_agent import approval_agent
from ..agents.reporting_agent import reporting_agent
from ..models.workflow import Workflow
from ..models.execution_log import ExecutionLog
from ..database import SessionLocal
from ..utils.logger import get_logger
import time

logger = get_logger(__name__)

def _log_execution(db: Session, workflow_id: str, agent_name: str, action: str, status: str, 
                   input_summary: str = None, output_summary: str = None, 
                   error_message: str = None, duration_ms: int = None):
    """Log an agent execution step."""
    log = ExecutionLog(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        agent_name=agent_name,
        action=action,
        status=status,
        input_summary=input_summary,
        output_summary=output_summary,
        error_message=error_message,
        duration_ms=duration_ms,
    )
    db.add(log)
    db.commit()

def _update_workflow_step(db: Session, workflow_id: str, step: str, status: str = None, error: str = None):
    """Update workflow current step in DB."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if workflow:
        workflow.current_step = step
        if status:
            workflow.status = status
        if error:
            workflow.error_message = error
        workflow.updated_at = datetime.now(timezone.utc)
        db.commit()

async def research_node(state: WorkflowState) -> WorkflowState:
    """Execute the Research Agent."""
    db = SessionLocal()
    start_time = time.time()
    try:
        logger.info(f"[{state['workflow_id']}] Research node starting")
        _update_workflow_step(db, state['workflow_id'], "RESEARCH", "RUNNING")
        
        result = await research_agent.research(
            instruction=state['instruction'],
            target_count=state.get('target_count', 5),
            existing_companies=[]
        )
        
        duration = int((time.time() - start_time) * 1000)
        _log_execution(db, state['workflow_id'], "Research Agent", "research_prospects",
                      "SUCCESS", state['instruction'][:200],
                      f"Found {result.total_found} prospects via {result.research_provider}",
                      duration_ms=duration)
        
        new_state = dict(state)
        new_state['research_result'] = result.model_dump()
        new_state['current_step'] = "ANALYSIS"
        new_state['execution_logs'] = state.get('execution_logs', []) + [{
            "agent": "Research Agent", "status": "SUCCESS", "prospects": result.total_found
        }]
        return new_state
        
    except Exception as e:
        logger.error(f"Research node failed: {e}")
        _log_execution(db, state['workflow_id'], "Research Agent", "research_prospects",
                      "FAILED", error_message=str(e))
        _update_workflow_step(db, state['workflow_id'], "RESEARCH_FAILED", "FAILED", str(e))
        new_state = dict(state)
        new_state['error_message'] = f"Research failed: {str(e)}"
        new_state['status'] = "FAILED"
        return new_state
    finally:
        db.close()

async def analysis_node(state: WorkflowState) -> WorkflowState:
    """Execute the Analysis Agent."""
    db = SessionLocal()
    start_time = time.time()
    try:
        logger.info(f"[{state['workflow_id']}] Analysis node starting")
        _update_workflow_step(db, state['workflow_id'], "ANALYSIS")
        
        research_data = state.get('research_result', {})
        from ..agents.research_agent import ProspectResearch
        prospects = [ProspectResearch(**p) for p in research_data.get('prospects', [])]
        
        if not prospects:
            new_state = dict(state)
            new_state['analysis_result'] = {"scored_prospects": [], "high_priority_count": 0, "medium_priority_count": 0, "low_priority_count": 0, "analysis_timestamp": datetime.now(timezone.utc).isoformat(), "is_demo": True}
            new_state['current_step'] = "MARKETING"
            return new_state
        
        business_context = json.dumps(state.get('business_profile', {}))
        result = await analysis_agent.analyze(prospects, business_context, state['instruction'])
        
        duration = int((time.time() - start_time) * 1000)
        _log_execution(db, state['workflow_id'], "Analysis Agent", "score_prospects",
                      "SUCCESS", f"{len(prospects)} prospects",
                      f"High: {result.high_priority_count}, Medium: {result.medium_priority_count}, Low: {result.low_priority_count}",
                      duration_ms=duration)
        
        new_state = dict(state)
        new_state['analysis_result'] = result.model_dump()
        new_state['current_step'] = "MARKETING"
        new_state['execution_logs'] = state.get('execution_logs', []) + [{
            "agent": "Analysis Agent", "status": "SUCCESS", 
            "high": result.high_priority_count, "medium": result.medium_priority_count
        }]
        return new_state
        
    except Exception as e:
        logger.error(f"Analysis node failed: {e}")
        _log_execution(db, state['workflow_id'], "Analysis Agent", "score_prospects", "FAILED", error_message=str(e))
        new_state = dict(state)
        new_state['error_message'] = f"Analysis failed: {str(e)}"
        new_state['status'] = "FAILED"
        return new_state
    finally:
        db.close()

async def marketing_node(state: WorkflowState) -> WorkflowState:
    """Execute the Marketing Agent."""
    db = SessionLocal()
    start_time = time.time()
    try:
        logger.info(f"[{state['workflow_id']}] Marketing node starting")
        _update_workflow_step(db, state['workflow_id'], "MARKETING")
        
        research_data = state.get('research_result', {})
        analysis_data = state.get('analysis_result', {})
        
        from ..agents.research_agent import ProspectResearch
        from ..agents.analysis_agent import LeadScore
        prospects = [ProspectResearch(**p) for p in research_data.get('prospects', [])]
        scores = [LeadScore(**s) for s in analysis_data.get('scored_prospects', [])]
        
        result = await marketing_agent.generate_drafts(
            prospects=prospects,
            scores=scores,
            business_profile=state.get('business_profile', {}),
            min_score=state.get('min_lead_score', 40)
        )
        
        duration = int((time.time() - start_time) * 1000)
        _log_execution(db, state['workflow_id'], "Marketing Agent", "generate_drafts",
                      "SUCCESS", f"{len(prospects)} prospects",
                      f"Generated {result.total_generated} email drafts",
                      duration_ms=duration)
        
        new_state = dict(state)
        new_state['marketing_result'] = result.model_dump()
        new_state['current_step'] = "CRM"
        new_state['execution_logs'] = state.get('execution_logs', []) + [{
            "agent": "Marketing Agent", "status": "SUCCESS", "drafts": result.total_generated
        }]
        return new_state
        
    except Exception as e:
        logger.error(f"Marketing node failed: {e}")
        _log_execution(db, state['workflow_id'], "Marketing Agent", "generate_drafts", "FAILED", error_message=str(e))
        new_state = dict(state)
        new_state['error_message'] = f"Marketing failed: {str(e)}"
        new_state['status'] = "FAILED"
        return new_state
    finally:
        db.close()

async def crm_node(state: WorkflowState) -> WorkflowState:
    """Execute the CRM Agent."""
    db = SessionLocal()
    start_time = time.time()
    try:
        logger.info(f"[{state['workflow_id']}] CRM node starting")
        _update_workflow_step(db, state['workflow_id'], "CRM")
        
        research_data = state.get('research_result', {})
        analysis_data = state.get('analysis_result', {})
        marketing_data = state.get('marketing_result', {})
        
        from ..agents.research_agent import ProspectResearch
        from ..agents.analysis_agent import LeadScore
        from ..agents.marketing_agent import EmailDraft
        
        prospects = [ProspectResearch(**p) for p in research_data.get('prospects', [])]
        scores = [LeadScore(**s) for s in analysis_data.get('scored_prospects', [])]
        drafts = [EmailDraft(**d) for d in marketing_data.get('drafts', [])]
        
        result = crm_agent.save_prospects(
            db=db,
            prospects=prospects,
            scores=scores,
            drafts=drafts,
            workflow_id=state['workflow_id'],
            user_id=state['user_id']
        )
        
        duration = int((time.time() - start_time) * 1000)
        _log_execution(db, state['workflow_id'], "CRM Agent", "save_prospects",
                      "SUCCESS", f"{len(prospects)} prospects",
                      f"Saved: {result.prospects_saved}, Updated: {result.prospects_updated}, Drafts: {result.drafts_saved}",
                      duration_ms=duration)
        
        crm_data = {
            "prospects_saved": result.prospects_saved,
            "prospects_updated": result.prospects_updated,
            "analyses_saved": result.analyses_saved,
            "drafts_saved": result.drafts_saved,
            "prospect_ids": result.prospect_ids,
            "draft_ids": result.draft_ids,
            "errors": result.errors
        }
        
        new_state = dict(state)
        new_state['crm_result'] = crm_data
        new_state['current_step'] = "APPROVAL"
        new_state['execution_logs'] = state.get('execution_logs', []) + [{
            "agent": "CRM Agent", "status": "SUCCESS", 
            "saved": result.prospects_saved, "drafts": result.drafts_saved
        }]
        return new_state
        
    except Exception as e:
        logger.error(f"CRM node failed: {e}")
        _log_execution(db, state['workflow_id'], "CRM Agent", "save_prospects", "FAILED", error_message=str(e))
        new_state = dict(state)
        new_state['error_message'] = f"CRM failed: {str(e)}"
        new_state['status'] = "FAILED"
        return new_state
    finally:
        db.close()

async def approval_node(state: WorkflowState) -> WorkflowState:
    """Execute the Approval Agent - creates pending approvals and pauses."""
    db = SessionLocal()
    start_time = time.time()
    try:
        logger.info(f"[{state['workflow_id']}] Approval node starting")
        _update_workflow_step(db, state['workflow_id'], "AWAITING_APPROVAL", "PAUSED")
        
        crm_data = state.get('crm_result', {})
        draft_ids = crm_data.get('draft_ids', [])
        
        approval_ids = approval_agent.create_email_approvals(
            db=db,
            draft_ids=draft_ids,
            workflow_id=state['workflow_id'],
            user_id=state['user_id']
        )
        
        duration = int((time.time() - start_time) * 1000)
        _log_execution(db, state['workflow_id'], "Approval Agent", "create_approvals",
                      "SUCCESS", f"{len(draft_ids)} drafts",
                      f"Created {len(approval_ids)} approval requests",
                      duration_ms=duration)
        
        new_state = dict(state)
        new_state['approval_ids'] = approval_ids
        new_state['current_step'] = "AWAITING_APPROVAL"
        new_state['status'] = "PAUSED"
        new_state['execution_logs'] = state.get('execution_logs', []) + [{
            "agent": "Approval Agent", "status": "SUCCESS", "approvals": len(approval_ids)
        }]
        return new_state
        
    except Exception as e:
        logger.error(f"Approval node failed: {e}")
        _log_execution(db, state['workflow_id'], "Approval Agent", "create_approvals", "FAILED", error_message=str(e))
        new_state = dict(state)
        new_state['error_message'] = f"Approval setup failed: {str(e)}"
        new_state['status'] = "FAILED"
        return new_state
    finally:
        db.close()

async def reporting_node(state: WorkflowState) -> WorkflowState:
    """Execute the Reporting Agent."""
    db = SessionLocal()
    start_time = time.time()
    try:
        logger.info(f"[{state['workflow_id']}] Reporting node starting")
        _update_workflow_step(db, state['workflow_id'], "REPORTING")
        
        report_id = reporting_agent.generate_report(
            db=db,
            workflow_id=state['workflow_id'],
            user_id=state['user_id']
        )
        
        duration = int((time.time() - start_time) * 1000)
        _log_execution(db, state['workflow_id'], "Reporting Agent", "generate_report",
                      "SUCCESS", state['workflow_id'],
                      f"Report generated: {report_id}",
                      duration_ms=duration)
        
        _update_workflow_step(db, state['workflow_id'], "COMPLETED", "COMPLETED")
        workflow = db.query(Workflow).filter(Workflow.id == state['workflow_id']).first()
        if workflow:
            workflow.completed_at = datetime.now(timezone.utc)
            db.commit()
        
        new_state = dict(state)
        new_state['report_id'] = report_id
        new_state['current_step'] = "COMPLETED"
        new_state['status'] = "COMPLETED"
        new_state['completed_at'] = datetime.now(timezone.utc).isoformat()
        return new_state
        
    except Exception as e:
        logger.error(f"Reporting node failed: {e}")
        new_state = dict(state)
        new_state['error_message'] = f"Reporting failed: {str(e)}"
        return new_state
    finally:
        db.close()

def should_continue_after_research(state: WorkflowState) -> str:
    """Conditional routing: continue or fail after research."""
    if state.get('status') == "FAILED":
        return "failed"
    research = state.get('research_result', {})
    if not research.get('prospects'):
        return "no_prospects"
    return "continue"

def should_continue_after_crm(state: WorkflowState) -> str:
    """Conditional routing after CRM save."""
    if state.get('status') == "FAILED":
        return "failed"
    crm = state.get('crm_result', {})
    if crm.get('draft_ids'):
        return "needs_approval"
    return "skip_approval"
