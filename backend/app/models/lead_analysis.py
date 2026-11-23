from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class LeadAnalysis(Base):
    __tablename__ = "lead_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prospect_id = Column(
        String(36),
        ForeignKey("prospects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 0-100
    lead_score = Column(Integer, nullable=False, default=0)
    # HIGH / MEDIUM / LOW
    priority = Column(String(20), nullable=False, default="LOW", index=True)
    reasoning = Column(Text, nullable=True)
    # JSON stored as text
    potential_needs = Column(Text, nullable=True)
    recommended_approach = Column(Text, nullable=True)
    # Sub-scores (each 0-100)
    industry_relevance_score = Column(Integer, nullable=True, default=0)
    business_need_score = Column(Integer, nullable=True, default=0)
    service_compatibility_score = Column(Integer, nullable=True, default=0)
    info_quality_score = Column(Integer, nullable=True, default=0)
    opportunity_score = Column(Integer, nullable=True, default=0)
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
    prospect = relationship("Prospect", back_populates="lead_analysis")
    workflow = relationship("Workflow", back_populates="lead_analyses")

    def __repr__(self) -> str:
        return (
            f"<LeadAnalysis id={self.id!r} prospect_id={self.prospect_id!r}"
            f" lead_score={self.lead_score} priority={self.priority!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prospect_id": self.prospect_id,
            "workflow_id": self.workflow_id,
            "lead_score": self.lead_score,
            "priority": self.priority,
            "reasoning": self.reasoning,
            "potential_needs": self.potential_needs,
            "recommended_approach": self.recommended_approach,
            "industry_relevance_score": self.industry_relevance_score,
            "business_need_score": self.business_need_score,
            "service_compatibility_score": self.service_compatibility_score,
            "info_quality_score": self.info_quality_score,
            "opportunity_score": self.opportunity_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
