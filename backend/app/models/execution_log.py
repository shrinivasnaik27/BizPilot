from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from ..database import Base


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name = Column(String(255), nullable=False, index=True)
    action = Column(String(500), nullable=False)
    # SUCCESS / FAILED / SKIPPED
    status = Column(String(50), nullable=False, default="SUCCESS", index=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    workflow = relationship("Workflow", back_populates="execution_logs")

    def __repr__(self) -> str:
        return (
            f"<ExecutionLog id={self.id!r} agent_name={self.agent_name!r}"
            f" action={self.action!r} status={self.status!r}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "status": self.status,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
