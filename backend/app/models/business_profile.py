from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    business_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Stored as JSON string
    services = Column(Text, nullable=True)
    target_industries = Column(Text, nullable=True)
    target_locations = Column(Text, nullable=True)
    ideal_customer = Column(Text, nullable=True)
    tone = Column(String(100), nullable=True, default="professional")
    website = Column(String(500), nullable=True)
    business_email = Column(String(255), nullable=True)
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
    user = relationship("User", back_populates="business_profile")

    def __repr__(self) -> str:
        return (
            f"<BusinessProfile id={self.id!r} business_name={self.business_name!r}"
            f" user_id={self.user_id!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "business_name": self.business_name,
            "description": self.description,
            "services": self.services,
            "target_industries": self.target_industries,
            "target_locations": self.target_locations,
            "ideal_customer": self.ideal_customer,
            "tone": self.tone,
            "website": self.website,
            "business_email": self.business_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
