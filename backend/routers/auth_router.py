from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyEmailOTPRequest,
    VerifyEmailTokenRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from backend.schemas.user import UserProfileResponse
from backend.schemas.response import success_response, error_response
from backend.services.auth_service import AuthService
from backend.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Autentikasi"])


def _get_client_ip(request: Request) -> str:
    """Mengambil IP address klien dengan proteksi reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Mendaftarkan akun baru (Role secara otomatis 'user')."""
    ip_addr = _get_client_ip(request)
    ok, msg, data = AuthService.register(db=db, req=req, ip_address=ip_addr)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "REGISTRATION_FAILED", "message": msg}
        )
    return success_response(data=data, message=msg)


@router.post("/login", status_code=status.HTTP_200_OK)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Login akun menggunakan email atau username dan kata sandi."""
    ip_addr = _get_client_ip(request)
    u_agent = request.headers.get("User-Agent", "")
    ok, msg, token_resp = AuthService.login(db=db, req=req, ip_address=ip_addr, user_agent=u_agent)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": msg}
        )
    return success_response(data=token_resp.dict(), message=msg)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mencabut sesi autentikasi pengguna saat ini (Session Revocation)."""
    raw_token = getattr(request.state, "raw_token", None)
    if raw_token:
        AuthService.logout(db=db, token=raw_token, user=current_user, ip_address=_get_client_ip(request))
    return success_response(message="Sesi berhasil diakhiri (logout)")


@router.get("/me", status_code=status.HTTP_200_OK)
def get_auth_me(current_user: User = Depends(get_current_user)):
    """Mengambil informasi identitas pengguna aktif dari token yang terautentikasi."""
    user_data = UserProfileResponse.from_orm(current_user).dict()
    return success_response(data=user_data, message="Data sesi pengguna aktif berhasil diambil")


@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email_otp(req: VerifyEmailOTPRequest, request: Request, db: Session = Depends(get_db)):
    """Memverifikasi akun menggunakan 6-digit kode OTP."""
    ip_addr = _get_client_ip(request)
    ok, msg = AuthService.verify_email_otp(db=db, email=req.email, otp_code=req.otp_code, ip_address=ip_addr)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VERIFICATION_FAILED", "message": msg}
        )
    return success_response(message=msg)


@router.get("/verify-email", status_code=status.HTTP_200_OK)
def verify_email_link(token: str, request: Request, db: Session = Depends(get_db)):
    """Memverifikasi akun melalui klik tautan verifikasi email."""
    ip_addr = _get_client_ip(request)
    ok, msg = AuthService.verify_email_token(db=db, token=token, ip_address=ip_addr)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_TOKEN", "message": msg}
        )
    return success_response(message=msg)


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(req: ResendVerificationRequest, request: Request, db: Session = Depends(get_db)):
    """Mengirim ulang kode OTP verifikasi email dengan perlindungan rate limiting."""
    ip_addr = _get_client_ip(request)
    ok, msg = AuthService.resend_verification(db=db, email=req.email, ip_address=ip_addr)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "RATE_LIMITED", "message": msg}
        )
    return success_response(message=msg)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(req: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Mengirim instruksi reset kata sandi jika email terdaftar."""
    ip_addr = _get_client_ip(request)
    ok, msg = AuthService.request_password_reset(db=db, email=req.email, ip_address=ip_addr)
    return success_response(message=msg)


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(req: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)):
    """Mereset kata sandi baru menggunakan token reset sekali pakai."""
    ip_addr = _get_client_ip(request)
    ok, msg = AuthService.reset_password(
        db=db,
        token=req.token,
        new_password=req.new_password,
        confirm_password=req.confirm_password,
        ip_address=ip_addr
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "RESET_PASSWORD_FAILED", "message": msg}
        )
    return success_response(message=msg)
