from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.schemas.auth import UserCreate, Token
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
        """Registers a new user (owner or admin)."""
        # Check if email exists
        stmt = select(User).where(User.email == user_in.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise PermissionDeniedError("User with this email already exists")

        user = User(
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role.upper(),
        )
        db.add(user)
        await db.flush()

        await AuditService.log_action(
            db=db,
            actor_type="USER",
            actor_id=str(user.id),
            action="USER_REGISTERED",
            resource_type="USER",
            resource_id=str(user.id),
            details={"email": user.email, "role": user.role}
        )
        return user

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
        """Authenticates user with email and password."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            await AuditService.log_action(
                db=db,
                actor_type="USER",
                actor_id=email,
                action="USER_AUTH_FAILED",
                resource_type="AUTH",
                resource_id=email,
                details={"reason": "Invalid credentials"}
            )
            raise AuthenticationError("Incorrect email or password")

        await AuditService.log_action(
            db=db,
            actor_type="USER",
            actor_id=str(user.id),
            action="USER_AUTH_SUCCESS",
            resource_type="AUTH",
            resource_id=str(user.id),
            details={"email": user.email}
        )
        return user

    @staticmethod
    async def generate_user_token(user: User) -> Token:
        """Issues JWT access token for user."""
        token = create_access_token(
            subject=str(user.id),
            role=user.role,
            extra_claims={"email": user.email}
        )
        return Token(
            access_token=token,
            token_type="bearer",
            expires_in=60 * 24 * 60,
            user_id=user.id,
            role=user.role,
        )
