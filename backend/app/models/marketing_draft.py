from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class MarketingDraft(Base):
    __tablename__ = "marketing_drafts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(
        String(36),
        ForeignKey("prospects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
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
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    marketing_angle = Column(String(255), nullable=True)
    personalization_notes = Column(Text, nullable=True)
    recipient_email = Column(String(255), nullable=True)
    # DRAFT / APPROVED / REJECTED / SENT / FAILED
    status = Column(String(50), nullable=False, default="DRAFT", index=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
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
    prospect = relationship("Prospect", back_populates="marketing_drafts")
    workflow = relationship("Workflow", back_populates="marketing_drafts")
    user = relationship("User", back_populates="marketing_drafts")
    approval = relationship(
        "Approval",
        back_populates="marketing_draft",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<MarketingDraft id={self.id!r} subject={self.subject!r}"
            f" status={self.status!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "workflow_id": self.workflow_id,
            "user_id": self.user_id,
            "subject": self.subject,
            "body": self.body,
            "marketing_angle": self.marketing_angle,
            "personalization_notes": self.personalization_notes,
            "recipient_email": self.recipient_email,
            "status": self.status,
            "is_edited": self.is_edited,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
