from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.audit import AuditLog
from app.db.models.user import User
from app.schemas.audit import AuditLogResponse
from app.api.deps import require_admin_user, get_current_user
from app.services.device_service import DeviceService
from app.core.exceptions import PermissionDeniedError

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """Admin/Auditor endpoint: retrieves system-wide tamper-evident hash-chained audit records."""
    stmt = select(AuditLog).order_by(desc(AuditLog.id)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/device/{device_id}", response_model=List[AuditLogResponse])
async def get_device_audit_logs(
    device_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Owner endpoint: retrieves tamper-evident audit records relating to their device."""
    device = await DeviceService.get_device(db, device_id)
    if current_user.role != "ADMIN" and device.owner_id != current_user.id:
        raise PermissionDeniedError("Access denied to audit logs for this device")

    stmt = (
        select(AuditLog)
        .where(AuditLog.resource_id == str(device_id))
        .order_by(desc(AuditLog.id))
        .limit(limit)
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())
