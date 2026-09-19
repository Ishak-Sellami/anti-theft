import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.user import GUID


class EvidenceMetadata(Base):
    __tablename__ = "evidence_metadata"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    device_id = Column(GUID(), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(GUID(), ForeignKey("security_events.id", ondelete="SET NULL"), nullable=True, index=True)

    capture_type = Column(String(50), nullable=False)  # SNAPSHOT, AMBIENT_RF, NETWORK_BEACONS, SENSOR_BURST
    integrity_hash = Column(String(64), nullable=False)  # SHA-256 hash of the evidence payload/file
    storage_ref = Column(String(512), nullable=False)  # S3 URI / secure filesystem path / object key
    mime_type = Column(String(100), default="application/octet-stream", nullable=False)
    file_size_bytes = Column(String(50), nullable=True)

    chain_of_custody_notes = Column(Text, nullable=True)
    device_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    device = relationship("Device", back_populates="evidence")
    security_event = relationship("SecurityEvent", back_populates="evidence")


Index("idx_evidence_device_time", EvidenceMetadata.device_id, EvidenceMetadata.device_timestamp.desc())
