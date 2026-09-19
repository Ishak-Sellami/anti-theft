from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.telemetry import (
    TelemetryBatchIngestRequest,
    TelemetryIngestResult,
    TelemetryResponse
)
from app.services.telemetry_service import TelemetryService
from app.services.device_service import DeviceService
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/batch", response_model=TelemetryIngestResult, status_code=status.HTTP_201_CREATED)
async def ingest_telemetry_batch(
    request: TelemetryBatchIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a batch of cryptographically signed location/health telemetry records from an enrolled device.
    Supports delayed/offline store-and-forward telemetry.
    """
    return await TelemetryService.ingest_telemetry_batch(db, request)


@router.get("/{device_id}/history", response_model=List[TelemetryResponse])
async def get_device_telemetry_history(
    device_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves chronological telemetry and location history for a device."""
    device = await DeviceService.get_device(db, device_id)
    if current_user.role != "ADMIN" and device.owner_id != current_user.id:
        raise PermissionDeniedError("Access denied to telemetry for this device")

    return await TelemetryService.get_device_telemetry_history(db, device_id, limit)
