import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.command import DeviceCommand
from app.db.models.device import Device
from app.db.models.user import User
from app.schemas.command import CommandCreateRequest, CommandAckRequest
from app.core.crypto import sign_payload, verify_signature
from app.core.exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    CryptographicVerificationError
)
from app.services.nonce_service import NonceService
from app.services.audit_service import AuditService
from app.services.device_service import get_master_backend_keys
from app.services.ws_manager import ws_manager


class CommandService:
    @staticmethod
    async def create_command(
        db: AsyncSession,
        issuer: User,
        request: CommandCreateRequest
    ) -> DeviceCommand:
        """
        Creates, signs, and queues a remote command for an enrolled device.
        """
        stmt = select(Device).where(Device.id == request.device_id)
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            raise ResourceNotFoundError(f"Device {request.device_id} not found")

        # Authorization: Must be device owner or admin
        if issuer.role != "ADMIN" and device.owner_id != issuer.id:
            raise PermissionDeniedError("You do not have permission to issue commands to this device")

        priv_key, _ = get_master_backend_keys()
        cmd_id = uuid.uuid4()
        nonce = f"cmd_nonce_{secrets.token_hex(16)}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=request.ttl_seconds)

        # Build canonical payload to sign
        payload_to_sign = {
            "command_id": str(cmd_id),
            "device_id": str(device.id),
            "command_type": request.command_type,
            "payload": request.payload,
            "nonce": nonce,
            "expires_at": expires_at.isoformat(),
            "created_at": now.isoformat()
        }

        signature = sign_payload(payload_to_sign, priv_key)

        command = DeviceCommand(
            id=cmd_id,
            device_id=device.id,
            issued_by=issuer.id,
            command_type=request.command_type,
            payload=request.payload,
            nonce=nonce,
            status="PENDING",
            expires_at=expires_at,
            signature=signature,
            created_at=now
        )
        db.add(command)
        await db.flush()

        # Audit log
        await AuditService.log_action(
            db=db,
            actor_type="USER",
            actor_id=str(issuer.id),
            action=f"COMMAND_ISSUED_{request.command_type}",
            resource_type="COMMAND",
            resource_id=str(cmd_id),
            details={
                "device_id": str(device.id),
                "command_type": request.command_type,
                "payload": request.payload,
                "expires_at": expires_at.isoformat()
            }
        )

        # Broadcast command update
        await ws_manager.broadcast_device_event(
            owner_id=device.owner_id,
            event_type="COMMAND_CREATED",
            data={
                "command_id": str(cmd_id),
                "device_id": str(device.id),
                "command_type": request.command_type,
                "status": "PENDING"
            }
        )

        return command

    @staticmethod
    async def acknowledge_command(
        db: AsyncSession,
        request: CommandAckRequest
    ) -> DeviceCommand:
        """
        Processes command execution acknowledgment from the device agent.
        Verifies device signature over execution result.
        """
        stmt = select(DeviceCommand).where(DeviceCommand.id == request.command_id)
        res = await db.execute(stmt)
        command = res.scalar_one_or_none()
        if not command:
            raise ResourceNotFoundError(f"Command {request.command_id} not found")

        stmt_dev = select(Device).where(Device.id == request.device_id)
        res_dev = await db.execute(stmt_dev)
        device = res_dev.scalar_one_or_none()
        if not device:
            raise ResourceNotFoundError(f"Device {request.device_id} not found")

        # Validate nonce and freshness
        await NonceService.validate_and_record_nonce(
            db=db,
            nonce=request.nonce,
            request_timestamp=request.timestamp,
            device_id=str(device.id)
        )

        # Verify device signature over ack
        payload_to_verify = {
            "command_id": str(request.command_id),
            "device_id": str(request.device_id),
            "status": request.status,
            "result_payload": request.result_payload or {},
            "error_message": request.error_message,
            "nonce": request.nonce,
            "timestamp": request.timestamp.isoformat()
        }

        verify_signature(
            payload=payload_to_verify,
            signature_b64=request.signature,
            public_key_pem=device.public_key_pem
        )

        now = datetime.now(timezone.utc)
        command.status = request.status
        command.result_payload = request.result_payload
        command.error_message = request.error_message

        if request.status == "ACKNOWLEDGED":
            command.acknowledged_at = now
        elif request.status in {"EXECUTED", "FAILED"}:
            command.executed_at = now

        await db.flush()

        # Audit log
        await AuditService.log_action(
            db=db,
            actor_type="DEVICE",
            actor_id=str(device.id),
            action=f"COMMAND_RESULT_{request.status}",
            resource_type="COMMAND",
            resource_id=str(command.id),
            details={
                "command_type": command.command_type,
                "status": request.status,
                "error_message": request.error_message
            }
        )

        # Notify via WebSocket
        await ws_manager.broadcast_device_event(
            owner_id=device.owner_id,
            event_type="COMMAND_STATUS_UPDATED",
            data={
                "command_id": str(command.id),
                "device_id": str(device.id),
                "status": request.status,
                "result": request.result_payload
            }
        )

        return command

    @staticmethod
    async def get_pending_commands_for_device(
        db: AsyncSession,
        device_id: UUID
    ) -> List[DeviceCommand]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(DeviceCommand)
            .where(
                DeviceCommand.device_id == device_id,
                DeviceCommand.status == "PENDING",
                DeviceCommand.expires_at > now
            )
            .order_by(DeviceCommand.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_command_history(
        db: AsyncSession,
        device_id: UUID,
        limit: int = 50
    ) -> List[DeviceCommand]:
        stmt = (
            select(DeviceCommand)
            .where(DeviceCommand.device_id == device_id)
            .order_by(desc(DeviceCommand.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
