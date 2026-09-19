import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.user import GUID


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    device_id = Column(GUID(), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    issued_by = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)

    command_type = Column(String(64), nullable=False)
    # SET_SECURITY_STATE, UPDATE_POLICY, TRIGGER_ALARM, STOP_ALARM, REQUEST_SNAPSHOT, LOCK_DEVICE, AUTHORIZE_WIPE

    payload = Column(JSON, default=dict, nullable=False)
    nonce = Column(String(64), unique=True, index=True, nullable=False)

    status = Column(String(20), default="PENDING", nullable=False, index=True)
    # PENDING, DELIVERED, ACKNOWLEDGED, EXECUTED, FAILED, EXPIRED

    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    signature = Column(String(512), nullable=False)

    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    result_payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    device = relationship("Device", back_populates="commands")
    issuer = relationship("User", back_populates="commands_issued")


Index("idx_device_command_status", DeviceCommand.device_id, DeviceCommand.status)
