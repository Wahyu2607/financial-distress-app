from __future__ import annotations

from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.models.session import UserSession
from backend.schemas.user import UpdateProfileRequest, ChangePasswordRequest
from backend.security.hashing import verify_password, hash_password
from backend.security.email_validator import validate_password_strength, validate_full_name
from backend.services.admin_service import record_audit_log


class UserService:
    @staticmethod
    def update_profile(
        db: Session,
        user: User,
        req: UpdateProfileRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, User]:
        """
        Memperbarui data profil milik pengguna sendiri.
        Kolom 'role' dan 'status' sama sekali tidak diizinkan diubah oleh user.
        """
        changes = {}

        if req.name is not None:
            clean_name = req.name.strip()
            ok_name, err_name = validate_full_name(clean_name)
            if not ok_name:
                return False, err_name, user
            changes["name"] = clean_name
            user.name = clean_name

        if req.institution is not None:
            user.institution = req.institution.strip()
            changes["institution"] = user.institution

        if req.phone_number is not None:
            user.phone_number = req.phone_number.strip()
            changes["phone_number"] = user.phone_number

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        record_audit_log(
            db=db,
            action="UPDATE_PROFILE",
            actor_id=user.id,
            actor_email=user.email,
            target_id=user.id,
            details=changes,
            ip_address=ip_address
        )

        return True, "Profil berhasil diperbarui", user

    @staticmethod
    def change_password(
        db: Session,
        user: User,
        req: ChangePasswordRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Mengubah kata sandi pengguna dengan verifikasi kata sandi lama.
        Setelah kata sandi diubah, seluruh sesi lama otomatis dicabut untuk keamanan.
        """
        # 1. Verifikasi kata sandi lama
        if not verify_password(req.old_password, user.password_hash):
            record_audit_log(
                db=db,
                action="CHANGE_PASSWORD_FAILED",
                actor_id=user.id,
                actor_email=user.email,
                details="Verifikasi password lama gagal",
                ip_address=ip_address
            )
            return False, "Kata sandi lama yang Anda masukkan salah"

        # 2. Cek kesesuaian konfirmasi password
        if req.new_password != req.confirm_password:
            return False, "Konfirmasi kata sandi baru tidak cocok"

        # 3. Validasi kekuatan password baru
        ok_pwd, err_pwd = validate_password_strength(req.new_password)
        if not ok_pwd:
            return False, err_pwd

        # 4. Password baru tidak boleh sama dengan password lama
        if verify_password(req.new_password, user.password_hash):
            return False, "Kata sandi baru tidak boleh sama dengan kata sandi lama Anda"

        # 5. Update password hash
        user.password_hash = hash_password(req.new_password)
        user.updated_at = datetime.utcnow()

        # 6. Cabut seluruh sesi aktif lama pengguna (Revoke Sessions)
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_revoked == False
        ).update({"is_revoked": True})

        db.commit()

        record_audit_log(
            db=db,
            action="CHANGE_PASSWORD_SUCCESS",
            actor_id=user.id,
            actor_email=user.email,
            target_id=user.id,
            details="Kata sandi berhasil diubah dan seluruh sesi lama dicabut",
            ip_address=ip_address
        )

        return True, "Kata sandi berhasil diperbarui. Silakan login kembali dengan kata sandi baru Anda."
