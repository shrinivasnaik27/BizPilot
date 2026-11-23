"""Marketing draft routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from ...database import get_db
from ...api.dependencies import get_current_user
from ...models.marketing_draft import MarketingDraft
from ...models.user import User

router = APIRouter(prefix="/api/marketing", tags=["Marketing"])


@router.get("/drafts")
async def list_drafts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    drafts = (
        db.query(MarketingDraft)
        .filter(MarketingDraft.user_id == current_user.id)
        .order_by(MarketingDraft.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "subject": d.subject,
            "recipient_email": d.recipient_email,
            "status": d.status,
            "is_edited": d.is_edited,
            "created_at": d.created_at,
            "prospect_id": d.prospect_id,
            "marketing_angle": d.marketing_angle,
        }
        for d in drafts
    ]


@router.get("/drafts/{draft_id}")
async def get_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = (
        db.query(MarketingDraft)
        .filter(MarketingDraft.id == draft_id, MarketingDraft.user_id == current_user.id)
        .first()
    )
    if not d:
        raise HTTPException(404, "Draft not found")
    return {
        "id": d.id,
        "subject": d.subject,
        "body": d.body,
        "marketing_angle": d.marketing_angle,
        "personalization_notes": d.personalization_notes,
        "recipient_email": d.recipient_email,
        "status": d.status,
        "is_edited": d.is_edited,
        "prospect_id": d.prospect_id,
        "created_at": d.created_at,
    }


@router.put("/drafts/{draft_id}")
async def update_draft(
    draft_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    d = (
        db.query(MarketingDraft)
        .filter(MarketingDraft.id == draft_id, MarketingDraft.user_id == current_user.id)
        .first()
    )
    if not d:
        raise HTTPException(404, "Draft not found")
    if "subject" in data:
        d.subject = data["subject"]
    if "body" in data:
        d.body = data["body"]
    d.is_edited = True
    d.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Draft updated. Re-approval required if previously approved.", "id": draft_id}
