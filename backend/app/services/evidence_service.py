from datetime import datetime, timezone
from typing import List
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.evidence import EvidenceMetadata
from app.db.models.device import Device
from app.schemas.evidence import EvidenceMetadataCreateRequest
from app.core.crypto import verify_signature
from app.core.exceptions import ResourceNotFoundError
from app.services.nonce_service import NonceService
from app.services.audit_service import AuditService


class EvidenceService:
    @staticmethod
    async def record_evidence_metadata(
        db: AsyncSession,
        request: EvidenceMetadataCreateRequest
    ) -> EvidenceMetadata:
        """
        Stores metadata and integrity hashes for evidence collected in STOLEN/RECOVERY mode.
        Verifies device signature and writes tamper-evident audit record.
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
            "event_id": str(request.event_id) if request.event_id else None,
            "capture_type": request.capture_type,
            "integrity_hash": request.integrity_hash,
            "storage_ref": request.storage_ref,
            "mime_type": request.mime_type,
            "device_timestamp": request.device_timestamp.isoformat(),
            "nonce": request.nonce
        }

        verify_signature(
            payload=payload_to_verify,
            signature_b64=request.signature,
            public_key_pem=device.public_key_pem
        )

        now = datetime.now(timezone.utc)
        evidence = EvidenceMetadata(
            device_id=device.id,
            event_id=request.event_id,
            capture_type=request.capture_type,
            integrity_hash=request.integrity_hash,
            storage_ref=request.storage_ref,
            mime_type=request.mime_type,
            file_size_bytes=request.file_size_bytes,
            chain_of_custody_notes=request.chain_of_custody_notes,
            device_timestamp=request.device_timestamp,
            received_at=now
        )
        db.add(evidence)
        await db.flush()

        # Audit log
        await AuditService.log_action(
            db=db,
            actor_type="DEVICE",
            actor_id=str(device.id),
            action="EVIDENCE_RECORDED",
            resource_type="EVIDENCE",
            resource_id=str(evidence.id),
            details={
                "capture_type": request.capture_type,
                "integrity_hash": request.integrity_hash,
                "storage_ref": request.storage_ref
            }
        )

        return evidence

    @staticmethod
    async def get_device_evidence(
        db: AsyncSession,
        device_id: UUID
    ) -> List[EvidenceMetadata]:
        stmt = (
            select(EvidenceMetadata)
            .where(EvidenceMetadata.device_id == device_id)
            .order_by(desc(EvidenceMetadata.device_timestamp))
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
