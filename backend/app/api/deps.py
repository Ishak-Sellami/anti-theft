from typing import Optional
from uuid import UUID
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.user import User
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, PermissionDeniedError

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency that parses JWT bearer token and resolves the user."""
    if not auth_creds:
        raise AuthenticationError("Authorization header missing")

    token = auth_creds.credentials
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Invalid token payload: missing subject")
        user_id = UUID(user_id_str)
    except Exception as e:
        raise AuthenticationError(f"Authentication token invalid: {str(e)}")

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise AuthenticationError("User associated with token not found")

    return user


async def require_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency that ensures the authenticated user is an ADMIN or INVESTIGATOR."""
    if current_user.role not in {"ADMIN", "INVESTIGATOR"}:
        raise PermissionDeniedError("Admin privileges required for this operation")
    return current_user
