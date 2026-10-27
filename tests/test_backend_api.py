"""
==============================================================================
AUTOMATED TEST SUITE: BACKEND AUTHENTICATION, AUTHORIZATION & SECURITY
Pytest Test Cases for Financial Distress Backend Auth API
==============================================================================
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.models.user import User, UserRole, UserStatus
from backend.models.token import EmailVerificationToken, PasswordResetToken
from backend.models.audit import AuditLog
from backend.security.hashing import hash_password, verify_password, hash_token
from backend.security.tokens import create_access_token
from backend.security.email_validator import validate_email_address, validate_password_strength

# In-memory SQLite untuk pengujian terisolasi
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Membuat tabel database baru di memori untuk setiap sesi pengujian."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Menyediakan TestClient FastAPI dengan dependency injection database terisolasi."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. PENGUJIAN REGISTRASI & KEAMANAN PASSWORD (SECTION 1 & 13)
# ==============================================================================

class TestRegistrationSecurity:
    def test_user_registration_success(self, client, db_session):
        """User dapat melakukan registrasi dan akun tersimpan dengan role 'user'."""
        payload = {
            "name": "Budi Santoso",
            "email": "budi.santoso@perusahaan.co.id",
            "username": "budi_santoso",
            "password": "PasswordKuat#2026",
            "institution": "PT Industri Keuangan",
            "phone_number": "081234567890"
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True

        # Verifikasi di database
        user = db_session.query(User).filter(User.username == "budi_santoso").first()
        assert user is not None
        assert user.name == "Budi Santoso"
        assert user.email == "budi.santoso@perusahaan.co.id"
        # 1. Pastikan role SELALU 'user', bukan admin
        assert user.role == UserRole.USER.value
        # 2. Pastikan password disimpan dalam bentuk hash (TIDAK BOLEH PLAINTEXT)
        assert user.password_hash != "PasswordKuat#2026"
        assert verify_password("PasswordKuat#2026", user.password_hash) is True

    def test_registration_blocks_privilege_escalation(self, client, db_session):
        """User mencoba menyisipkan role='admin' saat registrasi publik harus ditolak/diabaikan."""
        payload = {
            "name": "Hacker WannaBe",
            "email": "hacker@gmail.com",
            "username": "hacker_pro",
            "password": "PasswordKuat#2026",
            "role": "admin"  # Upaya ekskalasi hak akses
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 201
        user = db_session.query(User).filter(User.username == "hacker_pro").first()
        assert user is not None
        # Role harus tetap 'user'
        assert user.role == UserRole.USER.value

    def test_registration_rejects_fake_and_unrecognized_domains(self, client):
        """Domain email sembarangan/tidak resmi seperti @laman.com dan @rata.com wajib ditolak."""
        for fake_email in ["wahyu@laman.com", "wahyu@rata.com", "user@test.com", "andi@palsu.net"]:
            payload = {
                "name": "Akun Palsu",
                "email": fake_email,
                "username": f"user_{fake_email.split('@')[0]}",
                "password": "PasswordKuat#2026"
            }
            resp = client.post("/auth/register", json=payload)
            assert resp.status_code == 400
            assert "bukan penyedia email resmi yang valid" in resp.json()["message"]

    def test_registration_duplicate_email_rejected(self, client, db_session):
        """Email yang sudah terdaftar tidak dapat didaftarkan kembali."""
        payload = {
            "name": "Andi Wijaya",
            "email": "andi@perusahaan.co.id",
            "username": "andi_w",
            "password": "PasswordKuat#2026"
        }
        r1 = client.post("/auth/register", json=payload)
        assert r1.status_code == 201

        # Coba daftar ulang dengan email yang sama tapi username beda
        payload2 = payload.copy()
        payload2["username"] = "andi_w2"
        r2 = client.post("/auth/register", json=payload2)
        assert r2.status_code == 400
        assert "sudah terdaftar" in r2.json()["message"]

    def test_registration_rejects_disposable_email(self, client):
        """Email sekali pakai (disposable) langsung ditolak oleh backend."""
        payload = {
            "name": "Anonim",
            "email": "anonim@mailinator.com",
            "username": "anonim_mail",
            "password": "PasswordKuat#2026"
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "disposable" in resp.json()["message"]

    def test_registration_rejects_weak_password(self, client):
        """Password lemah (kurang dari 8 char atau tanpa variasi huruf/angka) ditolak."""
        payload = {
            "name": "User Lemah",
            "email": "user.lemah@gmail.com",
            "username": "user_lemah",
            "password": "lemah"
        }
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 400
        assert "minimal 8 karakter" in resp.json()["message"]


# ==============================================================================
# 2. PENGUJIAN VERIFIKASI EMAIL (SECTION 13)
# ==============================================================================

class TestEmailVerification:
    def test_email_verification_via_otp(self, client, db_session):
        """Verifikasi menggunakan kode OTP 6 digit berhasil mengaktifkan akun."""
        # 1. Registrasi akun
        payload = {
            "name": "Citra Lestari",
            "email": "citra@kampus.ac.id",
            "username": "citra_l",
            "password": "PasswordKuat#2026"
        }
        client.post("/auth/register", json=payload)

        user = db_session.query(User).filter(User.username == "citra_l").first()
        assert user.status == UserStatus.PENDING_VERIFICATION.value

        # 2. Ambil token verifikasi yang dibuat di database
        verif = db_session.query(EmailVerificationToken).filter(EmailVerificationToken.user_id == user.id).first()
        assert verif is not None

        # Simulasi verifikasi dengan OTP salah
        r_fail = client.post("/auth/verify-email", json={"email": "citra@kampus.ac.id", "otp_code": "000000"})
        assert r_fail.status_code == 400

        # Buat OTP yang cocok
        test_otp = "123456"
        verif.otp_hash = hash_token(test_otp)
        db_session.commit()

        # Verifikasi dengan OTP benar
        r_ok = client.post("/auth/verify-email", json={"email": "citra@kampus.ac.id", "otp_code": test_otp})
        assert r_ok.status_code == 200
        assert r_ok.json()["success"] is True

        # Akun sekarang harus ACTIVE
        db_session.refresh(user)
        assert user.status == UserStatus.ACTIVE.value
        assert user.email_verified_at is not None

    def test_unverified_user_cannot_login(self, client, db_session):
        """Pengguna yang belum verifikasi email ditolak saat login."""
        user = User(
            name="Unverified User",
            email="unverified@gmail.com",
            username="unverified_user",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.USER.value,
            status=UserStatus.PENDING_VERIFICATION.value
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post("/auth/login", json={
            "username_or_email": "unverified@gmail.com",
            "password": "PasswordKuat#2026"
        })
        assert resp.status_code == 401
        assert "belum diverifikasi" in resp.json()["message"]


# ==============================================================================
# 3. PENGUJIAN LOGIN, SESI & PENCABUTAN SESI / LOGOUT (SECTION 2 & 7)
# ==============================================================================

class TestAuthenticationAndSession:
    def test_login_success_and_logout(self, client, db_session):
        """User aktif dapat login dan mengakhiri sesi (logout)."""
        user = User(
            name="Dodi Prakoso",
            email="dodi@perusahaan.co.id",
            username="dodi_p",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
            email_verified_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()

        # 1. Login dengan email
        r_login = client.post("/auth/login", json={
            "username_or_email": "dodi@perusahaan.co.id",
            "password": "PasswordKuat#2026"
        })
        assert r_login.status_code == 200
        token_data = r_login.json()["data"]
        token = token_data["access_token"]
        assert token is not None

        # 2. Akses /auth/me dengan token
        headers = {"Authorization": f"Bearer {token}"}
        r_me = client.get("/auth/me", headers=headers)
        assert r_me.status_code == 200
        assert r_me.json()["data"]["username"] == "dodi_p"

        # 3. Logout
        r_logout = client.post("/auth/logout", headers=headers)
        assert r_logout.status_code == 200

        # 4. Akses ulang dengan token yang telah di-logout harus DITOLAK (Session Revoked)
        r_revoked = client.get("/auth/me", headers=headers)
        assert r_revoked.status_code == 401
        assert "dicabut" in r_revoked.json()["message"] or "diakhiri" in r_revoked.json()["message"]

    def test_disabled_user_rejected_from_login(self, client, db_session):
        """Pengguna dengan status 'disabled' langsung ditolak saat login."""
        user = User(
            name="Akun Diblokir",
            email="blokir@gmail.com",
            username="akun_blokir",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.USER.value,
            status=UserStatus.DISABLED.value
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post("/auth/login", json={
            "username_or_email": "akun_blokir",
            "password": "PasswordKuat#2026"
        })
        assert resp.status_code == 401
        assert "nonaktif" in resp.json()["message"]


# ==============================================================================
# 4. PENGUJIAN OTORISASI RBAC (USER VS ADMIN) & IDOR (SECTION 3 & 5)
# ==============================================================================

class TestAuthorizationAndRBAC:
    def test_regular_user_cannot_access_admin_endpoints(self, client, db_session):
        """User biasa DILARANG mengakses endpoint khusus Admin (403 Forbidden)."""
        user = User(
            name="Regular User",
            email="regular@perusahaan.co.id",
            username="regular_user",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
            email_verified_at=datetime.utcnow()
        )
        db_session.add(user)
        db_session.commit()

        # Login user biasa
        r_login = client.post("/auth/login", json={
            "username_or_email": "regular@perusahaan.co.id",
            "password": "PasswordKuat#2026"
        })
        token = r_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Coba akses GET /admin/users
        r_admin = client.get("/admin/users", headers=headers)
        assert r_admin.status_code == 403
        assert r_admin.json()["error"]["code"] == "FORBIDDEN"

        # Coba akses GET /admin/audit-logs
        r_audit = client.get("/admin/audit-logs", headers=headers)
        assert r_audit.status_code == 403

    def test_admin_can_access_admin_endpoints(self, client, db_session):
        """Administrator memiliki hak akses untuk melihat data pengguna & audit logs."""
        admin = User(
            name="Super Admin",
            email="admin@distress.ai",
            username="admin_utama",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
            email_verified_at=datetime.utcnow()
        )
        db_session.add(admin)
        db_session.commit()

        r_login = client.post("/auth/login", json={
            "username_or_email": "admin@distress.ai",
            "password": "PasswordKuat#2026"
        })
        token = r_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        r_users = client.get("/admin/users", headers=headers)
        assert r_users.status_code == 200
        assert r_users.json()["success"] is True

        r_logs = client.get("/admin/audit-logs", headers=headers)
        assert r_logs.status_code == 200

    def test_last_admin_protection_from_demotion_and_disable(self, client, db_session):
        """Sistem menolak menurunkan role atau menonaktifkan Admin aktif terakhir."""
        admin = User(
            name="Satu Satunya Admin",
            email="sole.admin@distress.ai",
            username="sole_admin",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
            email_verified_at=datetime.utcnow()
        )
        db_session.add(admin)
        db_session.commit()

        r_login = client.post("/auth/login", json={
            "username_or_email": "sole.admin@distress.ai",
            "password": "PasswordKuat#2026"
        })
        token = r_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Coba demosi diri sendiri / admin terakhir ke role 'user'
        r_demote = client.patch(f"/admin/users/{admin.id}/role", json={"role": "user"}, headers=headers)
        assert r_demote.status_code == 400
        assert "terakhir" in r_demote.json()["message"]

        # 2. Coba nonaktifkan akun diri sendiri
        r_disable = client.patch(f"/admin/users/{admin.id}/status", json={"status": "disabled"}, headers=headers)
        assert r_disable.status_code == 400
        assert "sendiri" in r_disable.json()["message"]

    def test_audit_logs_recorded_on_admin_actions(self, client, db_session):
        """Setiap perubahan status dan role tercatat di tabel audit_logs."""
        admin = User(
            name="Auditor Admin",
            email="auditor@distress.ai",
            username="auditor_admin",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.ADMIN.value,
            status=UserStatus.ACTIVE.value,
            email_verified_at=datetime.utcnow()
        )
        target_user = User(
            name="Target User",
            email="target@perusahaan.co.id",
            username="target_user",
            password_hash=hash_password("PasswordKuat#2026"),
            role=UserRole.USER.value,
            status=UserStatus.ACTIVE.value,
            email_verified_at=datetime.utcnow()
        )
        db_session.add_all([admin, target_user])
        db_session.commit()

        # Login admin
        r_login = client.post("/auth/login", json={
            "username_or_email": "auditor@distress.ai",
            "password": "PasswordKuat#2026"
        })
        token = r_login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Ubah role target user menjadi admin
        client.patch(f"/admin/users/{target_user.id}/role", json={"role": "admin"}, headers=headers)

        # Cek apakah audit log tercatat
        log = db_session.query(AuditLog).filter(
            AuditLog.action == "CHANGE_ROLE",
            AuditLog.target_id == target_user.id
        ).first()
        assert log is not None
        assert log.actor_id == admin.id
