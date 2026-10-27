from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.supabase_client import get_supabase_client, is_supabase_configured

# ==============================================================================
# 1. ATURAN DAN VALIDASI INPUT PENGGUNA (SERVER-SIDE VALIDATION)
# ==============================================================================

DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "throwawaymail.com",
    "guerrillamail.com", "yopmail.com", "trashmail.com", "sharklasers.com",
    "dispostable.com", "getairmail.com", "fake.com", "test.com", "example.com"
}

FORBIDDEN_USERNAMES = {
    "admin", "administrator", "root", "superuser", "system", "moderator",
    "support", "owner", "guest", "anonymous", "null", "undefined"
}


def validate_email(email: str) -> Tuple[bool, str]:
    """Validasi format dan domain alamat email (Wajib Google/Yahoo/Outlook atau Instansi Resmi)."""
    if not email:
        return False, "Alamat email wajib diisi."
    
    clean_email = email.strip().lower()
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, clean_email):
        return False, "Format alamat email tidak valid (contoh: nama@gmail.com atau nama@instansi.ac.id)."
    
    domain = clean_email.split("@")[1].strip()
    if domain in DISPOSABLE_DOMAINS:
        return False, "Domain email sementara/disposable tidak diizinkan demi keamanan akun."
    
    if "." not in domain or len(domain.split(".")[-1]) < 2:
        return False, "Domain email tidak valid."

    TRUSTED_PUBLIC_DOMAINS = {
        "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.id",
        "outlook.com", "hotmail.com", "live.com", "icloud.com"
    }

    INSTITUTION_EXTENSIONS = (
        ".ac.id", ".edu", ".edu.id",    # Kampus / Akademik
        ".go.id", ".gov",               # Lembaga Pemerintah
        ".co.id",                       # Korporat Resmi Indonesia (cth: idx.co.id, astra.co.id)
        ".or.id", ".sch.id", ".mil.id"  # Organisasi & Sekolah
    )

    if not (domain in TRUSTED_PUBLIC_DOMAINS or any(domain.endswith(sfx) for sfx in INSTITUTION_EXTENSIONS)):
        return False, f"Domain '@{domain}' bukan penyedia email resmi yang valid. Harap gunakan alamat email dari Google (@gmail.com) atau email resmi instansi/kampus Anda (.ac.id, .co.id, .go.id)."

    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validasi kebijakan keamanan kata sandi:
    - Minimal 8 karakter
    - Mengandung huruf besar dan kecil
    - Mengandung angka atau simbol
    """
    if not password:
        return False, "Kata sandi wajib diisi."
    
    if len(password) < 8:
        return False, "Kata sandi harus minimal 8 karakter."
    
    if not re.search(r"[a-z]", password):
        return False, "Kata sandi harus mengandung minimal 1 huruf kecil."
    
    if not re.search(r"[A-Z]", password):
        return False, "Kata sandi harus mengandung minimal 1 huruf besar."
    
    if not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Kata sandi harus mengandung minimal 1 angka atau simbol unik."
    
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validasi username:
    - Panjang 3-30 karakter
    - Karakter alfanumerik dan garis bawah (underscore) saja
    - Tidak boleh menggunakan kata terlarang (admin, root, dsb.)
    """
    if not username:
        return False, "Username wajib diisi."
    
    clean_u = username.strip().lower()
    if len(clean_u) < 3 or len(clean_u) > 30:
        return False, "Username harus memiliki panjang antara 3 hingga 30 karakter."
    
    if not re.match(r"^[a-zA-Z0-9_]+$", clean_u):
        return False, "Username hanya boleh mengandung huruf, angka, dan garis bawah (_)."
    
    if clean_u in FORBIDDEN_USERNAMES:
        return False, "Username tersebut dilindungi dan tidak dapat digunakan."
    
    return True, ""


def validate_full_name(full_name: str) -> Tuple[bool, str]:
    """Validasi nama lengkap pengguna."""
    if not full_name:
        return False, "Nama lengkap wajib diisi."
    
    clean_name = full_name.strip()
    if len(clean_name) < 2:
        return False, "Nama lengkap harus minimal 2 karakter."
    
    if any(k in clean_name.lower() for k in ["administrator", "root", "superuser"]):
        return False, "Nama lengkap tidak boleh mengandung gelar terlarang sistem."
    
    return True, ""


# ==============================================================================
# 2. OPERASI AUTENTIKASI PENGGUNA (SUPABASE AUTH)
# ==============================================================================

