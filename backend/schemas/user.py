from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
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
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    institution: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)

    # Note: 'role' dan 'status' tidak ada di schema ini untuk mencegah IDOR / privilege escalation


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., description="Kata sandi saat ini untuk verifikasi keamanan")
    new_password: str = Field(..., min_length=8, description="Kata sandi baru")
    confirm_password: str = Field(..., min_length=8, description="Konfirmasi kata sandi baru")
