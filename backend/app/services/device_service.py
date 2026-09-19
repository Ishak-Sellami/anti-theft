import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.device import Device
from app.db.models.user import User
from app.schemas.device import (
    DeviceEnrollInitiateResponse,
    DeviceEnrollCompleteRequest,
    DeviceHeartbeatRequest
)
from app.schemas.state import SecurityState, ConnectivityState, PowerState
from app.core.crypto import (
    compute_public_key_fingerprint,
    verify_signature,
    generate_backend_ecdsa_keypair
)
from app.core.state_engine import (
    validate_security_state_transition,
    determine_power_state_from_battery
)
from app.core.exceptions import (
    ResourceNotFoundError,
    PermissionDeniedError,
    CryptographicVerificationError
)
from app.services.nonce_service import NonceService
from app.services.audit_service import AuditService
from app.services.ws_manager import ws_manager

# Cache in-memory enrollment sessions (pairing token -> (owner_id, nonce, expires_at))
ENROLLMENT_SESSIONS = {}

# Master backend signing key
MASTER_PRIV_KEY = None
MASTER_PUB_KEY = None


def get_master_backend_keys():
    global MASTER_PRIV_KEY, MASTER_PUB_KEY
    if not MASTER_PRIV_KEY or not MASTER_PUB_KEY:
        if settings.BACKEND_PRIVATE_KEY_PEM and settings.BACKEND_PUBLIC_KEY_PEM:
            MASTER_PRIV_KEY = settings.BACKEND_PRIVATE_KEY_PEM
            MASTER_PUB_KEY = settings.BACKEND_PUBLIC_KEY_PEM
        else:
            MASTER_PRIV_KEY, MASTER_PUB_KEY = generate_backend_ecdsa_keypair()
    return MASTER_PRIV_KEY, MASTER_PUB_KEY


