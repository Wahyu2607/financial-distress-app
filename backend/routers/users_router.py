from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import UserProfileResponse, UpdateProfileRequest, ChangePasswordRequest
from backend.schemas.response import success_response
from backend.services.user_service import UserService
from backend.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/users", tags=["Pengelolaan Profil"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.get("/me", status_code=status.HTTP_200_OK)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Melihat data profil milik pengguna sendiri."""
    return success_response(
        data=UserProfileResponse.from_orm(current_user).dict(),
        message="Profil pengguna berhasil dimuat"
    )


@router.patch("/me", status_code=status.HTTP_200_OK)
def update_my_profile(
    req: UpdateProfileRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Memperbarui profil diri sendiri (nama, instansi, nomor telepon).
    Kolom 'role' dan 'status' tidak dapat diubah oleh user biasa.
    """
    ip_addr = _get_client_ip(request)
    ok, msg, updated_user = UserService.update_profile(
        db=db,
        user=current_user,
        req=req,
        ip_address=ip_addr
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPDATE_PROFILE_FAILED", "message": msg}
        )
    return success_response(
        data=UserProfileResponse.from_orm(updated_user).dict(),
        message=msg
    )


@router.patch("/me/password", status_code=status.HTTP_200_OK)
def change_my_password(
    req: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mengubah kata sandi pengguna dengan verifikasi kata sandi lama."""
    ip_addr = _get_client_ip(request)
    ok, msg = UserService.change_password(
        db=db,
        user=current_user,
        req=req,
        ip_address=ip_addr
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CHANGE_PASSWORD_FAILED", "message": msg}
        )
    return success_response(message=msg)
