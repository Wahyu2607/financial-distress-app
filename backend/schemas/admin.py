from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    id: str
    name: str
    email: str
    username: str
    role: str
    status: str
    institution: Optional[str] = None
    phone_number: Optional[str] = None
    email_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    failed_login_attempts: int
    locked_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminCreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., max_length=254)
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    role: Literal["user", "admin"] = "user"
    status: Literal["active", "disabled", "pending_verification"] = "active"
    institution: Optional[str] = None
    phone_number: Optional[str] = None


class AdminUpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    institution: Optional[str] = None
    phone_number: Optional[str] = None


class AdminUpdateUserRoleRequest(BaseModel):
    role: Literal["user", "admin"] = Field(..., description="Role baru: 'admin' atau 'user'")


class AdminUpdateUserStatusRequest(BaseModel):
    status: Literal["active", "disabled", "pending_verification"] = Field(..., description="Status baru")


class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str]
    actor_email: Optional[str]
    action: str
    target_id: Optional[str]
    ip_address: Optional[str]
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
