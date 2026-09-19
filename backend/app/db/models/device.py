import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.user import GUID


class Device(Base):
    __tablename__ = "devices"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    owner_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(100), nullable=False)
    device_model = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    agent_version = Column(String(50), nullable=True)

    # Multi-dimensional independent state dimensions
    security_state = Column(String(20), default="NORMAL", nullable=False, index=True)      # NORMAL, PROTECTED, STOLEN, RECOVERY
    connectivity_state = Column(String(20), default="OFFLINE", nullable=False, index=True) # ONLINE, DEGRADED, OFFLINE
    power_state = Column(String(20), default="NORMAL", nullable=False)                     # NORMAL, LOW, CRITICAL

    # Cryptographic public key
    public_key_pem = Column(Text, nullable=False)
    public_key_fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    enrollment_status = Column(String(20), default="PENDING", nullable=False)              # PENDING, ACTIVE, REVOKED

    # Active Recovery Policy
    active_policy_id = Column(String(64), default="pol_default_v1", nullable=False)

    # Health & Telemetry Caches
    battery_level = Column(Integer, nullable=True)
    is_charging = Column(Boolean, default=False, nullable=False)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_known_lat = Column(Float, nullable=True)
    last_known_lng = Column(Float, nullable=True)
    last_known_accuracy = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="devices")
    telemetry = relationship("LocationTelemetry", back_populates="device", cascade="all, delete-orphan")
    security_events = relationship("SecurityEvent", back_populates="device", cascade="all, delete-orphan")
    commands = relationship("DeviceCommand", back_populates="device", cascade="all, delete-orphan")
    evidence = relationship("EvidenceMetadata", back_populates="device", cascade="all, delete-orphan")


Index("idx_device_owner_state", Device.owner_id, Device.security_state)
