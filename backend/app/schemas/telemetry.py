from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.state import SecurityState, ConnectivityState, PowerState


class TelemetryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude: Optional[float] = None
    accuracy: Optional[float] = Field(None, ge=0.0)
    speed: Optional[float] = Field(None, ge=0.0)
    bearing: Optional[float] = Field(None, ge=0.0, le=360.0)
    provider: Optional[str] = Field("fused", description="gps, network, fused, cell, wifi_ssid")
    
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    power_state: Optional[PowerState] = None
    security_state: Optional[SecurityState] = None
    connectivity_state: Optional[ConnectivityState] = None
    network_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    recorded_at: datetime = Field(..., description="Timestamp recorded by device clock")


class TelemetryBatchIngestRequest(BaseModel):
    device_id: UUID
    items: List[Dict[str, Any]] = Field(..., min_length=1)
    nonce: str
    timestamp: datetime
    signature: str = Field(..., description="Signature over canonical items, device_id, timestamp, nonce")


class TelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    latitude: float
    longitude: float
    altitude: Optional[float]
    accuracy: Optional[float]
    speed: Optional[float]
    bearing: Optional[float]
    provider: Optional[str]
    battery_level: Optional[int]
    power_state: str
    security_state: str
    connectivity_state: str
    network_metadata: Dict[str, Any]
    recorded_at: datetime
    received_at: datetime


class TelemetryIngestResult(BaseModel):
    ingested_count: int
    latest_recorded_at: datetime
    server_time: datetime
