"""
==============================================================================
UNIT TEST SUITE: SISTEM AUTENTIKASI DAN OTORISASI
Pytest Test Cases for Financial Distress Prediction System
==============================================================================
"""

import pytest
from unittest.mock import MagicMock, patch

from src.auth import (
    validate_email,
    validate_password,
    validate_username,
    validate_full_name,
    sign_in_user,
    sign_in_admin,
    sign_up_user,
    update_user_profile,
    admin_update_user_status,
    admin_update_user_role,
)


class TestInputValidation:
    """Pengujian aturan validasi input pada lapisan server / backend."""

    def test_validate_email_valid(self):
        valid_emails = [
            "analis@perusahaan.co.id",
            "dosen@kampus.ac.id",
            "user.name+tag@gmail.com",
            "bursa@idx.co.id",
        ]
        for email in valid_emails:
            is_valid, err = validate_email(email)
            assert is_valid is True, f"Harusnya valid: {email}, error: {err}"
            assert err == ""

    def test_validate_email_invalid(self):
        invalid_emails = [
            ("", "Alamat email wajib diisi."),
            ("bukan-email", "Format alamat email tidak valid"),
            ("user@domain", "Domain email tidak valid"),
            ("temp@mailinator.com", "Domain email sementara/disposable tidak diizinkan"),
            ("test@tempmail.com", "Domain email sementara/disposable tidak diizinkan"),
            ("wahyu@laman.com", "bukan penyedia email resmi"),
            ("wahyu@rata.com", "bukan penyedia email resmi"),
        ]
        for email, expected_fragment in invalid_emails:
            is_valid, err = validate_email(email)
            assert is_valid is False
            assert expected_fragment in err

    def test_validate_password_strength(self):
        # Valid: >=8 char, lowercase, uppercase, digit/symbol
        valid_passwords = [
            "Password123",
            "Rahasia#2026",
            "DistressAI_99",
            "Keuangan@Aman1",
        ]
        for pwd in valid_passwords:
            is_valid, err = validate_password(pwd)
            assert is_valid is True, f"Harusnya lolos kebijakan: {pwd}, error: {err}"

        # Invalid cases
        assert validate_password("")[0] is False
        assert "minimal 8 karakter" in validate_password("Pass1")[1]
        assert "minimal 1 huruf besar" in validate_password("password123")[1]
        assert "minimal 1 huruf kecil" in validate_password("PASSWORD123")[1]
        assert "minimal 1 angka atau simbol" in validate_password("PasswordTanpaAngka")[1]

    def test_validate_username_rules(self):
        # Valid usernames
        assert validate_username("john_doe")[0] is True
        assert validate_username("analis99")[0] is True
        assert validate_username("andi_finance")[0] is True

        # Invalid length
        assert validate_username("ab")[0] is False
        assert "antara 3 hingga 30" in validate_username("ab")[1]
        assert validate_username("a" * 31)[0] is False

        # Invalid characters
        assert validate_username("john doe")[0] is False
        assert validate_username("user@name")[0] is False
        assert validate_username("user-name")[0] is False

        # Forbidden system usernames
        forbidden = ["admin", "administrator", "root", "superuser", "system"]
        for f in forbidden:
            is_val, err = validate_username(f)
            assert is_val is False, f"Username {f} harusnya dilarang"
            assert "dilindungi" in err

    def test_validate_full_name(self):
        assert validate_full_name("Ahmad Dahlan")[0] is True
        assert validate_full_name("")[0] is False
        assert validate_full_name("A")[0] is False
        assert validate_full_name("Administrator")[0] is False


