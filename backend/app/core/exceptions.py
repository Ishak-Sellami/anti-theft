from typing import Any, Optional, Dict
from fastapi import HTTPException, status


class AntiSarikaException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or "INTERNAL_ERROR"


class AuthenticationError(AntiSarikaException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_FAILED",
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDeniedError(AntiSarikaException):
    def __init__(self, detail: str = "Not authorized to perform this operation"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED",
        )


class CryptographicVerificationError(AntiSarikaException):
    def __init__(self, detail: str = "Cryptographic signature verification failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="CRYPTO_VERIFICATION_FAILED",
        )


class ReplayAttackError(AntiSarikaException):
    def __init__(self, detail: str = "Nonce has already been used or timestamp expired"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="REPLAY_DETECTED",
        )


class ResourceNotFoundError(AntiSarikaException):
    def __init__(self, detail: str = "Requested resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="RESOURCE_NOT_FOUND",
        )


class InvalidStateTransitionError(AntiSarikaException):
    def __init__(self, detail: str = "Invalid state transition requested"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_STATE_TRANSITION",
        )


class InvalidPolicyError(AntiSarikaException):
    def __init__(self, detail: str = "Invalid RecoveryPolicy parameters"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="INVALID_POLICY",
        )
