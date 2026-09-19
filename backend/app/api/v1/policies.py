from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.policy import (
    RecoveryPolicyCreateRequest,
    RecoveryPolicyResponse
)
from app.services.policy_service import PolicyService
from app.api.deps import require_admin_user, get_current_user

router = APIRouter(prefix="/policies", tags=["Recovery Policies"])


@router.get("", response_model=List[RecoveryPolicyResponse])
async def list_policies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists available RecoveryPolicy configurations."""
    policies = await PolicyService.list_policies(db)
    return [
        RecoveryPolicyResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            is_default=p.is_default,
            config=p.policy_json,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in policies
    ]


@router.get("/{policy_id}", response_model=RecoveryPolicyResponse)
async def get_policy(
    policy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves specific RecoveryPolicy definition."""
    p = await PolicyService.get_policy(db, policy_id)
    return RecoveryPolicyResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        is_default=p.is_default,
        config=p.policy_json,
        created_at=p.created_at,
        updated_at=p.updated_at
    )


@router.post("", response_model=RecoveryPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    request: RecoveryPolicyCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_admin_user)
):
    """Admin creates or registers a new RecoveryPolicy configuration."""
    p = await PolicyService.create_policy(db, request)
    return RecoveryPolicyResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        is_default=p.is_default,
        config=p.policy_json,
        created_at=p.created_at,
        updated_at=p.updated_at
    )
