from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.config import settings
from backend.models.user import User, UserRole, UserStatus
from backend.models.session import UserSession
from backend.models.token import EmailVerificationToken, PasswordResetToken
from backend.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from backend.security.hashing import hash_password, verify_password, hash_token
from backend.security.tokens import create_access_token, generate_secure_token, generate_otp
from backend.security.email_validator import (
    normalize_email,
    validate_email_address,
    validate_password_strength,
    validate_username_policy,
    validate_full_name,
)
from backend.security.rate_limiter import limiter
from backend.services.email_service import EmailService
from backend.services.admin_service import record_audit_log


class AuthService:
    @staticmethod
    def register(
        db: Session,
        req: RegisterRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Registrasi akun pengguna baru dengan proteksi lengkap:
        - Validasi nama, email, username, dan kekuatan password
        - Pencegahan email dan username duplikat
        - Role OTOMATIS 'user' (tidak dapat diekskalasi menjadi admin)
        - Pengiriman kode OTP / tautan verifikasi jika REQUIRE_EMAIL_VERIFICATION aktif
        """
        # 1. Rate Limiting Registrasi per IP (Anti-Spam: max 5 pendaftaran per 15 menit per IP)
        rate_key = f"register_ip:{ip_address or 'unknown'}"
        is_limited, retry_sec = limiter.is_rate_limited(rate_key, max_requests=5, window_seconds=900)
        if is_limited:
            return False, f"Terlalu banyak permintaan pendaftaran. Silakan coba kembali dalam {retry_sec} detik.", None

        # 2. Validasi Nama Lengkap
        ok_name, err_name = validate_full_name(req.name)
        if not ok_name:
            return False, err_name, None

        # 3. Validasi Username
        ok_user, err_user = validate_username_policy(req.username)
        if not ok_user:
            return False, err_user, None

        # 4. Validasi Email (Format, Typo, Disposable, MX DNS)
        ok_email, err_email = validate_email_address(req.email)
        if not ok_email:
            return False, err_email, None

        # 5. Validasi Kekuatan Password
        ok_pwd, err_pwd = validate_password_strength(req.password)
        if not ok_pwd:
            return False, err_pwd, None

        clean_email = normalize_email(req.email)
        clean_username = req.username.strip().lower()

        # 6. Cek Keunikan Email & Username di Database
        existing_email = db.query(User).filter(User.email == clean_email).first()
        if existing_email:
            return False, "Alamat email ini sudah terdaftar. Silakan login atau gunakan menu pemulihan kata sandi.", None

        existing_user = db.query(User).filter(User.username == clean_username).first()
        if existing_user:
            return False, f"Username '{clean_username}' sudah digunakan. Silakan pilih username lain.", None

        # 7. Tentukan Status Awal Akun
        initial_status = (
            UserStatus.PENDING_VERIFICATION.value
            if settings.REQUIRE_EMAIL_VERIFICATION
            else UserStatus.ACTIVE.value
        )
        verified_at = datetime.utcnow() if not settings.REQUIRE_EMAIL_VERIFICATION else None

        # 8. Buat Pengguna Baru di Database
        new_user = User(
            name=req.name.strip(),
            email=clean_email,
            username=clean_username,
            password_hash=hash_password(req.password),
            role=UserRole.USER.value,  # MUTLAK: Publik HANYA BISA role 'user'
            status=initial_status,
            institution=req.institution.strip() if req.institution else None,
            phone_number=req.phone_number.strip() if req.phone_number else None,
            email_verified_at=verified_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            failed_login_attempts=0
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 9. Jika Verifikasi Email Diperlukan, Buat OTP & Token
        if settings.REQUIRE_EMAIL_VERIFICATION:
            otp_code = generate_otp(settings.OTP_LENGTH)
            verify_token = generate_secure_token(32)
            expires_at = datetime.utcnow() + timedelta(minutes=settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES)

            verif_record = EmailVerificationToken(
                user_id=new_user.id,
                token_hash=hash_token(verify_token),
                otp_hash=hash_token(otp_code),
                attempts=0,
                expires_at=expires_at,
                created_at=datetime.utcnow()
            )
            db.add(verif_record)
            db.commit()

            # Kirim email verifikasi
            verify_link = f"http://localhost:8000/auth/verify-email?token={verify_token}"
            EmailService.send_verification_email(
                email=clean_email,
                name=new_user.name,
                otp_code=otp_code,
                verify_link=verify_link
            )

            record_audit_log(
                db=db,
                action="REGISTER",
                actor_id=new_user.id,
                actor_email=clean_email,
                target_id=new_user.id,
                details={"status": "pending_verification"},
                ip_address=ip_address
            )

            return True, "Pendaftaran berhasil! Kode OTP verifikasi telah dikirim ke alamat email Anda. Silakan verifikasi akun Anda sebelum login.", {
                "user_id": new_user.id,
                "email": clean_email,
                "requires_verification": True
            }

        record_audit_log(
            db=db,
            action="REGISTER",
            actor_id=new_user.id,
            actor_email=clean_email,
            target_id=new_user.id,
            details={"status": "active"},
            ip_address=ip_address
        )

        return True, "Pendaftaran berhasil! Akun Anda telah aktif dan siap digunakan.", {
            "user_id": new_user.id,
            "email": clean_email,
            "requires_verification": False
        }

    @staticmethod
    def login(
        db: Session,
        req: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[TokenResponse]]:
        """
        Autentikasi login pengguna:
        - Mencegah brute force via rate limiting & lockout
        - Memverifikasi hash password
        - Menolak akun nonaktif atau belum verifikasi email
        - Menghasilkan token JWT & mencatat sesi aktif
        """
        ident = req.username_or_email.strip().lower()

        # 1. Rate Limiting Percobaan Login (Anti Brute-Force per IP/Identitas)
        rate_key = f"login_attempt:{ident}:{ip_address or 'unknown'}"
        is_limited, retry_sec = limiter.is_rate_limited(
            rate_key,
            max_requests=settings.MAX_LOGIN_FAILED_ATTEMPTS,
            window_seconds=900,
            lockout_seconds=settings.ACCOUNT_LOCKOUT_MINUTES * 60
        )
        if is_limited:
            return False, f"Terlalu banyak percobaan login gagal. Akun dibatasi sementara selama {retry_sec} detik untuk mencegah brute-force.", None

        # 2. Cari Akun berdasarkan Email ATAU Username
        user = db.query(User).filter(
            or_(User.email == ident, User.username == ident)
        ).first()

        # 3. Validasi Akun & Password
        generic_err = "Email/username atau kata sandi yang Anda masukkan salah."

        if not user:
            record_audit_log(
                db=db,
                action="LOGIN_FAILED",
                details=f"Akun tidak ditemukan untuk identitas: {ident}",
                ip_address=ip_address
            )
            return False, generic_err, None

        # Cek apakah akun sedang terkunci di database
        if user.is_locked():
            remaining = int((user.locked_until - datetime.utcnow()).total_seconds())
            return False, f"Akun terkunci sementara karena beberapa kali salah password. Silakan coba lagi dalam {max(1, remaining)} detik.", None

        # Verifikasi Password
        if not verify_password(req.password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
                record_audit_log(
                    db=db,
                    action="ACCOUNT_LOCKED",
                    actor_id=user.id,
                    actor_email=user.email,
                    target_id=user.id,
                    details=f"Akun dikunci selama {settings.ACCOUNT_LOCKOUT_MINUTES} menit karena {user.failed_login_attempts} kali gagal login",
                    ip_address=ip_address
                )
            db.commit()

            record_audit_log(
                db=db,
                action="LOGIN_FAILED",
                actor_id=user.id,
                actor_email=user.email,
                details=f"Password salah (percobaan ke-{user.failed_login_attempts})",
                ip_address=ip_address
            )
            return False, generic_err, None

        # 4. Periksa Status Akun
        if user.status == UserStatus.DISABLED.value:
            record_audit_log(
                db=db,
                action="LOGIN_BLOCKED_DISABLED",
                actor_id=user.id,
                actor_email=user.email,
                details="Percobaan login pada akun berstatus disabled",
                ip_address=ip_address
            )
            return False, "Akun Anda berstatus nonaktif. Silakan hubungi Administrator untuk informasi lebih lanjut.", None

        if user.status == UserStatus.PENDING_VERIFICATION.value:
            record_audit_log(
                db=db,
                action="LOGIN_BLOCKED_UNVERIFIED",
                actor_id=user.id,
                actor_email=user.email,
                details="Percobaan login sebelum menyelesaikan verifikasi email",
                ip_address=ip_address
            )
            return False, "Alamat email Anda belum diverifikasi. Silakan periksa kotak masuk email Anda atau minta pengiriman ulang kode verifikasi.", None

        # 5. Login Berhasil: Reset Percobaan Gagal & Perbarui Waktu Login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        limiter.reset(rate_key)

        # 6. Buat Token JWT
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_payload = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "status": user.status,
            "name": user.name,
        }
        access_token = create_access_token(token_payload, expires_delta=expires_delta)

        # 7. Simpan Sesi di Database untuk Mekanisme Pencabutan (Revocation)
        session_record = UserSession(
            user_id=user.id,
            token_hash=hash_token(access_token),
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            expires_at=datetime.utcnow() + expires_delta,
            is_revoked=False,
            created_at=datetime.utcnow()
        )
        db.add(session_record)
        db.commit()

        record_audit_log(
            db=db,
            action="LOGIN_SUCCESS",
            actor_id=user.id,
            actor_email=user.email,
            target_id=user.id,
            details={"role": user.role},
            ip_address=ip_address
        )

        resp = TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            name=user.name,
            email=user.email,
            username=user.username,
            role=user.role,
            status=user.status,
        )
        return True, "Login berhasil", resp

    @staticmethod
    def logout(db: Session, token: str, user: User, ip_address: Optional[str] = None) -> bool:
        """Mencabut sesi token aktif (Session Revocation / Logout)."""
        t_hash = hash_token(token)
        session = db.query(UserSession).filter(
            UserSession.token_hash == t_hash,
            UserSession.user_id == user.id
        ).first()

        if session:
            session.is_revoked = True
            db.commit()

        record_audit_log(
            db=db,
            action="LOGOUT",
            actor_id=user.id,
            actor_email=user.email,
            target_id=user.id,
            details="Sesi berhasil diakhiri / dicabut",
            ip_address=ip_address
        )
        return True

    @staticmethod
    def verify_email_otp(
        db: Session,
        email: str,
        otp_code: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Memverifikasi akun menggunakan 6-digit kode OTP."""
        clean_email = normalize_email(email)
        user = db.query(User).filter(User.email == clean_email).first()
        if not user:
            return False, "Akun dengan alamat email tersebut tidak ditemukan."

        if user.status == UserStatus.ACTIVE.value and user.email_verified_at is not None:
            return True, "Alamat email ini sudah terverifikasi sebelumnya. Silakan login."

        # Ambil token verifikasi aktif terbaru
        verif = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at == None
        ).order_by(EmailVerificationToken.created_at.desc()).first()

        if not verif or not verif.is_valid():
            return False, "Kode OTP verifikasi tidak ditemukan atau telah kedaluwarsa. Silakan minta kode baru."

        # Cek batas percobaan OTP (max 5 kali)
        if verif.attempts >= settings.OTP_MAX_ATTEMPTS:
            return False, "Anda telah melampaui batas maksimal percobaan verifikasi. Silakan minta kode baru."

        verif.attempts += 1
        expected_hash = hash_token(otp_code.strip())

        if verif.otp_hash != expected_hash:
            db.commit()
            return False, f"Kode OTP tidak cocok. Sisa percobaan: {settings.OTP_MAX_ATTEMPTS - verif.attempts}."

        # Verifikasi Berhasil
        verif.used_at = datetime.utcnow()
        user.status = UserStatus.ACTIVE.value
        user.email_verified_at = datetime.utcnow()
        db.commit()

        record_audit_log(
            db=db,
            action="EMAIL_VERIFIED_OTP",
            actor_id=user.id,
            actor_email=user.email,
            target_id=user.id,
            details="Email berhasil diverifikasi via OTP",
            ip_address=ip_address
        )

        return True, "Alamat email Anda berhasil diverifikasi! Akun kini aktif dan dapat digunakan untuk login."

    @staticmethod
    def verify_email_token(db: Session, token: str, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """Memverifikasi akun menggunakan token kriptografis dari tautan email."""
        t_hash = hash_token(token.strip())
        verif = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token_hash == t_hash,
            EmailVerificationToken.used_at == None
        ).first()

        if not verif or not verif.is_valid():
            return False, "Tautan verifikasi tidak valid atau telah kedaluwarsa. Silakan minta tautan baru."

        user = verif.user
        verif.used_at = datetime.utcnow()
        user.status = UserStatus.ACTIVE.value
        user.email_verified_at = datetime.utcnow()
        db.commit()

        record_audit_log(
            db=db,
            action="EMAIL_VERIFIED_TOKEN",
            actor_id=user.id,
            actor_email=user.email,
            target_id=user.id,
            details="Email berhasil diverifikasi via tautan link",
            ip_address=ip_address
        )

        return True, "Alamat email Anda berhasil diverifikasi! Akun kini aktif dan dapat digunakan untuk login."

    @staticmethod
    def resend_verification(db: Session, email: str, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """Mengirim ulang kode OTP dan tautan verifikasi email dengan rate limiting cooldown."""
        clean_email = normalize_email(email)

        # Rate Limiting Resend OTP (Anti-Spam)
        rate_key = f"resend_verif:{clean_email}"
        is_limited, retry_sec = limiter.is_rate_limited(
            rate_key,
            max_requests=1,
            window_seconds=settings.RESEND_COOLDOWN_SECONDS
        )
        if is_limited:
            return False, f"Harap tunggu {retry_sec} detik sebelum meminta pengiriman ulang kode verifikasi."

        user = db.query(User).filter(User.email == clean_email).first()
        # Jika akun tidak ada atau sudah aktif, tetap beri respons aman tanpa bocorkan database
        if not user or user.status == UserStatus.ACTIVE.value:
            return True, "Jika alamat email terdaftar dan belum diverifikasi, kode verifikasi baru telah dikirimkan."

        # Nonaktifkan token lama
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.used_at == None
        ).update({"used_at": datetime.utcnow()})

        # Buat OTP & Token baru
        otp_code = generate_otp(settings.OTP_LENGTH)
        verify_token = generate_secure_token(32)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES)

        verif_record = EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(verify_token),
            otp_hash=hash_token(otp_code),
            attempts=0,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        db.add(verif_record)
        db.commit()

        verify_link = f"http://localhost:8000/auth/verify-email?token={verify_token}"
        EmailService.send_verification_email(
            email=clean_email,
            name=user.name,
            otp_code=otp_code,
            verify_link=verify_link
        )

        record_audit_log(
            db=db,
            action="RESEND_VERIFICATION",
            actor_id=user.id,
            actor_email=clean_email,
            target_id=user.id,
            details="Pengiriman ulang kode OTP diminta",
            ip_address=ip_address
        )

        return True, "Kode verifikasi baru telah dikirim ke alamat email Anda."

    @staticmethod
    def request_password_reset(db: Session, email: str, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """Membuat token reset password sekali pakai dan mengirim tautan pemulihan."""
        clean_email = normalize_email(email)
        user = db.query(User).filter(User.email == clean_email).first()

        safe_msg = "Jika alamat email tersebut terdaftar di sistem kami, instruksi pemulihan kata sandi telah dikirimkan."

        if not user or user.status == UserStatus.DISABLED.value:
            return True, safe_msg

        # Nonaktifkan token reset lama
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at == None
        ).update({"used_at": datetime.utcnow()})

        reset_token = generate_secure_token(32)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(reset_token),
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        db.add(reset_record)
        db.commit()

        reset_link = f"http://localhost:8000/auth/reset-password?token={reset_token}"
        EmailService.send_password_reset_email(
            email=clean_email,
            name=user.name,
            reset_link=reset_link
        )

        record_audit_log(
            db=db,
            action="REQUEST_PASSWORD_RESET",
            actor_id=user.id,
            actor_email=clean_email,
            target_id=user.id,
            details="Permintaan reset kata sandi diajukan",
            ip_address=ip_address
        )

        return True, safe_msg

    @staticmethod
    def reset_password(
        db: Session,
        token: str,
        new_password: str,
        confirm_password: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Mereset kata sandi menggunakan token reset sekali pakai yang sah."""
        if new_password != confirm_password:
            return False, "Konfirmasi kata sandi tidak cocok."

        ok_pwd, err_pwd = validate_password_strength(new_password)
        if not ok_pwd:
            return False, err_pwd

        t_hash = hash_token(token.strip())
        record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == t_hash,
            PasswordResetToken.used_at == None
        ).first()

        if not record or not record.is_valid():
            return False, "Tautan reset kata sandi tidak valid atau telah kedaluwarsa. Silakan ajukan permintaan baru."

        user = record.user
        record.used_at = datetime.utcnow()
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()

        # Cabut seluruh sesi aktif lama pengguna
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_revoked == False
        ).update({"is_revoked": True})

        db.commit()

        record_audit_log(
            db=db,
            action="RESET_PASSWORD_SUCCESS",
            actor_id=user.id,
            actor_email=user.email,
            target_id=user.id,
            details="Kata sandi berhasil direset menggunakan token pemulihan",
            ip_address=ip_address
        )

        return True, "Kata sandi Anda berhasil diperbarui. Silakan login menggunakan kata sandi baru Anda."
