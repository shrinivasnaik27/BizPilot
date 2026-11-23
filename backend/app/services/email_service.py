"""Email service with mandatory approval verification."""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from ..models.approval import Approval
from ..models.marketing_draft import MarketingDraft
from ..agents.approval_agent import approval_agent
from ..config import get_settings
from ..utils.logger import get_logger
from datetime import datetime, timezone

logger = get_logger(__name__)


class EmailService:
    def __init__(self):
        self.settings = get_settings()

    async def send_approved_email(self, db: Session, draft_id: str, sent_by: str) -> dict:
        """Send an email – ONLY after backend approval verification."""
        # MANDATORY backend approval check (independent of UI)
        is_approved, reason = approval_agent.verify_approval_before_send(db, draft_id)
        if not is_approved:
            logger.warning(f"Email send BLOCKED – not approved: {reason}")
            raise PermissionError(f"Email not approved: {reason}")

        draft = db.query(MarketingDraft).filter(MarketingDraft.id == draft_id).first()
        if not draft:
            raise ValueError("Draft not found")

        if not draft.recipient_email or draft.recipient_email == "unknown":
            raise ValueError("No recipient email address available")

        if self.settings.demo_mode:
            logger.info("[DEMO MODE] Email send simulated – not actually sent")
            draft.status = "SENT"
            draft.sent_at = datetime.now(timezone.utc)
            approval = db.query(Approval).filter(
                Approval.draft_id == draft_id, Approval.status == "APPROVED"
            ).first()
            if approval:
                approval.status = "EXECUTED"
                approval.executed_at = datetime.now(timezone.utc)
                approval.execution_result = "[DEMO] Email simulated – not actually sent"
            db.commit()
            return {
                "success": True,
                "message": "[DEMO MODE] Email simulated. Configure SMTP for real sending.",
                "demo": True,
            }

        # Real email sending
        if not self.settings.smtp_host:
            raise ValueError("SMTP not configured. Set SMTP_HOST in .env")

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = draft.subject
            msg["From"] = self.settings.smtp_from_email
            msg["To"] = draft.recipient_email
            msg.attach(MIMEText(draft.body, "plain"))

            async with aiosmtplib.SMTP(
                hostname=self.settings.smtp_host, port=self.settings.smtp_port, use_tls=False
            ) as smtp:
                if self.settings.smtp_use_tls:
                    await smtp.starttls()
                if self.settings.smtp_username:
                    await smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                await smtp.send_message(msg)

            draft.status = "SENT"
            draft.sent_at = datetime.now(timezone.utc)
            approval = db.query(Approval).filter(
                Approval.draft_id == draft_id, Approval.status == "APPROVED"
            ).first()
            if approval:
                approval.status = "EXECUTED"
                approval.executed_at = datetime.now(timezone.utc)
                approval.execution_result = "Email sent successfully"
            db.commit()
            return {"success": True, "message": f"Email sent to {draft.recipient_email}"}

        except Exception as e:
            logger.error(f"Email send failed: {e}")
            draft.status = "FAILED"
            approval = db.query(Approval).filter(
                Approval.draft_id == draft_id, Approval.status == "APPROVED"
            ).first()
            if approval:
                approval.status = "FAILED"
                approval.execution_result = str(e)
            db.commit()
            raise


email_service = EmailService()
