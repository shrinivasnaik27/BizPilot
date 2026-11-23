from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    draft_id = Column(
        String(36),
        ForeignKey("marketing_drafts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # SEND_EMAIL / CRM_UPDATE / EXTERNAL_ACTION
    action_type = Column(String(100), nullable=False)
    action_description = Column(Text, nullable=False)
    target_company = Column(String(500), nullable=False)
    target_email = Column(String(255), nullable=True)
    # SHA256 of the content requiring approval
    content_hash = Column(String(64), nullable=False)
    # PENDING / APPROVED / REJECTED / EXECUTED / FAILED
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    execution_result = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="approvals")
    user = relationship("User", back_populates="approvals")
    marketing_draft = relationship("MarketingDraft", back_populates="approval")

    def __repr__(self) -> str:
        return (
            f"<Approval id={self.id!r} action_type={self.action_type!r}"
            f" status={self.status!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "draft_id": self.draft_id,
            "action_type": self.action_type,
            "action_description": self.action_description,
            "target_company": self.target_company,
            "target_email": self.target_email,
            "content_hash": self.content_hash,
            "status": self.status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "execution_result": self.execution_result,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
