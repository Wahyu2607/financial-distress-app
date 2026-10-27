from __future__ import annotations

from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User, UserRole, UserStatus
from backend.models.session import UserSession
from backend.security.tokens import decode_access_token
from backend.security.hashing import hash_token


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Middleware Dependency untuk memverifikasi autentikasi pengguna:
    1. Membaca header 'Authorization: Bearer <token>'
    2. Memverifikasi tanda tangan JWT dan masa berlaku
    3. Memeriksa status sesi di database (apakah token telah di-logout/dicabut)
    4. Mengambil objek User terbaru dari database
    5. Menolak jika akun dinonaktifkan
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Token autentikasi tidak ditemukan pada header permintaan."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN_FORMAT", "message": "Format token tidak valid. Gunakan 'Bearer <token>'."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = parts[1]
    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED_OR_INVALID", "message": "Token autentikasi tidak valid atau telah kedaluwarsa."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_PAYLOAD", "message": "Muatan token tidak valid."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cek status pencabutan sesi di database (Revocation check)
    t_hash = hash_token(raw_token)
    session_record = db.query(UserSession).filter(
        UserSession.token_hash == t_hash,
        UserSession.user_id == user_id
    ).first()

    if not session_record or not session_record.is_valid():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "SESSION_REVOKED", "message": "Sesi autentikasi telah diakhiri (logout) atau dicabut."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "Akun pengguna tidak ditemukan."},
        )

    if user.status == UserStatus.DISABLED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "Akun Anda berstatus nonaktif. Akses ditolak."},
        )

    # Simpan raw_token di request state agar endpoint logout dapat menggunakannya
    request.state.raw_token = raw_token
    return user


def require_verified_user(current_user: User = Depends(get_current_user)) -> User:
    """Memastikan akun pengguna telah memverifikasi alamat emailnya."""
    if current_user.status == UserStatus.PENDING_VERIFICATION.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "EMAIL_UNVERIFIED", "message": "Fitur ini memerlukan verifikasi alamat email terlebih dahulu."},
        )
    return current_user


def require_role(allowed_roles: list[str]) -> Callable:
    """
    Dependency generator untuk Role-Based Access Control (RBAC).
    Memastikan hanya pengguna dengan role tertentu yang dapat mengakses endpoint.
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Akses ditolak: Anda tidak memiliki wewenang yang cukup untuk mengakses sumber daya ini."
                },
            )
        return user

    return role_checker


# Dependency siap pakai untuk Administrator
require_admin = require_role([UserRole.ADMIN.value])
