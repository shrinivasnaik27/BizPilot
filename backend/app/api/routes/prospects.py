"""Prospect CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from ...database import get_db
from ...api.dependencies import get_current_user
from ...schemas.prospect import ProspectCreate, ProspectUpdate, ProspectResponse
from ...models.prospect import Prospect
from ...models.lead_analysis import LeadAnalysis
from ...models.user import User

router = APIRouter(prefix="/api/prospects", tags=["Prospects"])


@router.get("", response_model=List[ProspectResponse])
async def list_prospects(
    search: Optional[str] = None,
    priority: Optional[str] = None,
    industry: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Prospect).filter(Prospect.user_id == current_user.id)
    if search:
        query = query.filter(Prospect.company_name.ilike(f"%{search}%"))
    if industry:
        query = query.filter(Prospect.industry.ilike(f"%{industry}%"))

    prospects = (
        query.order_by(Prospect.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for p in prospects:
        analysis = (
            db.query(LeadAnalysis).filter(LeadAnalysis.prospect_id == p.id).first()
        )
        resp = ProspectResponse.model_validate(p)
        if analysis:
            resp.lead_score = analysis.lead_score
            resp.priority = analysis.priority
        if priority and resp.priority != priority:
            continue
        result.append(resp)

    return result


@router.post("", response_model=ProspectResponse, status_code=201)
async def create_prospect(
    data: ProspectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(Prospect)
        .filter(
            Prospect.user_id == current_user.id,
            Prospect.company_name == data.company_name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Prospect with this company name already exists")
    p = Prospect(id=str(uuid.uuid4()), user_id=current_user.id, **data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(
    prospect_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = (
        db.query(Prospect)
        .filter(Prospect.id == prospect_id, Prospect.user_id == current_user.id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Prospect not found")
    analysis = db.query(LeadAnalysis).filter(LeadAnalysis.prospect_id == p.id).first()
    resp = ProspectResponse.model_validate(p)
    if analysis:
        resp.lead_score = analysis.lead_score
        resp.priority = analysis.priority
    return resp


@router.put("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: str,
    data: ProspectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = (
        db.query(Prospect)
        .filter(Prospect.id == prospect_id, Prospect.user_id == current_user.id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Prospect not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    p.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{prospect_id}")
async def delete_prospect(
    prospect_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = (
        db.query(Prospect)
        .filter(Prospect.id == prospect_id, Prospect.user_id == current_user.id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Prospect not found")
    db.delete(p)
    db.commit()
    return {"message": "Prospect deleted", "id": prospect_id}
