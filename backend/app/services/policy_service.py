from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.policy import RecoveryPolicyModel
from app.schemas.policy import (
    RecoveryPolicyCreateRequest,
    RecoveryPolicyConfig,
    PowerStatePolicy,
    RetryConfig,
    StorageLimits
)
from app.schemas.state import SecurityState
from app.core.exceptions import ResourceNotFoundError, InvalidPolicyError


def get_default_stolen_policy() -> RecoveryPolicyConfig:
    return RecoveryPolicyConfig(
        policy_version=1,
        policy_id="pol_stolen_default_v1",
        security_state=SecurityState.STOLEN,
        power_state_overrides={
            "NORMAL": PowerStatePolicy(
                location_interval_ms=15000,
                location_fastest_interval_ms=10000,
                location_accuracy="HIGH_ACCURACY",
                heartbeat_interval_ms=30000,
                telemetry_batch_size=1,
                enable_ble_beacon=False
            ),
            "LOW": PowerStatePolicy(
                location_interval_ms=60000,
                location_fastest_interval_ms=30000,
                location_accuracy="BALANCED_POWER",
                heartbeat_interval_ms=120000,
                telemetry_batch_size=5,
                enable_ble_beacon=False
            ),
            "CRITICAL": PowerStatePolicy(
                location_interval_ms=300000,
                location_fastest_interval_ms=180000,
                location_accuracy="PRIORITIZE_CELL_WIFI",
                heartbeat_interval_ms=600000,
                telemetry_batch_size=10,
                enable_ble_beacon=False
            )
        },
        retry_config=RetryConfig(
            initial_retry_interval_ms=5000,
            max_retry_interval_ms=300000,
            backoff_multiplier=2.0,
            max_jitter_ms=1000
        ),
        storage_limits=StorageLimits(
            offline_queue_max_records=10000,
            eviction_strategy="DROP_OLDEST_UNIMPORTANT"
        )
    )


class PolicyService:
    @staticmethod
    async def initialize_default_policies(db: AsyncSession):
        """Seeds default recovery policies if not present."""
        stolen_pol = get_default_stolen_policy()
        stmt = select(RecoveryPolicyModel).where(RecoveryPolicyModel.id == stolen_pol.policy_id)
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            db_pol = RecoveryPolicyModel(
                id=stolen_pol.policy_id,
                name="Default Stolen Recovery Policy",
                description="Aggressive multi-tier telemetry policy for stolen device recovery",
                is_default=True,
                policy_json=stolen_pol.model_dump(mode="json")
            )
            db.add(db_pol)
            await db.flush()

    @staticmethod
    async def get_policy(db: AsyncSession, policy_id: str) -> RecoveryPolicyModel:
        stmt = select(RecoveryPolicyModel).where(RecoveryPolicyModel.id == policy_id)
        res = await db.execute(stmt)
        pol = res.scalar_one_or_none()
        if not pol:
            raise ResourceNotFoundError(f"RecoveryPolicy '{policy_id}' not found")
        return pol

    @staticmethod
    async def create_policy(db: AsyncSession, request: RecoveryPolicyCreateRequest) -> RecoveryPolicyModel:
        # Check if already exists
        stmt = select(RecoveryPolicyModel).where(RecoveryPolicyModel.id == request.id)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise InvalidPolicyError(f"Policy with ID '{request.id}' already exists")

        model = RecoveryPolicyModel(
            id=request.id,
            name=request.name,
            description=request.description,
            is_default=request.is_default,
            policy_json=request.config.model_dump(mode="json")
        )
        db.add(model)
        await db.flush()
        return model

    @staticmethod
    async def list_policies(db: AsyncSession) -> List[RecoveryPolicyModel]:
        stmt = select(RecoveryPolicyModel)
        res = await db.execute(stmt)
        return list(res.scalars().all())
