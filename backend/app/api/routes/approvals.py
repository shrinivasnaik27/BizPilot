"""Approval routes with backend enforcement."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ...database import get_db
from ...api.dependencies import get_current_user
from ...schemas.approval import ApprovalResponse, ApproveRequest, RejectRequest
from ...models.approval import Approval
from ...models.marketing_draft import MarketingDraft
from ...models.user import User
from ...agents.approval_agent import approval_agent
from ...services.email_service import email_service

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])


@router.get("", response_model=List[ApprovalResponse])
async def list_approvals(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Approval).filter(Approval.user_id == current_user.id)
    if status:
        query = query.filter(Approval.status == status)
    approvals = query.order_by(Approval.created_at.desc()).all()

    result = []
    for a in approvals:
        resp = ApprovalResponse.model_validate(a)
        if a.draft_id:
            draft = db.query(MarketingDraft).filter(MarketingDraft.id == a.draft_id).first()
            if draft:
                resp.draft_id = draft.id
                resp.draft_subject = draft.subject
                resp.draft_body = draft.body
        result.append(resp)
    return result


@router.post("/{approval_id}/approve")
async def approve_action(
    approval_id: str,
    request: ApproveRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approval = (
        db.query(Approval)
        .filter(Approval.id == approval_id, Approval.user_id == current_user.id)
        .first()
    )
    if not approval:
        raise HTTPException(404, "Approval not found")

    edited_content = None
    if request and (request.edited_subject or request.edited_body):
        edited_content = {}
        if request.edited_subject:
            edited_content["subject"] = request.edited_subject
        if request.edited_body:
            edited_content["body"] = request.edited_body

    try:
        approval_agent.approve_action(db, approval_id, current_user.email, edited_content)
        return {"message": "Action approved", "approval_id": approval_id}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{approval_id}/reject")
async def reject_action(
    approval_id: str,
    request: RejectRequest = RejectRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    approval = (
        db.query(Approval)
        .filter(Approval.id == approval_id, Approval.user_id == current_user.id)
        .first()
    )
    if not approval:
        raise HTTPException(404, "Approval not found")
    try:
        approval_agent.reject_action(db, approval_id, current_user.email, request.reason or "")
        return {"message": "Action rejected", "approval_id": approval_id}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{approval_id}/send")
async def send_approved_email(
    approval_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send an approved email – backend re-verifies approval before sending."""
    approval = (
        db.query(Approval)
        .filter(Approval.id == approval_id, Approval.user_id == current_user.id)
        .first()
    )
    if not approval or not approval.draft_id:
        raise HTTPException(404, "Approval or linked draft not found")
    try:
        result = await email_service.send_approved_email(db, approval.draft_id, current_user.email)
        return result
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Email send failed: {str(e)}")
