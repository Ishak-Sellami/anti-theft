from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EvidenceMetadataCreateRequest(BaseModel):
    device_id: UUID
    event_id: Optional[UUID] = None
    capture_type: str = Field(..., description="SNAPSHOT, AMBIENT_RF, NETWORK_BEACONS, SENSOR_BURST")
    integrity_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash of captured evidence artifact")
    storage_ref: str = Field(..., description="Secure storage URI or path")
    mime_type: str = "application/octet-stream"
    file_size_bytes: Optional[str] = None
    chain_of_custody_notes: Optional[str] = None
    device_timestamp: datetime
    nonce: str
    signature: str


class EvidenceMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    event_id: Optional[UUID]
    capture_type: str
    integrity_hash: str
    storage_ref: str
    mime_type: str
    file_size_bytes: Optional[str]
    chain_of_custody_notes: Optional[str]
    device_timestamp: datetime
    received_at: datetime
