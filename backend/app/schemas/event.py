from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.state import SecurityState


class SecurityEventCreateRequest(BaseModel):
    device_id: UUID
    event_type: str = Field(..., description="POWER_OFF_ATTEMPT, SHUTDOWN_NOTIFIED, FACTORY_RESET_ATTEMPT, FAILED_AUTH, SIM_SWAP, AIRPLANE_TOGGLE, TAMPER_DETECTED")
    severity: str = Field("HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    security_state_before: SecurityState
    security_state_after: SecurityState
    payload: Dict[str, Any] = Field(default_factory=dict)
    device_timestamp: datetime
    nonce: str
    signature: str


class SecurityEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    device_id: UUID
    event_type: str
    severity: str
    security_state_before: str
    security_state_after: str
    payload: Dict[str, Any]
    device_timestamp: datetime
    received_at: datetime
    signature: str
