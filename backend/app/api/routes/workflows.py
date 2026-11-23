"""Workflow API routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid, json
from datetime import datetime, timezone
from ...database import get_db
from ...api.dependencies import get_current_user
from ...schemas.workflow import WorkflowCreate, WorkflowResponse
from ...models.workflow import Workflow
from ...models.user import User
from ...graph.workflow import orchestrator
from ...utils.logger import get_logger

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])
logger = get_logger(__name__)


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workflow_id = str(uuid.uuid4())
    title = data.title or f"Workflow: {data.instruction[:60]}..."

    workflow = Workflow(
        id=workflow_id,
        user_id=current_user.id,
        title=title,
        instruction=data.instruction,
        status="PENDING",
        current_step="PENDING",
        metadata_=json.dumps(
            {"target_count": data.target_count, "min_lead_score": data.min_lead_score}
        ),
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Launch in background so the API returns immediately
    background_tasks.add_task(
        _run_workflow_background,
        workflow_id=workflow_id,
        user_id=current_user.id,
        instruction=data.instruction,
        target_count=data.target_count,
        min_lead_score=data.min_lead_score,
    )
    return workflow


async def _run_workflow_background(
    workflow_id: str, user_id: str, instruction: str, target_count: int, min_lead_score: int
):
    from ...database import SessionLocal

    db = SessionLocal()
    try:
        await orchestrator.start_workflow(
            db, workflow_id, user_id, instruction, target_count, min_lead_score
        )
    except Exception as e:
        logger.error(f"Background workflow {workflow_id} failed: {e}")
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if wf:
            wf.status = "FAILED"
            wf.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(Workflow)
        .filter(Workflow.user_id == current_user.id)
        .order_by(Workflow.created_at.desc())
        .all()
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wf = (
        db.query(Workflow)
        .filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id)
        .first()
    )
    if not wf:
        raise HTTPException(404, "Workflow not found")
    return wf


@router.post("/{workflow_id}/resume")
async def resume_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wf = (
        db.query(Workflow)
        .filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id)
        .first()
    )
    if not wf:
        raise HTTPException(404, "Workflow not found")
    if wf.status not in ("PAUSED", "AWAITING_APPROVAL"):
        raise HTTPException(400, f"Cannot resume from status: {wf.status}")

    background_tasks.add_task(
        _resume_workflow_background, workflow_id=workflow_id, user_id=current_user.id
    )
    return {"message": "Workflow resuming for final report", "workflow_id": workflow_id}


async def _resume_workflow_background(workflow_id: str, user_id: str):
    from ...database import SessionLocal

    db = SessionLocal()
    try:
        await orchestrator.resume_workflow(db, workflow_id, user_id)
    except Exception as e:
        logger.error(f"Resume workflow {workflow_id} failed: {e}")
    finally:
        db.close()


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wf = (
        db.query(Workflow)
        .filter(Workflow.id == workflow_id, Workflow.user_id == current_user.id)
        .first()
    )
    if not wf:
        raise HTTPException(404, "Workflow not found")
    wf.status = "CANCELLED"
    wf.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Workflow cancelled", "workflow_id": workflow_id}
