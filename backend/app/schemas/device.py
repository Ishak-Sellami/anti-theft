from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.state import SecurityState, ConnectivityState, PowerState


class DeviceEnrollInitiateRequest(BaseModel):
    device_name: str = Field(..., max_length=100)
    device_model: Optional[str] = Field(None, max_length=100)
    os_version: Optional[str] = Field(None, max_length=50)


class DeviceEnrollInitiateResponse(BaseModel):
    enrollment_token: str
    nonce: str
    backend_public_key_pem: str
    expires_at: datetime


class DeviceEnrollCompleteRequest(BaseModel):
    enrollment_token: str
    public_key_pem: str = Field(..., description="Device generated PEM public key (ECDSA or Ed25519)")
    device_name: str
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    agent_version: Optional[str] = None
    nonce: str
    timestamp: datetime
    signature: str = Field(..., description="Signature over canonical payload proving possession of private key")


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    device_name: str
    device_model: Optional[str]
    os_version: Optional[str]
    agent_version: Optional[str]
    
    # 3D States
    security_state: SecurityState
    connectivity_state: ConnectivityState
    power_state: PowerState
    
    public_key_fingerprint: str
    enrollment_status: str
    active_policy_id: str
    
    battery_level: Optional[int]
    is_charging: bool
    last_heartbeat_at: Optional[datetime]
    last_known_lat: Optional[float]
    last_known_lng: Optional[float]
    last_known_accuracy: Optional[float]
    
    created_at: datetime
    updated_at: datetime


class DeviceUpdateSecurityStateRequest(BaseModel):
    target_security_state: SecurityState
    reason: Optional[str] = None


class DeviceHeartbeatRequest(BaseModel):
    device_id: UUID
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    is_charging: bool = False
    connectivity_state: ConnectivityState = ConnectivityState.ONLINE
    nonce: str
    timestamp: datetime
    signature: str