def sign_in_user(email: str, password: str) -> Tuple[bool, Optional[Any], Optional[Dict[str, Any]], str]:
    """
    Melakukan login untuk pengguna biasa (role 'user').
    Memverifikasi:
    1. Kredensial via Supabase Auth
    2. Status akun 'active' di tabel profiles
    3. Role pengguna
    """
    client = get_supabase_client()
    if not client:
        return False, None, None, "Layanan Supabase belum dikonfigurasikan. Periksa file .streamlit/secrets.toml."

    val_e, err_e = validate_email(email)
    if not val_e:
        return False, None, None, err_e
    
    if not password:
        return False, None, None, "Kata sandi wajib diisi."

    try:
        auth_resp = client.auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password
        })
        user = auth_resp.user
        if not user:
            return False, None, None, "Email atau kata sandi tidak cocok."

        # Ambil profil pengguna dari tabel profiles
        prof_resp = client.table("profiles").select("*").eq("id", user.id).execute()
        profile = prof_resp.data[0] if prof_resp.data else None

        if not profile:
            # Fallback jika trigger delay
            profile = {
                "id": user.id,
                "email": user.email,
                "username": user.user_metadata.get("username", user.email.split("@")[0]),
                "full_name": user.user_metadata.get("full_name", "Pengguna"),
                "role": "user",
                "status": "active"
            }

        # Periksa status akun
        if profile.get("status") == "disabled":
            # Segera bersihkan sesi jika akun nonaktif
            try:
                client.auth.sign_out()
            except Exception:
                pass
            return False, None, None, "Akun Anda berstatus nonaktif. Silakan hubungi Administrator untuk informasi lebih lanjut."

        return True, user, profile, ""

    except Exception as exc:
        msg = str(exc)
        if "Invalid login credentials" in msg or "invalid_credentials" in msg:
            return False, None, None, "Email atau kata sandi yang Anda masukkan salah."
        if "Email not confirmed" in msg:
            return False, None, None, "Alamat email Anda belum diverifikasi. Harap periksa kotak masuk email Anda."
        return False, None, None, f"Gagal masuk: {msg}"


def sign_in_admin(email: str, password: str) -> Tuple[bool, Optional[Any], Optional[Dict[str, Any]], str]:
    """
    Melakukan login khusus Administrator (role 'admin').
    Memverifikasi identitas via Supabase Auth dan memastikan hak akses 'admin'
    dari tabel public.profiles yang tepercaya.
    """
    client = get_supabase_client()
    if not client:
        return False, None, None, "Layanan Supabase belum dikonfigurasikan."

    val_e, err_e = validate_email(email)
    if not val_e:
        return False, None, None, err_e
    
    if not password:
        return False, None, None, "Kata sandi Administrator wajib diisi."

    try:
        auth_resp = client.auth.sign_in_with_password({
            "email": email.strip().lower(),
            "password": password
        })
        user = auth_resp.user
        if not user:
            return False, None, None, "Email atau kata sandi Administrator salah."

        # Ambil profil terverifikasi dari database
        prof_resp = client.table("profiles").select("*").eq("id", user.id).execute()
        profile = prof_resp.data[0] if prof_resp.data else None

        if not profile or profile.get("role") != "admin":
            # Jika bukan Admin, bersihkan sesi Supabase seketika!
            try:
                client.auth.sign_out()
            except Exception:
                pass
            return False, None, None, "Akses ditolak: Akun Anda tidak memiliki wewenang Administrator."

        if profile.get("status") != "active":
            try:
                client.auth.sign_out()
            except Exception:
                pass
            return False, None, None, "Akses ditolak: Akun Administrator ini berstatus nonaktif."

        return True, user, profile, ""

    except Exception as exc:
        msg = str(exc)
        if "Invalid login credentials" in msg:
            return False, None, None, "Email atau kata sandi Administrator salah."
        return False, None, None, f"Otentikasi Administrator gagal: {msg}"


