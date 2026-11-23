from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(500), nullable=False)
    instruction = Column(Text, nullable=False)
    # PENDING / RUNNING / PAUSED / COMPLETED / FAILED / CANCELLED
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    current_step = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    # JSON stored as text
    metadata_ = Column("metadata", Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
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
    user = relationship("User", back_populates="workflows")
    prospects = relationship(
        "Prospect", back_populates="workflow", cascade="all, delete-orphan"
    )
    marketing_drafts = relationship(
        "MarketingDraft", back_populates="workflow", cascade="all, delete-orphan"
    )
    approvals = relationship(
        "Approval", back_populates="workflow", cascade="all, delete-orphan"
    )
    reports = relationship(
        "Report", back_populates="workflow", cascade="all, delete-orphan"
    )
    execution_logs = relationship(
        "ExecutionLog", back_populates="workflow", cascade="all, delete-orphan"
    )
    lead_analyses = relationship(
        "LeadAnalysis", back_populates="workflow", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Workflow id={self.id!r} title={self.title!r} status={self.status!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "instruction": self.instruction,
            "status": self.status,
            "current_step": self.current_step,
            "error_message": self.error_message,
            "metadata": self.metadata_,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
