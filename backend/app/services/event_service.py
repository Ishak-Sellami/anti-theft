from datetime import datetime, timezone
from typing import List
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event import SecurityEvent
from app.db.models.device import Device
from app.schemas.event import SecurityEventCreateRequest
from app.schemas.state import SecurityState
from app.core.crypto import verify_signature
from app.core.exceptions import ResourceNotFoundError
from app.services.nonce_service import NonceService
from app.services.audit_service import AuditService
from app.services.ws_manager import ws_manager


class EventService:
    @staticmethod
    async def process_security_event(
        db: AsyncSession,
        request: SecurityEventCreateRequest
    ) -> SecurityEvent:
        """
        Ingests a verified security event from a device agent.
        Escalates security state if applicable and broadcasts urgent real-time alert.
        """
        stmt = select(Device).where(Device.id == request.device_id)
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            raise ResourceNotFoundError(f"Device {request.device_id} not found")

        # Validate replay and freshness
        await NonceService.validate_and_record_nonce(
            db=db,
            nonce=request.nonce,
            request_timestamp=request.device_timestamp,
            device_id=str(device.id)
        )

        # Cryptographic verification
        payload_to_verify = {
            "device_id": str(request.device_id),
            "event_type": request.event_type,
            "severity": request.severity,
            "security_state_before": request.security_state_before.value,
            "security_state_after": request.security_state_after.value,
            "payload": request.payload,
            "device_timestamp": request.device_timestamp.isoformat(),
            "nonce": request.nonce
        }

        verify_signature(
            payload=payload_to_verify,
            signature_b64=request.signature,
            public_key_pem=device.public_key_pem
        )

        now = datetime.now(timezone.utc)
        sec_event = SecurityEvent(
            device_id=device.id,
            event_type=request.event_type,
            severity=request.severity,
            security_state_before=request.security_state_before.value,
            security_state_after=request.security_state_after.value,
            payload=request.payload,
            device_timestamp=request.device_timestamp,
            signature=request.signature,
            received_at=now
        )
        db.add(sec_event)

        # Update device security state if the event shifted it
        if request.security_state_after.value != device.security_state:
            device.security_state = request.security_state_after.value
            device.updated_at = now

        await db.flush()

        # Create tamper-evident audit record
        await AuditService.log_action(
            db=db,
            actor_type="DEVICE",
            actor_id=str(device.id),
            action=f"SECURITY_EVENT_{request.event_type}",
            resource_type="SECURITY_EVENT",
            resource_id=str(sec_event.id),
            details={
                "event_type": request.event_type,
                "severity": request.severity,
                "security_state_after": request.security_state_after.value,
                "payload": request.payload
            }
        )

        # Broadcast critical real-time alert via WebSocket
        await ws_manager.broadcast_device_event(
            owner_id=device.owner_id,
            event_type="SECURITY_EVENT_ALERT",
            data={
                "event_id": str(sec_event.id),
                "device_id": str(device.id),
                "event_type": request.event_type,
                "severity": request.severity,
                "security_state": device.security_state,
                "payload": request.payload,
                "device_timestamp": request.device_timestamp.isoformat()
            }
        )

        return sec_event

    @staticmethod
    async def get_device_events(
        db: AsyncSession,
        device_id: UUID,
        limit: int = 50
    ) -> List[SecurityEvent]:
        stmt = (
            select(SecurityEvent)
            .where(SecurityEvent.device_id == device_id)
            .order_by(desc(SecurityEvent.device_timestamp))
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
