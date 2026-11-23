"""Approval Agent: Creates and manages human-in-the-loop approval requests."""
import uuid, hashlib, json
from typing import List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..models.approval import Approval
from ..models.marketing_draft import MarketingDraft
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ApprovalAgent:
    def __init__(self):
        self.agent_name = "Approval Agent"
    
    def create_email_approvals(self, db: Session, draft_ids: List[str], workflow_id: str, user_id: str) -> List[str]:
        """Create approval requests for each email draft."""
        approval_ids = []
        
        for draft_id in draft_ids:
            draft = db.query(MarketingDraft).filter(MarketingDraft.id == draft_id).first()
            if not draft:
                continue
            
            # Check if approval already exists for this draft
            existing = db.query(Approval).filter(
                Approval.draft_id == draft_id,
                Approval.status.in_(["PENDING", "APPROVED"])
            ).first()
            
            if existing:
                logger.info(f"Approval already exists for draft {draft_id}")
                approval_ids.append(existing.id)
                continue
            
            # Create content hash to prevent duplicate execution
            content_hash = hashlib.sha256(
                f"{draft.subject}{draft.body}{draft.recipient_email}".encode()
            ).hexdigest()
            
            approval = Approval(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                user_id=user_id,
                draft_id=draft_id,
                action_type="SEND_EMAIL",
                action_description=f"Send marketing email to {draft.recipient_email or 'unknown'} at {draft.prospect_id}",
                target_company=draft.prospect_id,  # Will be resolved later
                target_email=draft.recipient_email,
                content_hash=content_hash,
                status="PENDING",
            )
            db.add(approval)
            db.flush()
            approval_ids.append(approval.id)
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Approval creation failed: {e}")
            raise
        
        logger.info(f"Approval Agent: Created {len(approval_ids)} approval requests")
        return approval_ids
    
    def approve_action(self, db: Session, approval_id: str, approved_by: str, edited_content: dict = None) -> bool:
        """Approve an action. Returns True if successful."""
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != "PENDING":
            raise ValueError(f"Approval {approval_id} is not pending (status: {approval.status})")
        
        # If content was edited, require re-hash check
        if edited_content and approval.draft_id:
            draft = db.query(MarketingDraft).filter(MarketingDraft.id == approval.draft_id).first()
            if draft:
                if "subject" in edited_content:
                    draft.subject = edited_content["subject"]
                if "body" in edited_content:
                    draft.body = edited_content["body"]
                draft.is_edited = True
                draft.updated_at = datetime.now(timezone.utc)
                
                # Update content hash for edited content
                new_hash = hashlib.sha256(
                    f"{draft.subject}{draft.body}{draft.recipient_email}".encode()
                ).hexdigest()
                approval.content_hash = new_hash
        
        approval.status = "APPROVED"
        approval.approved_by = approved_by
        approval.approved_at = datetime.now(timezone.utc)
        
        db.commit()
        logger.info(f"Approval Agent: Approved action {approval_id} by {approved_by}")
        return True
    
    def reject_action(self, db: Session, approval_id: str, rejected_by: str, reason: str = "") -> bool:
        """Reject an action."""
        approval = db.query(Approval).filter(Approval.id == approval_id).first()
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        if approval.status != "PENDING":
            raise ValueError(f"Approval {approval_id} is not pending")
        
        approval.status = "REJECTED"
        approval.approved_by = rejected_by
        approval.approved_at = datetime.now(timezone.utc)
        approval.rejection_reason = reason
        
        # Update draft status too
        if approval.draft_id:
            draft = db.query(MarketingDraft).filter(MarketingDraft.id == approval.draft_id).first()
            if draft:
                draft.status = "REJECTED"
        
        db.commit()
        logger.info(f"Approval Agent: Rejected action {approval_id}")
        return True
    
    def verify_approval_before_send(self, db: Session, draft_id: str) -> tuple[bool, str]:
        """Backend verification: check approval before sending email. Returns (is_approved, reason)."""
        approval = db.query(Approval).filter(
            Approval.draft_id == draft_id,
            Approval.status == "APPROVED"
        ).first()
        
        if not approval:
            return False, "No approved action found for this draft"
        
        # Verify content hash hasn't changed
        draft = db.query(MarketingDraft).filter(MarketingDraft.id == draft_id).first()
        if not draft:
            return False, "Draft not found"
        
        current_hash = hashlib.sha256(
            f"{draft.subject}{draft.body}{draft.recipient_email}".encode()
        ).hexdigest()
        
        if current_hash != approval.content_hash:
            # Content changed after approval - block send
            approval.status = "PENDING"  # Reset to pending
            db.commit()
            return False, "Email content changed after approval. Re-approval required."
        
        return True, "Approved"

approval_agent = ApprovalAgent()
