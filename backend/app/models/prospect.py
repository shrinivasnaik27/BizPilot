from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class Prospect(Base):
    __tablename__ = "prospects"
    __table_args__ = (
        UniqueConstraint("user_id", "company_name", name="uq_prospect_user_company"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    company_name = Column(String(500), nullable=False, index=True)
    website = Column(String(500), nullable=True)
    industry = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(100), nullable=True)
    # JSON stored as text (list of URLs)
    source_urls = Column(Text, nullable=True)
    research_confidence = Column(Float, nullable=True, default=0.0)
    # e.g. PENDING / IN_PROGRESS / COMPLETE / FAILED
    research_status = Column(String(50), nullable=True, default="PENDING")
    is_demo = Column(Boolean, default=False, nullable=False)
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
    user = relationship("User", back_populates="prospects")
    workflow = relationship("Workflow", back_populates="prospects")
    lead_analysis = relationship(
        "LeadAnalysis",
        back_populates="prospect",
        uselist=False,
        cascade="all, delete-orphan",
    )
    marketing_drafts = relationship(
        "MarketingDraft", back_populates="prospect", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Prospect id={self.id!r} company_name={self.company_name!r}"
            f" research_status={self.research_status!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "workflow_id": self.workflow_id,
            "company_name": self.company_name,
            "website": self.website,
            "industry": self.industry,
            "description": self.description,
            "location": self.location,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "source_urls": self.source_urls,
            "research_confidence": self.research_confidence,
            "research_status": self.research_status,
            "is_demo": self.is_demo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
