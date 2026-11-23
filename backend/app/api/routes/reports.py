"""Report routes."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import json
from ...database import get_db
from ...api.dependencies import get_current_user
from ...models.report import Report
from ...models.user import User
from ...agents.reporting_agent import reporting_agent

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("")
async def list_reports(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "workflow_id": r.workflow_id,
            "title": r.title,
            "summary": r.summary,
            "total_prospects": r.total_prospects,
            "qualified_prospects": r.qualified_prospects,
            "high_priority": r.high_priority,
            "medium_priority": r.medium_priority,
            "low_priority": r.low_priority,
            "drafts_generated": r.drafts_generated,
            "created_at": r.created_at,
        }
        for r in reports
    ]


@router.get("/{report_id}")
async def get_report(
    report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    r = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Report not found")
    data = json.loads(r.report_data) if r.report_data else {}
    return {
        "id": r.id,
        "workflow_id": r.workflow_id,
        "title": r.title,
        "summary": r.summary,
        "stats": data.get("stats", {}),
        "top_prospects": data.get("top_prospects", []),
        "recommendations": data.get("recommendations", []),
        "execution_logs": data.get("execution_logs", []),
        "created_at": r.created_at,
    }


@router.get("/{report_id}/export/csv")
async def export_csv(
    report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    r = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not r:
        raise HTTPException(404, "Report not found")
    csv_content = reporting_agent.export_csv(db, report_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=bizpilot_report_{report_id[:8]}.csv"
        },
    )