class DeviceService:
    @staticmethod
    async def initiate_enrollment(
        owner_id: UUID,
        device_name: str,
        device_model: Optional[str] = None,
        os_version: Optional[str] = None
    ) -> DeviceEnrollInitiateResponse:
        """
        Initiates enrollment by generating a short-lived pairing token and returning backend public key.
        """
        _, pub_key = get_master_backend_keys()
        pairing_token = f"pair_{secrets.token_urlsafe(32)}"
        nonce = f"nonce_{secrets.token_hex(16)}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        ENROLLMENT_SESSIONS[pairing_token] = {
            "owner_id": owner_id,
            "device_name": device_name,
            "device_model": device_model,
            "os_version": os_version,
            "nonce": nonce,
            "expires_at": expires_at
        }

        return DeviceEnrollInitiateResponse(
            enrollment_token=pairing_token,
            nonce=nonce,
            backend_public_key_pem=pub_key,
            expires_at=expires_at
        )

    @staticmethod
    async def complete_enrollment(
        db: AsyncSession,
        request: DeviceEnrollCompleteRequest
    ) -> Device:
        """
        Validates the device's public key, verifies signature over the enrollment payload,
        checks the pairing token and nonce, and registers the device.
        """
        session_data = ENROLLMENT_SESSIONS.get(request.enrollment_token)
        if not session_data:
            raise PermissionDeniedError("Invalid or expired enrollment token")

        now = datetime.now(timezone.utc)
        if now > session_data["expires_at"]:
            del ENROLLMENT_SESSIONS[request.enrollment_token]
            raise PermissionDeniedError("Enrollment token has expired")

        # Validate nonce and replay
        await NonceService.validate_and_record_nonce(
            db=db,
            nonce=request.nonce,
            request_timestamp=request.timestamp
        )

        # Verify signature over enrollment payload
        payload_to_verify = {
            "enrollment_token": request.enrollment_token,
            "device_name": request.device_name,
            "device_model": request.device_model,
            "os_version": request.os_version,
            "agent_version": request.agent_version,
            "nonce": request.nonce,
            "timestamp": request.timestamp.isoformat()
        }

        verify_signature(
            payload=payload_to_verify,
            signature_b64=request.signature,
            public_key_pem=request.public_key_pem
        )

        # Compute public key fingerprint
        fingerprint = compute_public_key_fingerprint(request.public_key_pem)

        # Check if fingerprint already enrolled
        stmt = select(Device).where(Device.public_key_fingerprint == fingerprint)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise PermissionDeniedError("Device with this public key fingerprint is already enrolled")

        owner_id = session_data["owner_id"]
        device = Device(
            owner_id=owner_id,
            device_name=request.device_name,
            device_model=request.device_model,
            os_version=request.os_version,
            agent_version=request.agent_version,
            security_state=SecurityState.NORMAL.value,
            connectivity_state=ConnectivityState.ONLINE.value,
            power_state=PowerState.NORMAL.value,
            public_key_pem=request.public_key_pem,
            public_key_fingerprint=fingerprint,
            enrollment_status="ACTIVE",
            active_policy_id="pol_stolen_default_v1",
            last_heartbeat_at=now
        )
        db.add(device)
        await db.flush()

        # Clean up pairing session
        del ENROLLMENT_SESSIONS[request.enrollment_token]

        # Audit log
        await AuditService.log_action(
            db=db,
            actor_type="DEVICE",
            actor_id=str(device.id),
            action="DEVICE_ENROLLED",
            resource_type="DEVICE",
            resource_id=str(device.id),
            details={
                "owner_id": str(owner_id),
                "device_name": device.device_name,
                "fingerprint": fingerprint
            }
        )

        # Notify via WebSocket
        await ws_manager.broadcast_device_event(
            owner_id=owner_id,
            event_type="DEVICE_ENROLLED",
            data={"device_id": str(device.id), "device_name": device.device_name}
        )

        return device

    @staticmethod
    async def get_device(db: AsyncSession, device_id: UUID) -> Device:
        stmt = select(Device).where(Device.id == device_id)
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            raise ResourceNotFoundError(f"Device {device_id} not found")
        return device

    @staticmethod
    async def get_user_devices(db: AsyncSession, user_id: UUID) -> List[Device]:
        stmt = select(Device).where(Device.owner_id == user_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_security_state(
        db: AsyncSession,
        device_id: UUID,
        target_state: SecurityState,
        actor_user: Optional[User] = None,
        reason: Optional[str] = None
    ) -> Device:
        device = await DeviceService.get_device(db, device_id)

        current_security_state = SecurityState(device.security_state)
        is_authorized = True
        if actor_user and actor_user.role not in {"OWNER", "ADMIN"}:
            is_authorized = False

        validate_security_state_transition(
            current=current_security_state,
            target=target_state,
            is_authorized_actor=is_authorized
        )

        device.security_state = target_state.value
        device.updated_at = datetime.now(timezone.utc)
        await db.flush()

        actor_id = str(actor_user.id) if actor_user else "SYSTEM"
        actor_type = "USER" if actor_user else "SYSTEM"

        await AuditService.log_action(
            db=db,
            actor_type=actor_type,
            actor_id=actor_id,
            action=f"SECURITY_STATE_CHANGED_{target_state.value}",
            resource_type="DEVICE",
            resource_id=str(device.id),
            details={
                "from_state": current_security_state.value,
                "to_state": target_state.value,
                "reason": reason
            }
        )

        await ws_manager.broadcast_device_event(
            owner_id=device.owner_id,
            event_type="STATE_CHANGED",
            data={
                "device_id": str(device.id),
                "security_state": device.security_state,
                "connectivity_state": device.connectivity_state,
                "power_state": device.power_state
            }
        )
        return device

    @staticmethod
    async def process_heartbeat(
        db: AsyncSession,
        request: DeviceHeartbeatRequest
    ) -> Device:
        device = await DeviceService.get_device(db, request.device_id)

        # Validate replay & freshness
        await NonceService.validate_and_record_nonce(
            db=db,
            nonce=request.nonce,
            request_timestamp=request.timestamp,
            device_id=str(device.id)
        )

        # Verify signature
        payload_to_verify = {
            "device_id": str(request.device_id),
            "battery_level": request.battery_level,
            "is_charging": request.is_charging,
            "connectivity_state": request.connectivity_state.value,
            "nonce": request.nonce,
            "timestamp": request.timestamp.isoformat()
        }
        verify_signature(
            payload=payload_to_verify,
            signature_b64=request.signature,
            public_key_pem=device.public_key_pem
        )

        now = datetime.now(timezone.utc)
        device.last_heartbeat_at = now
        device.connectivity_state = request.connectivity_state.value
        if request.battery_level is not None:
            device.battery_level = request.battery_level
            device.is_charging = request.is_charging
            device.power_state = determine_power_state_from_battery(
                request.battery_level,
                request.is_charging
            ).value

        await db.flush()
        return device