class TestAuthorizationAndRoleProtection:
    """Pengujian pemisahan Authentication dan Authorization (Admin vs User)."""

    @patch("src.auth.get_supabase_client")
    def test_user_cannot_login_through_admin_portal(self, mock_get_client):
        """Memastikan akun dengan role 'user' DITOLAK saat mencoba login via portal Admin."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock auth success
        mock_user = MagicMock()
        mock_user.id = "uuid-123-regular-user"
        mock_client.auth.sign_in_with_password.return_value.user = mock_user

        # Mock database profiles: role is 'user', NOT 'admin'
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "uuid-123-regular-user",
            "email": "user@distress.ai",
            "role": "user",
            "status": "active"
        }]

        success, user, profile, err = sign_in_admin("user@distress.ai", "Password123")

        # Harus ditolak
        assert success is False
        assert user is None
        assert profile is None
        assert "tidak memiliki wewenang Administrator" in err
        # Sesi Supabase harus dibersihkan seketika
        mock_client.auth.sign_out.assert_called_once()

    @patch("src.auth.get_supabase_client")
    def test_disabled_user_login_rejected(self, mock_get_client):
        """Memastikan pengguna berstatus 'disabled' langsung ditolak dan sesi di-logout."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_user = MagicMock()
        mock_user.id = "uuid-disabled-user"
        mock_client.auth.sign_in_with_password.return_value.user = mock_user

        # Profile status is 'disabled'
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "id": "uuid-disabled-user",
            "email": "disabled@distress.ai",
            "role": "user",
            "status": "disabled"
        }]

        success, user, profile, err = sign_in_user("disabled@distress.ai", "Password123")
        assert success is False
        assert "nonaktif" in err
        mock_client.auth.sign_out.assert_called_once()

    @patch("src.auth.get_supabase_client")
    def test_admin_cannot_disable_self(self, mock_get_client):
        """Admin yang sedang aktif tidak boleh menonaktifkan akunnya sendiri."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        admin_id = "uuid-admin-current"
        success, msg = admin_update_user_status(
            target_user_id=admin_id,
            new_status="disabled",
            current_admin_id=admin_id
        )
        assert success is False
        assert "tidak dapat menonaktifkan akun Administrator Anda sendiri" in msg

    @patch("src.auth.admin_get_all_users")
    @patch("src.auth.get_user_profile")
    @patch("src.auth.get_supabase_client")
    def test_last_admin_protected_from_demotion(self, mock_get_client, mock_get_prof, mock_get_all):
        """Sistem harus menolak menurunkan role jika hanya tersisa 1 Admin aktif."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        target_admin_id = "uuid-target-admin"
        caller_admin_id = "uuid-caller-admin"

        # Target adalah admin
        mock_get_prof.return_value = {"id": target_admin_id, "role": "admin", "status": "active"}

        # Hanya ada 1 admin aktif dalam sistem
        mock_get_all.return_value = [
            {"id": target_admin_id, "role": "admin", "status": "active"},
            {"id": "uuid-user-1", "role": "user", "status": "active"},
        ]

        success, msg = admin_update_user_role(
            target_user_id=target_admin_id,
            new_role="user",
            current_admin_id=caller_admin_id
        )
        assert success is False
        assert "Tidak dapat menurunkan role Administrator terakhir" in msg

    @patch("src.auth.admin_get_all_users")
    @patch("src.auth.get_user_profile")
    @patch("src.auth.get_supabase_client")
    def test_last_admin_protected_from_disabling(self, mock_get_client, mock_get_prof, mock_get_all):
        """Sistem harus menolak menonaktifkan Admin jika hanya tersisa 1 Admin aktif."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        target_admin_id = "uuid-target-admin"
        caller_admin_id = "uuid-caller-admin"

        mock_get_prof.return_value = {"id": target_admin_id, "role": "admin", "status": "active"}
        mock_get_all.return_value = [
            {"id": target_admin_id, "role": "admin", "status": "active"},
            {"id": "uuid-user-1", "role": "user", "status": "active"},
        ]

        success, msg = admin_update_user_status(
            target_user_id=target_admin_id,
            new_status="disabled",
            current_admin_id=caller_admin_id
        )
        assert success is False
        assert "Tidak dapat menonaktifkan Administrator aktif terakhir" in msg

    @patch("src.auth.get_supabase_client")
    def test_user_profile_update_prevents_privilege_escalation(self, mock_get_client):
        """
        Pengguna biasa yang memanggil update_user_profile TIDAK BOLEH
        dapat menyisipkan 'role' atau 'status' untuk menaikkan hak akses.
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        user_id = "uuid-regular-user"
        malicious_payload = {
            "full_name": "Budi Santoso",
            "role": "admin",          # Coba eskalasi privilege ke admin!
            "status": "active",       # Coba ubah status
            "phone_number": "08123456789",
        }

        # Mock update response
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": user_id}]

        success, msg = update_user_profile(user_id, malicious_payload)

        assert success is True
        # Periksa argumen yang diteruskan ke table.update()
        call_args = mock_client.table.return_value.update.call_args[0][0]
        assert "role" not in call_args, "Privilege escalation terdeteksi! 'role' harus disanitasi!"
        assert "status" not in call_args, "'status' harus disanitasi!"
        assert call_args["full_name"] == "Budi Santoso"
        assert call_args["phone_number"] == "08123456789"


