from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_type = Column(String(100), nullable=False, default="WORKFLOW_SUMMARY")
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)

    # Aggregate counts
    total_prospects = Column(Integer, nullable=False, default=0)
    qualified_prospects = Column(Integer, nullable=False, default=0)
    high_priority = Column(Integer, nullable=False, default=0)
    medium_priority = Column(Integer, nullable=False, default=0)
    low_priority = Column(Integer, nullable=False, default=0)
    drafts_generated = Column(Integer, nullable=False, default=0)
    crm_saved = Column(Integer, nullable=False, default=0)
    pending_approvals = Column(Integer, nullable=False, default=0)
    approved_actions = Column(Integer, nullable=False, default=0)
    executed_actions = Column(Integer, nullable=False, default=0)
    failed_actions = Column(Integer, nullable=False, default=0)

    # JSON stored as text
    recommendations = Column(Text, nullable=True)
    report_data = Column(Text, nullable=True)

    # File export paths
    pdf_path = Column(String(1000), nullable=True)
    csv_path = Column(String(1000), nullable=True)

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
    workflow = relationship("Workflow", back_populates="reports")
    user = relationship("User", back_populates="reports")

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id!r} title={self.title!r}"
            f" workflow_id={self.workflow_id!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "report_type": self.report_type,
            "title": self.title,
            "summary": self.summary,
            "total_prospects": self.total_prospects,
            "qualified_prospects": self.qualified_prospects,
            "high_priority": self.high_priority,
            "medium_priority": self.medium_priority,
            "low_priority": self.low_priority,
            "drafts_generated": self.drafts_generated,
            "crm_saved": self.crm_saved,
            "pending_approvals": self.pending_approvals,
            "approved_actions": self.approved_actions,
            "executed_actions": self.executed_actions,
            "failed_actions": self.failed_actions,
            "recommendations": self.recommendations,
            "report_data": self.report_data,
            "pdf_path": self.pdf_path,
            "csv_path": self.csv_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
