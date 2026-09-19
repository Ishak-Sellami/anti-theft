from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    prev_hash: str
    entry_hash: str
    created_at: datetime