def sign_up_user(
    email: str,
    password: str,
    confirm_password: str,
    full_name: str,
    username: str,
    agreed_terms: bool = True
) -> Tuple[bool, Optional[Any], str, bool]:
    """
    Mendaftarkan pengguna baru via Supabase Auth:
    - Validasi nama, email, username, dan password secara ketat di backend.
    - Menetapkan role 'user' secara default (Role 'admin' TIDAK PERNAH diterima dari pendaftaran).
    - Mengembalikan: (success, user, message, is_email_confirmation_required)
    """
    client = get_supabase_client()
    if not client:
        return False, None, "Layanan Supabase belum dikonfigurasikan.", False

    if not agreed_terms:
        return False, None, "Anda harus menyetujui syarat & ketentuan layanan untuk mendaftar.", False

    # Validasi nama lengkap
    val_fn, err_fn = validate_full_name(full_name)
    if not val_fn:
        return False, None, err_fn, False

    # Validasi username
    val_u, err_u = validate_username(username)
    if not val_u:
        return False, None, err_u, False

    # Validasi email
    val_e, err_e = validate_email(email)
    if not val_e:
        return False, None, err_e, False

    # Validasi password
    val_p, err_p = validate_password(password)
    if not val_p:
        return False, None, err_p, False

    if password != confirm_password:
        return False, None, "Konfirmasi kata sandi tidak cocok dengan kata sandi yang dimasukkan.", False

    clean_email = email.strip().lower()
    clean_username = username.strip().lower()
    clean_fullname = full_name.strip()

    try:
        # Cek apakah username sudah dipakai di tabel profiles
        check_u = client.table("profiles").select("id").eq("username", clean_username).execute()
        if check_u.data:
            return False, None, f"Username '{clean_username}' sudah digunakan. Silakan pilih username lain.", False

        # Daftarkan pengguna via Supabase Auth
        # Metadata 'role' TIDAK dikirim atau diabaikan oleh trigger database
        signup_resp = client.auth.sign_up({
            "email": clean_email,
            "password": password,
            "options": {
                "data": {
                    "full_name": clean_fullname,
                    "username": clean_username
                }
            }
        })

        user = signup_resp.user
        if not user:
            return False, None, "Gagal membuat akun pengguna.", False

        # Periksa apakah email confirmation diperlukan
        needs_confirm = False
        if signup_resp.session is None and user.confirmed_at is None:
            needs_confirm = True

        msg = "Pendaftaran berhasil! Akun Anda telah siap digunakan."
        if needs_confirm:
            msg = "Pendaftaran berhasil! Tautan konfirmasi telah dikirim ke email Anda. Silakan verifikasi email Anda sebelum masuk."

        return True, user, msg, needs_confirm

    except Exception as exc:
        msg = str(exc)
        if "User already registered" in msg or "already registered" in msg:
            return False, None, "Alamat email ini sudah terdaftar. Silakan gunakan menu Masuk atau Lupa Password.", False
        return False, None, f"Pendaftaran gagal: {msg}", False


def sign_out_user() -> bool:
    """Melakukan proses logout pengguna pada client Supabase."""
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
            return True
        except Exception:
            pass
    return True


def request_password_reset(email: str, redirect_url: Optional[str] = None) -> Tuple[bool, str]:
    """Mengirim email instruksi reset password menggunakan Supabase Auth."""
    client = get_supabase_client()
    if not client:
        return False, "Layanan Supabase belum dikonfigurasikan."

    val_e, err_e = validate_email(email)
    if not val_e:
        return False, err_e

    try:
        options = {}
        if redirect_url:
            options["redirect_to"] = redirect_url
        client.auth.reset_password_for_email(email.strip().lower(), options)
        return True, "Jika email tersebut terdaftar di sistem, tautan pemulihan kata sandi telah dikirim ke kotak masuk Anda."
    except Exception as exc:
        # Untuk keamanan, berikan pesan aman agar tidak membocorkan enumerasi email
        return True, "Jika email tersebut terdaftar di sistem, tautan pemulihan kata sandi telah dikirim ke kotak masuk Anda."


def update_user_password(new_password: str) -> Tuple[bool, str]:
    """Mengubah kata sandi pengguna yang sedang dalam sesi aktif."""
    client = get_supabase_client()
    if not client:
        return False, "Layanan Supabase belum dikonfigurasikan."

    val_p, err_p = validate_password(new_password)
    if not val_p:
        return False, err_p

    try:
        client.auth.update_user({"password": new_password})
        return True, "Kata sandi Anda berhasil diperbarui."
    except Exception as exc:
        return False, f"Gagal memperbarui kata sandi: {exc}"


# ==============================================================================
# 3. PENGELOLAAN PROFIL PENGGUNA (PROFILES)
# ==============================================================================

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Mengambil data profil pengguna berdasarkan UUID auth.users.id."""
    client = get_supabase_client()
    if not client or not user_id:
        return None

    try:
        resp = client.table("profiles").select("*").eq("id", user_id).execute()
        if resp.data:
            return resp.data[0]
    except Exception as exc:
        print(f"[Profile Query Error] {exc}")
    return None


def update_user_profile(user_id: str, updates: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Memperbarui profil pengguna biasa:
    Hanya mengizinkan kolom profil non-sensitif (mencegah eskalasi hak akses).
    Kolom 'role' dan 'status' DIHAPUS secara mutlak jika ada di payload.
    """
    client = get_supabase_client()
    if not client or not user_id:
        return False, "Koneksi database tidak tersedia."

    ALLOWED_FIELDS = {
        "full_name", "phone_number", "institution", "user_type",
        "position", "city", "bio", "avatar_data"
    }

    sanitized_updates = {k: v for k, v in updates.items() if k in ALLOWED_FIELDS}

    if not sanitized_updates:
        return False, "Tidak ada data profil yang valid untuk diperbarui."

    if "full_name" in sanitized_updates:
        val_fn, err_fn = validate_full_name(sanitized_updates["full_name"])
        if not val_fn:
            return False, err_fn

    try:
        resp = client.table("profiles").update(sanitized_updates).eq("id", user_id).execute()
        if resp.data:
            return True, "Profil berhasil diperbarui."
        return False, "Gagal memperbarui profil pengguna."
    except Exception as exc:
        return False, f"Kesalahan saat memperbarui profil: {exc}"


