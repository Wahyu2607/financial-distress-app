from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.user import User, UserRole, UserStatus
from backend.models.audit import AuditLog
from backend.schemas.admin import AdminUpdateUserRequest


def record_audit_log(
    db: Session,
    action: str,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Any] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Mencatat aktivitas administratif dan keamanan ke tabel audit_logs."""
    details_str = json.dumps(details) if isinstance(details, (dict, list)) else (str(details) if details else None)
    log = AuditLog(
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        target_id=target_id,
        ip_address=ip_address,
        details=details_str,
        created_at=datetime.utcnow()
    )
    db.add(log)
    try:
        db.commit()
        db.refresh(log)
    except Exception:
        db.rollback()
    return log


class AdminService:
    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Mengambil seluruh data akun pengguna untuk keperluan manajemen."""
        return db.query(User).order_by(desc(User.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Mengambil detail akun berdasarkan user ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update_user_details(
        db: Session,
        target_id: str,
        req: AdminUpdateUserRequest,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """Memperbarui informasi non-otorisasi akun oleh Admin."""
        user = db.query(User).filter(User.id == target_id).first()
        if not user:
            return False, "Pengguna tidak ditemukan", None

        changes = {}
        if req.name is not None and req.name.strip():
            changes["old_name"] = user.name
            user.name = req.name.strip()
            changes["new_name"] = user.name

        if req.institution is not None:
            user.institution = req.institution.strip()

        if req.phone_number is not None:
            user.phone_number = req.phone_number.strip()

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        record_audit_log(
            db=db,
            action="ADMIN_UPDATE_USER",
            actor_id=actor.id,
            actor_email=actor.email,
            target_id=user.id,
            details=changes,
            ip_address=ip_address
        )

        return True, "Data pengguna berhasil diperbarui", user

    @staticmethod
    def update_user_role(
        db: Session,
        target_id: str,
        new_role: str,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Mengubah role akun ('admin' atau 'user').
        Proteksi:
        - Tidak dapat mendemosi Administrator aktif terakhir menjadi user biasa.
        """
        if new_role not in (UserRole.ADMIN.value, UserRole.USER.value):
            return False, "Role yang dipilih tidak valid (harus 'admin' atau 'user')", None

        user = db.query(User).filter(User.id == target_id).first()
        if not user:
            return False, "Pengguna tidak ditemukan", None

        if user.role == new_role:
            return True, f"Role pengguna sudah '{new_role}'", user

        # Cek jika target saat ini Admin dan hendak diubah ke User
        if user.role == UserRole.ADMIN.value and new_role == UserRole.USER.value:
            active_admins = db.query(User).filter(
                User.role == UserRole.ADMIN.value,
                User.status == UserStatus.ACTIVE.value
            ).all()

            if len(active_admins) <= 1 and active_admins[0].id == user.id:
                return False, "Tindakan ditolak: Tidak dapat menurunkan role Administrator aktif terakhir dalam sistem", None

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        record_audit_log(
            db=db,
            action="CHANGE_ROLE",
            actor_id=actor.id,
            actor_email=actor.email,
            target_id=user.id,
            details={"old_role": old_role, "new_role": new_role},
            ip_address=ip_address
        )

        return True, f"Role pengguna berhasil diubah menjadi '{new_role}'", user

    @staticmethod
    def update_user_status(
        db: Session,
        target_id: str,
        new_status: str,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Mengubah status akun ('active', 'disabled', 'pending_verification').
        Proteksi:
        - Admin tidak boleh menonaktifkan akun miliknya sendiri yang sedang login.
        - Tidak dapat menonaktifkan Administrator aktif terakhir.
        """
        valid_statuses = [s.value for s in UserStatus]
        if new_status not in valid_statuses:
            return False, f"Status tidak valid. Pilihan: {', '.join(valid_statuses)}", None

        user = db.query(User).filter(User.id == target_id).first()
        if not user:
            return False, "Pengguna tidak ditemukan", None

        # 1. Cek self-disable
        if user.id == actor.id and new_status == UserStatus.DISABLED.value:
            return False, "Tindakan ditolak: Anda tidak dapat menonaktifkan akun Administrator Anda sendiri", None

        # 2. Cek last admin
        if user.role == UserRole.ADMIN.value and new_status == UserStatus.DISABLED.value:
            active_admins = db.query(User).filter(
                User.role == UserRole.ADMIN.value,
                User.status == UserStatus.ACTIVE.value
            ).all()

            if len(active_admins) <= 1 and active_admins[0].id == user.id:
                return False, "Tindakan ditolak: Tidak dapat menonaktifkan Administrator aktif terakhir dalam sistem", None

        old_status = user.status
        user.status = new_status
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        record_audit_log(
            db=db,
            action="CHANGE_STATUS",
            actor_id=actor.id,
            actor_email=actor.email,
            target_id=user.id,
            details={"old_status": old_status, "new_status": new_status},
            ip_address=ip_address
        )

        return True, f"Status akun berhasil diubah menjadi '{new_status}'", user

    @staticmethod
    def delete_user(
        db: Session,
        target_id: str,
        actor: User,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Menghapus akun pengguna dari database.
        Proteksi:
        - Admin tidak dapat menghapus akunnya sendiri.
        - Tidak dapat menghapus Administrator aktif terakhir.
        """
        user = db.query(User).filter(User.id == target_id).first()
        if not user:
            return False, "Pengguna tidak ditemukan"

        if user.id == actor.id:
            return False, "Tindakan ditolak: Anda tidak dapat menghapus akun Anda sendiri"

        if user.role == UserRole.ADMIN.value:
            active_admins = db.query(User).filter(
                User.role == UserRole.ADMIN.value,
                User.status == UserStatus.ACTIVE.value
            ).all()
            if len(active_admins) <= 1 and active_admins[0].id == user.id:
                return False, "Tindakan ditolak: Tidak dapat menghapus Administrator aktif terakhir dalam sistem"

        deleted_email = user.email
        db.delete(user)
        db.commit()

        record_audit_log(
            db=db,
            action="DELETE_USER",
            actor_id=actor.id,
            actor_email=actor.email,
            target_id=target_id,
            details={"deleted_email": deleted_email},
            ip_address=ip_address
        )

        return True, f"Akun pengguna '{deleted_email}' berhasil dihapus"

    @staticmethod
    def list_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Mengambil riwayat log audit keamanan dan aktivitas administratif."""
        return db.query(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
