"""Reporting Agent: Generates comprehensive business intelligence reports."""
import json, uuid, csv, io
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.report import Report
from ..models.prospect import Prospect
from ..models.lead_analysis import LeadAnalysis
from ..models.marketing_draft import MarketingDraft
from ..models.approval import Approval
from ..models.workflow import Workflow
from ..models.execution_log import ExecutionLog
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ReportData:
    def __init__(self):
        self.total_prospects = 0
        self.qualified_prospects = 0
        self.high_priority = 0
        self.medium_priority = 0
        self.low_priority = 0
        self.drafts_generated = 0
        self.crm_saved = 0
        self.pending_approvals = 0
        self.approved_actions = 0
        self.executed_actions = 0
        self.failed_actions = 0
        self.recommendations = []
        self.top_prospects = []
        self.workflow_summary = {}

class ReportingAgent:
    def __init__(self):
        self.agent_name = "Reporting Agent"
    
    def generate_report(self, db: Session, workflow_id: str, user_id: str) -> str:
        """Generate a comprehensive workflow report. Returns report ID."""
        logger.info(f"Reporting Agent: Generating report for workflow {workflow_id}")
        
        # Collect data
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        prospects = db.query(Prospect).filter(Prospect.workflow_id == workflow_id).all()
        analyses = db.query(LeadAnalysis).filter(LeadAnalysis.workflow_id == workflow_id).all()
        drafts = db.query(MarketingDraft).filter(MarketingDraft.workflow_id == workflow_id).all()
        approvals = db.query(Approval).filter(Approval.workflow_id == workflow_id).all()
        logs = db.query(ExecutionLog).filter(ExecutionLog.workflow_id == workflow_id).all()
        
        data = ReportData()
        data.total_prospects = len(prospects)
        data.crm_saved = len(prospects)
        data.drafts_generated = len(drafts)
        
        # Analysis stats
        for a in analyses:
            if a.priority == "HIGH":
                data.high_priority += 1
                data.qualified_prospects += 1
            elif a.priority == "MEDIUM":
                data.medium_priority += 1
                data.qualified_prospects += 1
            else:
                data.low_priority += 1
        
        # Approval stats
        for approval in approvals:
            if approval.status == "PENDING":
                data.pending_approvals += 1
            elif approval.status == "APPROVED":
                data.approved_actions += 1
            elif approval.status == "EXECUTED":
                data.executed_actions += 1
            elif approval.status == "FAILED":
                data.failed_actions += 1
        
        # Top prospects
        analysis_map = {a.prospect_id: a for a in analyses}
        for p in prospects[:5]:
            analysis = analysis_map.get(p.id)
            data.top_prospects.append({
                "company": p.company_name,
                "industry": p.industry,
                "score": analysis.lead_score if analysis else 0,
                "priority": analysis.priority if analysis else "UNKNOWN"
            })
        
        # Sort top prospects by score
        data.top_prospects.sort(key=lambda x: x["score"], reverse=True)
        
        # Generate recommendations
        if data.high_priority > 0:
            data.recommendations.append(f"Focus immediate outreach on {data.high_priority} HIGH priority prospect(s)")
        if data.pending_approvals > 0:
            data.recommendations.append(f"Review and approve {data.pending_approvals} pending email draft(s) in Approval Center")
        if data.total_prospects < 5:
            data.recommendations.append("Consider running additional research to find more prospects")
        if data.medium_priority > 0:
            data.recommendations.append(f"Nurture {data.medium_priority} MEDIUM priority prospect(s) with follow-up content")
        
        # Build full report data
        report_data = {
            "workflow_id": workflow_id,
            "instruction": workflow.instruction if workflow else "Unknown",
            "workflow_title": workflow.title if workflow else "Unknown",
            "stats": {
                "total_prospects": data.total_prospects,
                "qualified_prospects": data.qualified_prospects,
                "high_priority": data.high_priority,
                "medium_priority": data.medium_priority,
                "low_priority": data.low_priority,
                "drafts_generated": data.drafts_generated,
                "crm_saved": data.crm_saved,
                "pending_approvals": data.pending_approvals,
                "approved_actions": data.approved_actions,
                "executed_actions": data.executed_actions,
                "failed_actions": data.failed_actions,
            },
            "top_prospects": data.top_prospects,
            "recommendations": data.recommendations,
            "execution_logs": [{"agent": l.agent_name, "action": l.action, "status": l.status} for l in logs],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Save report to DB
        report = Report(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            user_id=user_id,
            report_type="WORKFLOW_SUMMARY",
            title=f"Workflow Report - {workflow.title if workflow else 'Unknown'}",
            summary=f"Researched {data.total_prospects} prospects, found {data.high_priority} high-priority leads, generated {data.drafts_generated} email drafts.",
            total_prospects=data.total_prospects,
            qualified_prospects=data.qualified_prospects,
            high_priority=data.high_priority,
            medium_priority=data.medium_priority,
            low_priority=data.low_priority,
            drafts_generated=data.drafts_generated,
            crm_saved=data.crm_saved,
            pending_approvals=data.pending_approvals,
            approved_actions=data.approved_actions,
            executed_actions=data.executed_actions,
            failed_actions=data.failed_actions,
            recommendations=json.dumps(data.recommendations),
            report_data=json.dumps(report_data),
        )
        db.add(report)
        db.commit()
        
        logger.info(f"Reporting Agent: Report generated {report.id}")
        return report.id
    
    def export_csv(self, db: Session, report_id: str) -> str:
        """Export report data as CSV string."""
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            raise ValueError("Report not found")
        
        report_data = json.loads(report.report_data) if report.report_data else {}
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["BizPilot AI - Workflow Report"])
        writer.writerow(["Generated At", report.created_at.isoformat()])
        writer.writerow([])
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Prospects", report.total_prospects])
        writer.writerow(["Qualified Prospects", report.qualified_prospects])
        writer.writerow(["High Priority", report.high_priority])
        writer.writerow(["Medium Priority", report.medium_priority])
        writer.writerow(["Low Priority", report.low_priority])
        writer.writerow(["Drafts Generated", report.drafts_generated])
        writer.writerow(["CRM Records", report.crm_saved])
        writer.writerow([])
        writer.writerow(["Top Prospects"])
        writer.writerow(["Company", "Industry", "Score", "Priority"])
        for p in report_data.get("top_prospects", []):
            writer.writerow([p["company"], p["industry"], p["score"], p["priority"]])
        writer.writerow([])
        writer.writerow(["Recommendations"])
        for r in report_data.get("recommendations", []):
            writer.writerow([r])
        
        return output.getvalue()

reporting_agent = ReportingAgent()