# ==============================================================================
# 4. OPERASI KHUSUS ADMINISTRATOR (ADMIN USER MANAGEMENT)
# ==============================================================================

def admin_get_all_users() -> List[Dict[str, Any]]:
    """Mengambil daftar seluruh profil pengguna untuk audit dan manajemen di Dashboard Admin."""
    client = get_supabase_client()
    if not client:
        return []

    try:
        resp = client.table("profiles").select("*").order("created_at", desc=True).execute()
        return resp.data or []
    except Exception as exc:
        print(f"[Admin Get Users Error] {exc}")
        return []


def admin_update_user_status(target_user_id: str, new_status: str, current_admin_id: str = "") -> Tuple[bool, str]:
    """
    Mengubah status akun pengguna ('active' atau 'disabled').
    Proteksi Keamanan:
    - Administrator tidak boleh menonaktifkan akunnya sendiri saat sedang login.
    - Sistem tidak boleh menonaktifkan Admin terakhir.
    """
    if new_status not in ("active", "disabled"):
        return False, "Status yang dipilih tidak valid (harus 'active' atau 'disabled')."

    if target_user_id == current_admin_id and new_status == "disabled":
        return False, "Tindakan ditolak: Anda tidak dapat menonaktifkan akun Administrator Anda sendiri."

    client = get_supabase_client()
    if not client:
        return False, "Layanan Supabase tidak tersedia."

    try:
        # Cek profil target
        target_prof = get_user_profile(target_user_id)
        if not target_prof:
            return False, "Pengguna target tidak ditemukan."

        # Jika target adalah admin dan hendak dinonaktifkan, periksa apakah dia admin terakhir
        if target_prof.get("role") == "admin" and new_status == "disabled":
            all_users = admin_get_all_users()
            active_admins = [u for u in all_users if u.get("role") == "admin" and u.get("status") == "active"]
            if len(active_admins) <= 1:
                return False, "Tindakan ditolak: Tidak dapat menonaktifkan Administrator aktif terakhir dalam sistem."

        resp = client.table("profiles").update({"status": new_status}).eq("id", target_user_id).execute()
        if resp.data:
            status_text = "diaktifkan" if new_status == "active" else "dinonaktifkan"
            return True, f"Akun pengguna berhasil {status_text}."
        return False, "Gagal memperbarui status akun."
    except Exception as exc:
        return False, f"Terjadi kesalahan: {exc}"


def admin_update_user_role(target_user_id: str, new_role: str, current_admin_id: str = "") -> Tuple[bool, str]:
    """
    Mengubah hak akses pengguna ('admin' atau 'user').
    Proteksi Keamanan:
    - Tidak boleh menurunkan role Administrator terakhir menjadi User.
    """
    if new_role not in ("admin", "user"):
        return False, "Role tidak valid (harus 'admin' atau 'user')."

    client = get_supabase_client()
    if not client:
        return False, "Layanan Supabase tidak tersedia."

    try:
        target_prof = get_user_profile(target_user_id)
        if not target_prof:
            return False, "Pengguna target tidak ditemukan."

        # Cek jika target saat ini adalah Admin dan hendak diturunkan ke User
        if target_prof.get("role") == "admin" and new_role == "user":
            all_users = admin_get_all_users()
            active_admins = [u for u in all_users if u.get("role") == "admin" and u.get("status") == "active"]
            if len(active_admins) <= 1:
                return False, "Tindakan ditolak: Tidak dapat menurunkan role Administrator terakhir dalam sistem."

        resp = client.table("profiles").update({"role": new_role}).eq("id", target_user_id).execute()
        if resp.data:
            return True, f"Role pengguna berhasil diubah menjadi '{new_role}'."
        return False, "Gagal memperbarui role akun."
    except Exception as exc:
        return False, f"Terjadi kesalahan: {exc}"
