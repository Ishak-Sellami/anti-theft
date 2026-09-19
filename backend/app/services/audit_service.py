import json
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditLog
from app.core.crypto import compute_audit_hash

GENESIS_HASH = "0" * 64


class AuditService:
    @staticmethod
    async def log_action(
        db: AsyncSession,
        actor_type: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any]
    ) -> AuditLog:
        """
        Creates an append-only, tamper-evident hash-chained audit log entry.
        """
        # Fetch the most recent audit entry to obtain prev_hash
        query = select(AuditLog).order_by(desc(AuditLog.id)).limit(1)
        result = await db.execute(query)
        latest_entry = result.scalar_one_or_none()

        prev_hash = latest_entry.entry_hash if latest_entry else GENESIS_HASH
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        details_json = json.dumps(details, sort_keys=True, separators=(',', ':'))
        entry_hash = compute_audit_hash(
            prev_hash=prev_hash,
            actor_id=str(actor_id),
            action=action,
            resource_id=str(resource_id),
            timestamp_iso=now_iso,
            details_json=details_json
        )

        audit_entry = AuditLog(
            actor_type=actor_type,
            actor_id=str(actor_id),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            created_at=now_dt
        )
        db.add(audit_entry)
        await db.flush()
        return audit_entry
