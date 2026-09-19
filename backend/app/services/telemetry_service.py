from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.telemetry import LocationTelemetry
from app.db.models.device import Device
from app.schemas.telemetry import TelemetryBatchIngestRequest, TelemetryIngestResult, TelemetryItem
from app.schemas.state import PowerState, SecurityState, ConnectivityState
from app.core.crypto import verify_signature
from app.core.state_engine import determine_power_state_from_battery
from app.core.exceptions import ResourceNotFoundError
from app.services.nonce_service import NonceService
from app.services.ws_manager import ws_manager


class TelemetryService:
    @staticmethod
    async def ingest_telemetry_batch(
        db: AsyncSession,
        request: TelemetryBatchIngestRequest
    ) -> TelemetryIngestResult:
        """
        Ingests a batch of telemetry items from a device (including store-and-forward buffered items).
        Verifies device signature, nonces, and updates device's last known position.
        """
        stmt = select(Device).where(Device.id == request.device_id)
        res = await db.execute(stmt)
        device = res.scalar_one_or_none()
        if not device:
            raise ResourceNotFoundError(f"Device {request.device_id} not found")

        # Validate nonce and replay
        await NonceService.validate_and_record_nonce(
            db=db,
            nonce=request.nonce,
            request_timestamp=request.timestamp,
            device_id=str(device.id)
        )

        # Build payload for cryptographic verification using exact submitted items
        payload_to_verify = {
            "device_id": str(request.device_id),
            "items": request.items,
            "nonce": request.nonce,
            "timestamp": request.timestamp.isoformat()
        }

        verify_signature(
            payload=payload_to_verify,
            signature_b64=request.signature,
            public_key_pem=device.public_key_pem
        )

        # Parse and validate individual items
        parsed_items: List[TelemetryItem] = [TelemetryItem.model_validate(item) for item in request.items]

        now = datetime.now(timezone.utc)
        latest_item_recorded_at = None
        new_records = []

        for item in parsed_items:
            pwr_state = item.power_state.value if item.power_state else device.power_state
            sec_state = item.security_state.value if item.security_state else device.security_state
            conn_state = item.connectivity_state.value if item.connectivity_state else ConnectivityState.ONLINE.value

            rec = LocationTelemetry(
                device_id=device.id,
                latitude=item.latitude,
                longitude=item.longitude,
                altitude=item.altitude,
                accuracy=item.accuracy,
                speed=item.speed,
                bearing=item.bearing,
                provider=item.provider,
                battery_level=item.battery_level,
                power_state=pwr_state,
                security_state=sec_state,
                connectivity_state=conn_state,
                network_metadata=item.network_metadata or {},
                recorded_at=item.recorded_at,
                received_at=now
            )
            new_records.append(rec)
            db.add(rec)

            if not latest_item_recorded_at or item.recorded_at > latest_item_recorded_at:
                latest_item_recorded_at = item.recorded_at

        # Update device current snapshot with the latest recorded telemetry
        if new_records:
            sorted_items = sorted(parsed_items, key=lambda x: x.recorded_at, reverse=True)
            newest_item = sorted_items[0]
            device.last_known_lat = newest_item.latitude
            device.last_known_lng = newest_item.longitude
            device.last_known_accuracy = newest_item.accuracy
            if newest_item.battery_level is not None:
                device.battery_level = newest_item.battery_level
                device.power_state = determine_power_state_from_battery(newest_item.battery_level).value
            device.last_heartbeat_at = now
            device.connectivity_state = ConnectivityState.ONLINE.value

        await db.flush()

        # Broadcast live location update to dashboard
        if new_records:
            latest = sorted(new_records, key=lambda r: r.recorded_at, reverse=True)[0]
            await ws_manager.broadcast_device_event(
                owner_id=device.owner_id,
                event_type="LOCATION_UPDATE",
                data={
                    "device_id": str(device.id),
                    "latitude": latest.latitude,
                    "longitude": latest.longitude,
                    "accuracy": latest.accuracy,
                    "battery_level": latest.battery_level,
                    "recorded_at": latest.recorded_at.isoformat(),
                    "security_state": device.security_state
                }
            )

        return TelemetryIngestResult(
            ingested_count=len(new_records),
            latest_recorded_at=latest_item_recorded_at or now,
            server_time=now
        )

    @staticmethod
    async def get_device_telemetry_history(
        db: AsyncSession,
        device_id: UUID,
        limit: int = 100
    ) -> List[LocationTelemetry]:
        stmt = (
            select(LocationTelemetry)
            .where(LocationTelemetry.device_id == device_id)
            .order_by(desc(LocationTelemetry.recorded_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
