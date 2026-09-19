from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SecurityState(str, Enum):
    NORMAL = "NORMAL"
    PROTECTED = "PROTECTED"
    STOLEN = "STOLEN"
    RECOVERY = "RECOVERY"


class ConnectivityState(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class PowerState(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    CRITICAL = "CRITICAL"


class DeviceCompositeState(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    security_state: SecurityState = Field(..., description="Current device security and enforcement state")
    connectivity_state: ConnectivityState = Field(..., description="Current communication and network status")
    power_state: PowerState = Field(..., description="Current battery and power status")
