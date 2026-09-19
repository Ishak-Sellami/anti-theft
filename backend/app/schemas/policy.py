from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.state import SecurityState, PowerState


class PowerStatePolicy(BaseModel):
    location_interval_ms: int = Field(..., ge=1000, le=86400000)
    location_fastest_interval_ms: int = Field(..., ge=500, le=86400000)
    location_accuracy: str = Field("HIGH_ACCURACY", description="HIGH_ACCURACY, BALANCED_POWER, NO_POWER, PRIORITIZE_CELL_WIFI")
    heartbeat_interval_ms: int = Field(..., ge=5000, le=86400000)
    telemetry_batch_size: int = Field(1, ge=1, le=500)
    enable_ble_beacon: bool = False


class RetryConfig(BaseModel):
    initial_retry_interval_ms: int = Field(5000, ge=500)
    max_retry_interval_ms: int = Field(300000, ge=1000)
    backoff_multiplier: float = Field(2.0, ge=1.0, le=10.0)
    max_jitter_ms: int = Field(1000, ge=0)


class StorageLimits(BaseModel):
    offline_queue_max_records: int = Field(10000, ge=100, le=100000)
    eviction_strategy: str = Field("DROP_OLDEST_UNIMPORTANT", description="DROP_OLDEST_UNIMPORTANT, DROP_OLDEST, REJECT_NEW")


class RecoveryPolicyConfig(BaseModel):
    policy_version: int = 1
    policy_id: str
    security_state: SecurityState
    power_state_overrides: Dict[str, PowerStatePolicy]
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    storage_limits: StorageLimits = Field(default_factory=StorageLimits)


class RecoveryPolicyCreateRequest(BaseModel):
    id: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_default: bool = False
    config: RecoveryPolicyConfig


class RecoveryPolicyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_default: bool
    config: RecoveryPolicyConfig
    created_at: datetime
    updated_at: datetime