class TestDatabaseAuthAndApproval:
    """Pengujian alur persetujuan akun admin (approval), status pending, dan proteksi brute-force."""

    def test_new_user_registration_is_pending_by_default(self):
        from src.database import add_new_user, get_user_profile, verify_user_detailed, update_user_status

        test_u = "test_pending_user"
        test_email = "test.pending@gmail.com"
        res = add_new_user(
            username=test_u,
            password="PasswordKuat#2026",
            email=test_email,
            full_name="User Pending Uji",
            status="pending"
        )
        assert res.success is True
        assert "menunggu persetujuan" in res.message.lower()

        # Profil harus berstatus 'pending'
        prof = get_user_profile(test_u)
        assert prof is not None
        assert prof.get("status") == "pending"

        # Coba login saat masih pending harus DITOLAK
        ok_login, role, msg, _ = verify_user_detailed(test_u, "PasswordKuat#2026")
        assert ok_login is False
        assert "Menunggu Persetujuan" in msg

        # Admin menyetujui akun -> status 'active'
        ok_appr, msg_appr = update_user_status(test_u, "active")
        assert ok_appr is True

        # Sekarang login harus BERHASIL
        ok_login_after, role_after, msg_after, _ = verify_user_detailed(test_u, "PasswordKuat#2026")
        assert ok_login_after is True
        assert role_after == "user"

    def test_admin_cannot_be_disabled(self):
        from src.database import update_user_status
        ok, msg = update_user_status("admin", "disabled")
        assert ok is False
        assert "dilindungi" in msg

    def test_brute_force_lockout_after_failed_attempts(self):
        from src.database import add_new_user, verify_user_detailed, update_user_status

        lock_u = "test_lockout_user"
        add_new_user(
            username=lock_u,
            password="PasswordKuat#2026",
            email="lockout@gmail.com",
            full_name="User Lockout Uji",
            status="active"
        )

        # 4 kali percobaan salah -> masih belum terkunci
        for i in range(4):
            ok, _, msg, _ = verify_user_detailed(lock_u, "SalahPassword")
            assert ok is False
            assert "Sisa percobaan" in msg

        # Percobaan ke-5 salah -> akun dikunci
        ok_5, _, msg_5, _ = verify_user_detailed(lock_u, "SalahPassword")
        assert ok_5 is False
        assert "dikunci sementara selama 15 menit" in msg_5

        # Meskipun sekarang memasukkan password yang benar, tetap ditolak karena terkunci!
        ok_locked, _, msg_locked, _ = verify_user_detailed(lock_u, "PasswordKuat#2026")
        assert ok_locked is False
        assert "Akun dikunci sementara" in msg_locked

    def test_derive_username_takes_full_name_without_underline_or_email(self):
        from src.database import derive_username

        # Memastikan username mengambil Nama Lengkap TANPA tambahan garis bawah (_) atau awalan email
        u1 = derive_username("Wahyu Pamungkas", "wahyu@gmail.com")
        assert u1 == "Wahyu Pamungkas"
        assert "_" not in u1
        assert "@" not in u1

        u2 = derive_username("Prof. Bambang Subagyo", "bambang@ugm.ac.id")
        assert u2 == "Prof. Bambang Subagyo"
        assert "_" not in u2

        u3 = derive_username("Sarah Wijaya", "sarah123@yahoo.com")
        assert u3 == "Sarah Wijaya"
        assert "_" not in u3

    def test_domain_based_auto_approval_for_institutional_emails(self):
        from src.database import add_new_user, get_user_profile, is_institutional_email, verify_user_detailed

        # 1. Cek deteksi domain instansi
        assert is_institutional_email("analis@idx.co.id") is True
        assert is_institutional_email("dosen@ugm.ac.id") is True
        assert is_institutional_email("pejabat@kemenkeu.go.id") is True
        assert is_institutional_email("user@gmail.com") is False

        # 2. Pendaftaran dengan email instansi -> Langsung ACTIVE otomatis tanpa kode akses
        inst_u = "Analis Bursa Resmi"
        res = add_new_user(
            username=inst_u,
            password="PasswordKuat#2026",
            email="analis@bursa.co.id",
            full_name=inst_u,
            passcode="",
        )
        assert res.success is True
        assert "disetujui otomatis" in res.message.lower()

        prof = get_user_profile(inst_u)
        assert prof is not None
        assert prof.get("status") == "active"

        # Dapat langsung masuk tanpa hambatan dan tanpa persetujuan admin
        ok_login, role, _, _ = verify_user_detailed(inst_u, "PasswordKuat#2026")
        assert ok_login is True
        assert role == "user"

    def test_smart_detection_and_auto_approval_for_valid_public_emails_without_passcode(self):
        from src.database import add_new_user, get_user_profile, verify_user_detailed

        name_u = "User Penguji Publik"

        # Pendaftaran dengan email @gmail.com yang valid langsung disetujui otomatis (ACTIVE) TANPA KODE AKSES
        res_ok = add_new_user(
            username=name_u,
            password="PasswordKuat#2026",
            email="user.pendaftar@gmail.com",
            full_name=name_u,
        )
        assert res_ok.success is True
        assert "terverifikasi valid" in res_ok.message.lower() or "berhasil" in res_ok.message.lower()

        prof = get_user_profile(name_u)
        assert prof is not None
        assert prof.get("status") == "active"

        # Dapat langsung masuk saat itu juga menggunakan Nama Lengkap ATAU Email tanpa perlu persetujuan admin
        ok_login_name, role_name, _, _ = verify_user_detailed(name_u, "PasswordKuat#2026")
        assert ok_login_name is True
        assert role_name == "user"

        ok_login_email, role_email, _, _ = verify_user_detailed("user.pendaftar@gmail.com", "PasswordKuat#2026")
        assert ok_login_email is True
        assert role_email == "user"

    def test_smart_detection_rejects_invalid_or_typo_emails(self):
        from src.database import add_new_user

        # 1. Salah ketik domain Google (nama@google.com bukan layanan email) -> Ditolak
        res_bad1 = add_new_user(
            username="Test Bad Google",
            password="PasswordKuat#2026",
            email="wahyu@google.com",
            full_name="Wahyu Google",
        )
        assert res_bad1.success is False
        assert "google.com" in res_bad1.message.lower()

        # 2. Salah ketik typo domain (nama@gamil.com) -> Ditolak
        res_bad2 = add_new_user(
            username="Test Typo Gmail",
            password="PasswordKuat#2026",
            email="wahyu@gamil.com",
            full_name="Wahyu Typo",
        )
        assert res_bad2.success is False
        assert "salah ketik" in res_bad2.message.lower()

        # 3. Domain media sosial (nama@facebook.com) -> Ditolak
        res_bad3 = add_new_user(
            username="Test Medsos",
            password="PasswordKuat#2026",
            email="wahyu@facebook.com",
            full_name="Wahyu Medsos",
        )
        assert res_bad3.success is False
        assert "bukan penyedia email" in res_bad3.message.lower()

        # 4. Domain email sementara (disposable) -> Ditolak
        res_bad4 = add_new_user(
            username="Test Temp",
            password="PasswordKuat#2026",
            email="wahyu@tempmail.com",
            full_name="Wahyu Temp",
        )
        assert res_bad4.success is False
        assert "sementara" in res_bad4.message.lower()

    def test_manual_admin_creation_and_role_management(self):
        from src.database import (
            add_new_user,
            get_user_profile,
            verify_user_detailed,
            update_user_role,
        )

        admin_name = "Hendro Administrator"
        admin_email = "hendro.admin@gmail.com"
        admin_pwd = "AdminSecure#2026"

        # 1. Admin dapat membuat akun administrator baru secara manual
        res = add_new_user(
            username=admin_name,
            password=admin_pwd,
            role="admin",
            email=admin_email,
            full_name=admin_name,
            institution="Kantor Pusat Keuangan",
            status="active",
        )
        assert res.success is True
        assert "administrator" in res.message.lower() or "berhasil" in res.message.lower()

        # Profil akun tersimpan dengan role 'admin'
        prof = get_user_profile(admin_name)
        assert prof is not None
        assert prof.get("role") == "admin"
        assert prof.get("status") == "active"

        # Verifikasi login akun admin baru berhasil dengan role 'admin'
        ok, role, msg, _ = verify_user_detailed(admin_name, admin_pwd)
        assert ok is True
        assert role == "admin"

        # 2. Pengubahan role pengguna (Promote / Demote)
        ok_demote, _ = update_user_role(admin_name, "user")
        assert ok_demote is True
        prof_after = get_user_profile(admin_name)
        assert prof_after.get("role") == "user"

        ok_promote, _ = update_user_role(admin_name, "admin")
        assert ok_promote is True
        prof_promo = get_user_profile(admin_name)
        assert prof_promo.get("role") == "admin"

        # 3. Superadmin utama 'admin' dilindungi dari penurunan hak akses
        ok_super, err_super = update_user_role("admin", "user")
        assert ok_super is False
        assert "dilindungi" in err_super.lower()

        # 4. Pembuatan admin baru dengan username persis 'admin' ditolak agar tidak bentrok
        res_conflict = add_new_user(
            username="admin",
            password=admin_pwd,
            role="admin",
            email="conflict@gmail.com",
            full_name="Admin",
        )
        assert res_conflict.success is False
        assert "sudah digunakan" in res_conflict.message.lower()
