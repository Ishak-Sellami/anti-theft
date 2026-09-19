import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.user import GUID


class LocationTelemetry(Base):
    __tablename__ = "location_telemetry"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    device_id = Column(GUID(), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    bearing = Column(Float, nullable=True)
    provider = Column(String(50), nullable=True)  # gps, network, fused, cell, wifi_ssid

    battery_level = Column(Integer, nullable=True)
    power_state = Column(String(20), nullable=False)
    security_state = Column(String(20), nullable=False)
    connectivity_state = Column(String(20), nullable=False)

    network_metadata = Column(JSON, default=dict, nullable=False)

    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    device = relationship("Device", back_populates="telemetry")


Index("idx_location_device_recorded", LocationTelemetry.device_id, LocationTelemetry.recorded_at.desc())
