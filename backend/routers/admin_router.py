from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.schemas.admin import (
    AdminUserResponse,
    AdminUpdateUserRequest,
    AdminUpdateUserRoleRequest,
    AdminUpdateUserStatusRequest,
    AuditLogResponse,
)
from backend.schemas.response import success_response
from backend.services.admin_service import AdminService
from backend.middleware.auth_middleware import require_admin

router = APIRouter(prefix="/admin", tags=["Administrasi Khusus Admin"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.get("/users", status_code=status.HTTP_200_OK)
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Melihat daftar seluruh akun pengguna terdaftar."""
    users = AdminService.list_users(db=db, skip=skip, limit=limit)
    data = [AdminUserResponse.from_orm(u).dict() for u in users]
    return success_response(data=data, message="Daftar pengguna berhasil dimuat")


@router.get("/users/{user_id}", status_code=status.HTTP_200_OK)
def get_user_detail(
    user_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Melihat detail akun pengguna tertentu."""
    user = AdminService.get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": f"Pengguna dengan ID '{user_id}' tidak ditemukan"}
        )
    return success_response(
        data=AdminUserResponse.from_orm(user).dict(),
        message="Detail akun pengguna berhasil dimuat"
    )


@router.patch("/users/{user_id}", status_code=status.HTTP_200_OK)
def update_user_info(
    user_id: str,
    req: AdminUpdateUserRequest,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Memperbarui informasi nama, instansi, atau telepon akun pengguna oleh Admin."""
    ip_addr = _get_client_ip(request)
    ok, msg, updated_user = AdminService.update_user_details(
        db=db,
        target_id=user_id,
        req=req,
        actor=current_admin,
        ip_address=ip_addr
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UPDATE_USER_FAILED", "message": msg}
        )
    return success_response(
        data=AdminUserResponse.from_orm(updated_user).dict(),
        message=msg
    )


@router.patch("/users/{user_id}/role", status_code=status.HTTP_200_OK)
def update_user_role(
    user_id: str,
    req: AdminUpdateUserRoleRequest,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Mengubah hak akses akun ('admin' atau 'user').
    Proteksi: Sistem menolak menurunkan role Administrator aktif terakhir.
    """
    ip_addr = _get_client_ip(request)
    ok, msg, updated_user = AdminService.update_user_role(
        db=db,
        target_id=user_id,
        new_role=req.role,
        actor=current_admin,
        ip_address=ip_addr
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ROLE_UPDATE_FAILED", "message": msg}
        )
    return success_response(
        data=AdminUserResponse.from_orm(updated_user).dict(),
        message=msg
    )


@router.patch("/users/{user_id}/status", status_code=status.HTTP_200_OK)
def update_user_status(
    user_id: str,
    req: AdminUpdateUserStatusRequest,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Mengubah status akun ('active', 'disabled', 'pending_verification').
    Proteksi: Admin tidak dapat menonaktifkan akunnya sendiri atau admin aktif terakhir.
    """
    ip_addr = _get_client_ip(request)
    ok, msg, updated_user = AdminService.update_user_status(
        db=db,
        target_id=user_id,
        new_status=req.status,
        actor=current_admin,
        ip_address=ip_addr
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "STATUS_UPDATE_FAILED", "message": msg}
        )
    return success_response(
        data=AdminUserResponse.from_orm(updated_user).dict(),
        message=msg
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user_account(
    user_id: str,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Menghapus akun pengguna dari database."""
    ip_addr = _get_client_ip(request)
    ok, msg = AdminService.delete_user(
        db=db,
        target_id=user_id,
        actor=current_admin,
        ip_address=ip_addr
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DELETE_USER_FAILED", "message": msg}
        )
    return success_response(message=msg)


@router.get("/audit-logs", status_code=status.HTTP_200_OK)
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Melihat catatan log aktivitas keamanan dan administratif."""
    logs = AdminService.list_audit_logs(db=db, skip=skip, limit=limit)
    data = [AuditLogResponse.from_orm(l).dict() for l in logs]
    return success_response(data=data, message="Catatan audit log berhasil dimuat")
