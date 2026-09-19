from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    full_name: Optional[str] = None
    role: str = Field(default="OWNER", description="User role: OWNER, ADMIN, AUDITOR, INVESTIGATOR")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID
    role: str


class TokenPayload(BaseModel):
    sub: str
    role: str
    iat: int
    exp: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: Optional[str]
    role: str
    created_at: datetime
