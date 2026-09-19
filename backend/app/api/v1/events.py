from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.event import SecurityEventCreateRequest, SecurityEventResponse
from app.services.event_service import EventService
from app.services.device_service import DeviceService
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/events", tags=["Security Events"])


@router.post("", response_model=SecurityEventResponse, status_code=status.HTTP_201_CREATED)
async def submit_security_event(
    request: SecurityEventCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a signed security event (e.g., POWER_OFF_ATTEMPT, FACTORY_RESET_ATTEMPT, SIM_SWAP, etc.).
    Automatically shifts device state and emits real-time WebSocket alerts to dashboard.
    """
    return await EventService.process_security_event(db, request)


@router.get("/{device_id}", response_model=List[SecurityEventResponse])
async def get_device_security_events(
    device_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves immutable security events for an authorized device."""
    device = await DeviceService.get_device(db, device_id)
    if current_user.role != "ADMIN" and device.owner_id != current_user.id:
        raise PermissionDeniedError("Access denied to security events for this device")

    return await EventService.get_device_events(db, device_id, limit)
