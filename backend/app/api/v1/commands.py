from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.command import (
    CommandCreateRequest,
    CommandAckRequest,
    CommandResponse
)
from app.services.command_service import CommandService
from app.services.device_service import DeviceService
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/commands", tags=["Remote Commands"])


@router.post("", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
async def issue_remote_command(
    request: CommandCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Owner or Admin issues a signed remote command (SET_SECURITY_STATE, TRIGGER_ALARM, etc.) with nonce and TTL.
    """
    return await CommandService.create_command(db, current_user, request)


@router.post("/ack", response_model=CommandResponse)
async def acknowledge_command_execution(
    request: CommandAckRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Device agent posts cryptographically signed execution receipt / result for an issued command.
    """
    return await CommandService.acknowledge_command(db, request)


@router.get("/{device_id}/pending", response_model=List[CommandResponse])
async def get_pending_commands(
    device_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Device agent or dashboard polls for unexpired pending commands waiting for delivery.
    """
    return await CommandService.get_pending_commands_for_device(db, device_id)


@router.get("/{device_id}", response_model=List[CommandResponse])
async def get_command_history(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Owner or Admin retrieves historical command logs for a device.
    """
    device = await DeviceService.get_device(db, device_id)
    if current_user.role != "ADMIN" and device.owner_id != current_user.id:
        raise PermissionDeniedError("Access denied to command history for this device")

    return await CommandService.get_command_history(db, device_id)
