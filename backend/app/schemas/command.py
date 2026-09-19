from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CommandCreateRequest(BaseModel):
    device_id: UUID
    command_type: str = Field(..., description="SET_SECURITY_STATE, UPDATE_POLICY, TRIGGER_ALARM, STOP_ALARM, REQUEST_SNAPSHOT, LOCK_DEVICE, AUTHORIZE_WIPE")
    payload: Dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int = Field(300, ge=30, le=86400, description="Command time-to-live in seconds")


class CommandAckRequest(BaseModel):
    command_id: UUID
    device_id: UUID
    status: str = Field(..., description="ACKNOWLEDGED, EXECUTED, FAILED")
    result_payload: Optional[Dict[str, Any]] = Field(default_factory=dict)
    error_message: Optional[str] = None
    nonce: str
    timestamp: datetime
    signature: str = Field(..., description="Device signature over command_id, status, nonce, timestamp")


class CommandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    issued_by: UUID
    command_type: str
    payload: Dict[str, Any]
    nonce: str
    status: str
    expires_at: datetime
    signature: str
    dispatched_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    executed_at: Optional[datetime]
    result_payload: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
