from __future__ import annotations

import argparse
import getpass
import sys
from datetime import datetime
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import SessionLocal, init_database
from backend.models.user import User, UserRole, UserStatus
from backend.security.hashing import hash_password
from backend.security.email_validator import (
    normalize_email,
    validate_email_address,
    validate_password_strength,
    validate_username_policy,
    validate_full_name,
)
from backend.services.admin_service import record_audit_log


def bootstrap_admin(
    email: str = "",
    username: str = "",
    name: str = "",
    password: str = "",
) -> bool:
    """
    Membuat akun Administrator pertama secara aman melalui proses bootstrap.
    Kredensial tidak ditulis permanen di source code, melainkan diambil dari
    argumen CLI, prompt interaktif, atau environment variables.
    """
    db: Session = SessionLocal()
    try:
        # 1. Pastikan tabel sudah diinisialisasi
        init_database()

        # Ambil nilai default dari environment jika tidak dipasok dari argumen
        target_email = email.strip() or settings.INITIAL_ADMIN_EMAIL
        target_username = username.strip() or settings.INITIAL_ADMIN_USERNAME
        target_name = name.strip() or settings.INITIAL_ADMIN_FULLNAME
        target_password = password.strip() or (settings.INITIAL_ADMIN_PASSWORD or "")

        # Jika password belum disediakan, minta input interaktif dengan masking
        if not target_password:
            print("==================================================================")
            print("PROSES BOOTSTRAP PEMBUATAN AKUN ADMINISTRATOR PERTAMA")
            print("==================================================================")
            if not target_name:
                target_name = input("Nama Lengkap Admin   : ").strip()
            if not target_email:
                target_email = input("Email Admin          : ").strip()
            if not target_username:
                target_username = input("Username Admin       : ").strip()
            
            while True:
                p1 = getpass.getpass("Kata Sandi Admin     : ")
                p2 = getpass.getpass("Ulangi Kata Sandi    : ")
                if p1 != p2:
                    print("❌ Konfirmasi kata sandi tidak cocok. Silakan coba lagi.\n")
                    continue
                ok_pwd, err_pwd = validate_password_strength(p1)
                if not ok_pwd:
                    print(f"❌ {err_pwd}\n")
                    continue
                target_password = p1
                break

        # 2. Validasi input
        clean_email = normalize_email(target_email)
        clean_username = target_username.strip().lower()

        ok_n, err_n = validate_full_name(target_name)
        if not ok_n:
            print(f"❌ Error Nama: {err_n}")
            return False

        ok_u, err_u = validate_username_policy(clean_username)
        # Khusus bootstrap superadmin awal, izinkan username 'admin'
        if not ok_u and clean_username != "admin":
            print(f"❌ Error Username: {err_u}")
            return False

        ok_e, err_e = validate_email_address(clean_email, verify_dns=False)
        if not ok_e:
            print(f"❌ Error Email: {err_e}")
            return False

        ok_p, err_p = validate_password_strength(target_password)
        if not ok_p:
            print(f"❌ Error Password: {err_p}")
            return False

        # 3. Cek apakah admin dengan email atau username sudah ada (Idempotent Check)
        existing_user = db.query(User).filter(
            (User.email == clean_email) | (User.username == clean_username)
        ).first()

        now = datetime.utcnow()

        if existing_user:
            if existing_user.role == UserRole.ADMIN.value:
                print(f"ℹ️ Akun Administrator '{clean_email}' ({clean_username}) sudah ada dalam sistem.")
                # Update password jika diperintahkan
                existing_user.password_hash = hash_password(target_password)
                existing_user.status = UserStatus.ACTIVE.value
                existing_user.email_verified_at = now
                existing_user.updated_at = now
                db.commit()
                print("✅ Kata sandi Administrator berhasil disinkronkan.")
                return True
            else:
                print(f"❌ Pengguna dengan email/username tersebut sudah ada dengan role '{existing_user.role}'.")
                return False

        # 4. Buat Akun Admin Baru
        admin_user = User(
            name=target_name,
            email=clean_email,
            username=clean_username,
            password_hash=hash_password(target_password),
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
            institution="Sistem Administrasi Internal",
            email_verified_at=now,
            created_at=now,
            updated_at=now,
            failed_login_attempts=0
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        record_audit_log(
            db=db,
            action="BOOTSTRAP_ADMIN",
            actor_id=admin_user.id,
            actor_email=admin_user.email,
            target_id=admin_user.id,
            details="Akun Administrator pertama berhasil dibuat via CLI bootstrap"
        )

        print("\n==================================================================")
        print("✅ AKUN ADMINISTRATOR PERTAMA BERHASIL DIBUAT DENGAN AMAN!")
        print(f"Nama     : {admin_user.name}")
        print(f"Email    : {admin_user.email}")
        print(f"Username : {admin_user.username}")
        print(f"Role     : {admin_user.role.upper()}")
        print(f"Status   : {admin_user.status.upper()}")
        print("==================================================================\n")
        return True

    except Exception as exc:
        db.rollback()
        print(f"❌ Gagal membuat akun administrator: {exc}")
        return False
    finally:
        db.close()


def list_users_cli():
    """Menampilkan daftar akun pengguna di database secara ringkas."""
    db: Session = SessionLocal()
    try:
        init_database()
        users = db.query(User).all()
        print("\n" + "=" * 95)
        print(f"{'ID':<38} | {'USERNAME':<16} | {'ROLE':<8} | {'STATUS':<15} | {'EMAIL'}")
        print("=" * 95)
        for u in users:
            print(f"{u.id:<38} | {u.username:<16} | {u.role:<8} | {u.status:<15} | {u.email}")
        print("=" * 95 + f"\nTotal: {len(users)} pengguna terdaftar.\n")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="CLI Manajemen Backend Autentikasi")
    subparsers = parser.add_subparsers(dest="command", help="Perintah yang tersedia")

    # Subcommand: init-db
    subparsers.add_parser("init-db", help="Inisialisasi skema tabel database")

    # Subcommand: create-admin
    admin_parser = subparsers.add_parser("create-admin", help="Membuat akun Administrator pertama")
    admin_parser.add_argument("--name", help="Nama lengkap admin", default="")
    admin_parser.add_argument("--email", help="Alamat email admin", default="")
    admin_parser.add_argument("--username", help="Username admin", default="")
    admin_parser.add_argument("--password", help="Kata sandi admin (opsional, disarankan via prompt)", default="")

    # Subcommand: list-users
    subparsers.add_parser("list-users", help="Menampilkan daftar akun terdaftar")

    args = parser.parse_args()

    if args.command == "init-db":
        init_database()
        print("✅ Skema database berhasil diinisialisasi.")
    elif args.command == "create-admin":
        bootstrap_admin(
            email=args.email,
            username=args.username,
            name=args.name,
            password=args.password
        )
    elif args.command == "list-users":
        list_users_cli()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
