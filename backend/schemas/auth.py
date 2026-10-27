from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Nama lengkap")
    email: str = Field(..., max_length=254, description="Alamat email aktif")
    username: str = Field(..., min_length=3, max_length=30, description="Username unik")
    password: str = Field(..., min_length=8, description="Kata sandi akun")
    institution: Optional[str] = Field(None, max_length=255, description="Instansi/Kampus/Perusahaan")
    phone_number: Optional[str] = Field(None, max_length=50, description="Nomor telepon")


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Email atau username akun")
    password: str = Field(..., description="Kata sandi akun")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_seconds: int
    user_id: str
    name: str
    email: str
    username: str
    role: str
    status: str


class VerifyEmailOTPRequest(BaseModel):
    email: str = Field(..., description="Email akun yang diverifikasi")
    otp_code: str = Field(..., min_length=6, max_length=6, description="Kode OTP 6 digit")


class VerifyEmailTokenRequest(BaseModel):
    token: str = Field(..., description="Token verifikasi dari tautan email")


class ResendVerificationRequest(BaseModel):
    email: str = Field(..., description="Email yang meminta pengiriman ulang OTP/link")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Email akun yang meminta reset kata sandi")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Token reset kata sandi")
    new_password: str = Field(..., min_length=8, description="Kata sandi baru")
    confirm_password: str = Field(..., min_length=8, description="Konfirmasi kata sandi baru")
