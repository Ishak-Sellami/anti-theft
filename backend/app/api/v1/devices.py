from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.device import (
    DeviceEnrollInitiateRequest,
    DeviceEnrollInitiateResponse,
    DeviceEnrollCompleteRequest,
    DeviceResponse,
    DeviceUpdateSecurityStateRequest,
    DeviceHeartbeatRequest
)
from app.services.device_service import DeviceService
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/enroll/initiate", response_model=DeviceEnrollInitiateResponse)
async def initiate_enrollment(
    request: DeviceEnrollInitiateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Step 1 of enrollment: Owner generates a pairing token and receives the backend public key.
    """
    return await DeviceService.initiate_enrollment(
        owner_id=current_user.id,
        device_name=request.device_name,
        device_model=request.device_model,
        os_version=request.os_version
    )


@router.post("/enroll/complete", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def complete_enrollment(
    request: DeviceEnrollCompleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2 of enrollment: Android Agent submits its public key and signed proof-of-possession payload.
    """
    device = await DeviceService.complete_enrollment(db, request)
    return device


@router.get("", response_model=List[DeviceResponse])
async def list_user_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists all enrolled devices belonging to the authenticated owner."""
    return await DeviceService.get_user_devices(db, current_user.id)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device_detail(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full device state and metadata with authorization check."""
    device = await DeviceService.get_device(db, device_id)
    if current_user.role != "ADMIN" and device.owner_id != current_user.id:
        raise PermissionDeniedError("Access denied to this device")
    return device


@router.patch("/{device_id}/security-state", response_model=DeviceResponse)
async def update_device_security_state(
    device_id: UUID,
    request: DeviceUpdateSecurityStateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Updates the device security state dimension (e.g., NORMAL -> STOLEN / RECOVERY).
    """
    device = await DeviceService.get_device(db, device_id)
    if current_user.role != "ADMIN" and device.owner_id != current_user.id:
        raise PermissionDeniedError("Access denied to change state on this device")

    updated = await DeviceService.update_security_state(
        db=db,
        device_id=device_id,
        target_state=request.target_security_state,
        actor_user=current_user,
        reason=request.reason
    )
    return updated


@router.post("/heartbeat", response_model=DeviceResponse)
async def submit_device_heartbeat(
    request: DeviceHeartbeatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Device agent submits periodic signed heartbeat ping to confirm reachability, battery, and connectivity.
    """
    return await DeviceService.process_heartbeat(db, request)
