from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.evidence import (
    EvidenceMetadataCreateRequest,
    EvidenceMetadataResponse
)
from app.services.evidence_service import EvidenceService
from app.services.device_service import DeviceService
from app.api.deps import get_current_user
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/evidence", tags=["Evidence Metadata"])


@router.post("", response_model=EvidenceMetadataResponse, status_code=status.HTTP_201_CREATED)
async def submit_evidence_metadata(
    request: EvidenceMetadataCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Device agent submits metadata, SHA-256 integrity hash, and storage URI for authorized evidence capture.
    """
    return await EvidenceService.record_evidence_metadata(db, request)


@router.get("/{device_id}", response_model=List[EvidenceMetadataResponse])
async def get_device_evidence(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves legal chain-of-custody evidence records for an authorized device."""
    device = await DeviceService.get_device(db, device_id)
    if current_user.role not in {"OWNER", "ADMIN", "INVESTIGATOR"}:
        raise PermissionDeniedError("Access denied to evidence records")
    if current_user.role == "OWNER" and device.owner_id != current_user.id:
        raise PermissionDeniedError("Access denied to this device's evidence records")

    return await EvidenceService.get_device_evidence(db, device_id)
