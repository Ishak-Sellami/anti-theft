import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.user import GUID


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    device_id = Column(GUID(), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(64), nullable=False, index=True)
    # POWER_OFF_ATTEMPT, SHUTDOWN_NOTIFIED, FACTORY_RESET_ATTEMPT, FAILED_AUTH,
    # SIM_SWAP, AIRPLANE_TOGGLE, STATE_TRANSITION, RECOVERY_TRIGGERED, EVIDENCE_CAPTURED, TAMPER_DETECTED

    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    security_state_before = Column(String(20), nullable=False)
    security_state_after = Column(String(20), nullable=False)

    payload = Column(JSON, default=dict, nullable=False)
    device_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    signature = Column(String(512), nullable=False)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    device = relationship("Device", back_populates="security_events")
    evidence = relationship("EvidenceMetadata", back_populates="security_event")


Index("idx_security_event_device_type", SecurityEvent.device_id, SecurityEvent.event_type)
