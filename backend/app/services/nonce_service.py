from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.nonce import UsedNonce
from app.core.exceptions import ReplayAttackError


class NonceService:
    @staticmethod
    async def validate_and_record_nonce(
        db: AsyncSession,
        nonce: str,
        request_timestamp: datetime,
        device_id: Optional[str] = None
    ) -> None:
        """
        Validates timestamp freshness and verifies that the nonce has not been seen before.
        Raises ReplayAttackError if the timestamp is expired or nonce has already been recorded.
        """
        now = datetime.now(timezone.utc)
        
        # Ensure request_timestamp has timezone info
        if request_timestamp.tzinfo is None:
            request_timestamp = request_timestamp.replace(tzinfo=timezone.utc)

        # Check timestamp skew / freshness (e.g., +/- 5 minutes)
        time_diff = abs((now - request_timestamp).total_seconds())
        if time_diff > settings.REQUEST_TIMESTAMP_TOLERANCE_SECONDS:
            raise ReplayAttackError(
                f"Request timestamp expired or clock skew excessive ({time_diff:.1f}s > {settings.REQUEST_TIMESTAMP_TOLERANCE_SECONDS}s)"
            )

        # Check if nonce already exists in database
        stmt = select(UsedNonce).where(UsedNonce.nonce == nonce)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            raise ReplayAttackError("Replay attack detected: Nonce has already been consumed")

        # Record nonce with expiration time
        expires_at = now + timedelta(seconds=settings.NONCE_EXPIRATION_SECONDS)
        used_nonce = UsedNonce(
            nonce=nonce,
            device_id=str(device_id) if device_id else None,
            expires_at=expires_at,
            created_at=now
        )
        db.add(used_nonce)
        await db.flush()
