from __future__ import annotations

import os
import re
import math
import json
import hashlib
import hmac
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Tuple
import pandas as pd

try:
    import streamlit as st
except ImportError:
    st = None

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "financial_distress.db"

# ==============================================================================
# 1. KEAMANAN PASSWORD (PBKDF2-HMAC-SHA256 WITH SALT)
# ==============================================================================
def hash_password(password: str) -> str:
    """Mengamankan password menggunakan standar industri PBKDF2-HMAC-SHA256 dengan salt unik."""
    if not password:
        return ""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Memverifikasi password terhadap hash tersimpan, dengan kompatibilitas mundur plaintext."""
    if not stored_hash or not password:
        return False
    if stored_hash.startswith("pbkdf2:sha256:"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 3:
                _, salt, key_hex = parts
                test_key = hashlib.pbkdf2_hmac(
                    "sha256",
                    password.encode("utf-8"),
                    salt.encode("utf-8"),
                    100000,
                )
                return hmac.compare_digest(test_key.hex(), key_hex)
        except Exception:
            return False
    # Kompatibilitas mundur jika password lama masih plaintext
    return hmac.compare_digest(password, stored_hash)


# ==============================================================================
# 2. DETEKSI & KONEKSI BASIS DATA (POSTGRESQL CLOUD vs SQLITE LOKAL)
# ==============================================================================
def get_database_url() -> Optional[str]:
    """Mendapatkan connection string database dari Streamlit Secrets atau Environment Variables."""
    # 1. Cek dari streamlit secrets jika running di Streamlit
    if st is not None:
        try:
            if hasattr(st, "secrets"):
                if "DATABASE_URL" in st.secrets:
                    return str(st.secrets["DATABASE_URL"])
                if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
                    pg_conf = st.secrets["connections"]["postgresql"]
                    if isinstance(pg_conf, dict) and "url" in pg_conf:
                        return str(pg_conf["url"])
                    elif isinstance(pg_conf, str):
                        return pg_conf
        except Exception:
            pass

    # 2. Cek dari environment variable
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    return None


def is_postgres_available() -> Tuple[bool, Optional[str]]:
    """Mengecek apakah PostgreSQL URL dikonfigurasi dan driver tersedia."""
    db_url = get_database_url()
    if not db_url:
        return False, None

    # Normalisasi format URI postgres:// ke postgresql:// untuk SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    try:
        import sqlalchemy
        return True, db_url
    except ImportError:
        return False, None


def get_db_info() -> dict:
    """Mengembalikan informasi konfigurasi database aktif untuk tampilan audit/status."""
    is_pg, pg_url = is_postgres_available()
    if is_pg and pg_url:
        # Mask password di URL untuk keamanan
        masked_url = pg_url
        if "@" in pg_url and "://" in pg_url:
            proto, rest = pg_url.split("://", 1)
            auth, host_db = rest.split("@", 1)
            user = auth.split(":", 1)[0] if ":" in auth else auth
            masked_url = f"{proto}://{user}:****@{host_db}"
        return {
            "type": "PostgreSQL (Cloud Database)",
            "provider": "Supabase / Neon / Managed Postgres",
            "url": masked_url,
            "persistent": True,
            "status": "Aktif & Siap Produksi",
            "notes": "Data riwayat dan akun pengguna tersimpan aman di cloud dan TIDAK akan hilang saat website di-restart / di-hosting."
        }
    else:
        return {
            "type": "SQLite (Lokal)",
            "provider": "SQLite File System",
            "url": str(DB_PATH),
            "persistent": True,
            "status": "Aktif (Lokal / Mode Pengembangan)",
            "notes": "Sangat cepat untuk lokal. Untuk hosting publik (Streamlit Cloud), sambungkan ke Supabase/Neon melalui .streamlit/secrets.toml agar data permanen."
        }


def _get_sqlite_conn():
    """Koneksi SQLite dengan proteksi concurrency timeout dan mode WAL."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


# ==============================================================================
# 3. INITIALISASI TABEL & SEED DATA
# ==============================================================================
class AuthResult:
    """Hasil operasi autentikasi yang dapat diakses sebagai Boolean maupun Tuple (success, message)."""
    def __init__(self, success: bool, message: str):
        self.success = bool(success)
        self.message = str(message)

    def __bool__(self) -> bool:
        return self.success

    def __iter__(self):
        return iter((self.success, self.message))

    def __getitem__(self, index):
        return (self.success, self.message)[index]

    def __repr__(self):
        return f"AuthResult(success={self.success}, message='{self.message}')"


# Domain email sekali pakai yang wajib diblokir
DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "throwawaymail.com",
    "guerrillamail.com", "yopmail.com", "trashmail.com", "sharklasers.com",
    "dispostable.com", "getairmail.com", "fake.com", "test.com", "example.com"
}

# Kamus deteksi salah ketik / typo domain email populer
EMAIL_TYPO_MAP = {
    # Typo Google / Gmail (termasuk contoh spesifik: nama@google.com)
    "google.com": "Domain '@google.com' bukan layanan penyedia email publik. Layanan email resmi Google adalah '@gmail.com'.",
    "gmai.com": "Salah ketik pada domain '@gmai.com'. Gunakan '@gmail.com'.",
    "gamil.com": "Salah ketik pada domain '@gamil.com'. Gunakan '@gmail.com'.",
    "gmial.com": "Salah ketik pada domain '@gmial.com'. Gunakan '@gmail.com'.",
    "gmaill.com": "Salah ketik pada domain '@gmaill.com'. Gunakan '@gmail.com'.",
    "gmaild.com": "Salah ketik pada domain '@gmaild.com'. Gunakan '@gmail.com'.",
    "gmaik.com": "Salah ketik pada domain '@gmaik.com'. Gunakan '@gmail.com'.",
    "gmail.con": "Salah ketik pada domain '@gmail.con'. Gunakan '@gmail.com'.",
    "gmail.co": "Salah ketik pada domain '@gmail.co'. Gunakan '@gmail.com'.",
    "gmai.co": "Salah ketik pada domain '@gmai.co'. Gunakan '@gmail.com'.",
    "gmal.com": "Salah ketik pada domain '@gmal.com'. Gunakan '@gmail.com'.",
    "gmeil.com": "Salah ketik pada domain '@gmeil.com'. Gunakan '@gmail.com'.",
    "gemail.com": "Salah ketik pada domain '@gemail.com'. Gunakan '@gmail.com'.",
    "gmaul.com": "Salah ketik pada domain '@gmaul.com'. Gunakan '@gmail.com'.",
    "gmail.comm": "Salah ketik pada domain '@gmail.comm'. Gunakan '@gmail.com'.",
    "googlemail.con": "Salah ketik pada domain '@googlemail.con'. Gunakan '@gmail.com' atau '@googlemail.com'.",
    # Typo Yahoo
    "yaho.com": "Salah ketik pada domain '@yaho.com'. Gunakan '@yahoo.com'.",
    "yahooo.com": "Salah ketik pada domain '@yahooo.com'. Gunakan '@yahoo.com'.",
    "yhaoo.com": "Salah ketik pada domain '@yhaoo.com'. Gunakan '@yahoo.com'.",
    "yaho.co.id": "Salah ketik pada domain '@yaho.co.id'. Gunakan '@yahoo.co.id'.",
    "yahooo.co.id": "Salah ketik pada domain '@yahooo.co.id'. Gunakan '@yahoo.co.id'.",
    "yahoo.con": "Salah ketik pada domain '@yahoo.con'. Gunakan '@yahoo.com'.",
    # Typo Microsoft (Hotmail / Outlook)
    "hotmial.com": "Salah ketik pada domain '@hotmial.com'. Gunakan '@hotmail.com'.",
    "hotmai.com": "Salah ketik pada domain '@hotmai.com'. Gunakan '@hotmail.com'.",
    "outlok.com": "Salah ketik pada domain '@outlok.com'. Gunakan '@outlook.com'.",
    "outloo.com": "Salah ketik pada domain '@outloo.com'. Gunakan '@outlook.com'.",
    "outluk.com": "Salah ketik pada domain '@outluk.com'. Gunakan '@outlook.com'.",
    "outlook.con": "Salah ketik pada domain '@outlook.con'. Gunakan '@outlook.com'.",
    # Typo Apple
    "iclou.com": "Salah ketik pada domain '@iclou.com'. Gunakan '@icloud.com'.",
    "icloude.com": "Salah ketik pada domain '@icloude.com'. Gunakan '@icloud.com'.",
}

# Domain platform sosial / web yang bukan merupakan layanan email pendaftaran
NON_EMAIL_PLATFORMS = {
    "facebook.com": "Domain '@facebook.com' bukan layanan penyedia email pendaftaran akun.",
    "instagram.com": "Domain '@instagram.com' bukan layanan penyedia email pendaftaran akun.",
    "twitter.com": "Domain '@twitter.com' bukan layanan penyedia email pendaftaran akun.",
    "x.com": "Domain '@x.com' bukan layanan penyedia email pendaftaran akun.",
    "youtube.com": "Domain '@youtube.com' bukan layanan penyedia email pendaftaran akun.",
    "tiktok.com": "Domain '@tiktok.com' bukan layanan penyedia email pendaftaran akun.",
    "whatsapp.com": "Domain '@whatsapp.com' bukan layanan penyedia email pendaftaran akun.",
    "telegram.org": "Domain '@telegram.org' bukan layanan penyedia email pendaftaran akun.",
    "github.com": "Domain '@github.com' bukan layanan email umum. Gunakan '@gmail.com' atau email instansi.",
}


def validate_registration_data(
    full_name: str,
    email: str,
    password: str,
    allow_admin: bool = False,
) -> Tuple[bool, str, str]:
    """
    Validasi data formulir registrasi akun pengguna:
    1. Nama lengkap minimal 2 karakter, tidak boleh mengandung kata terlarang 'admin' (kecuali pembuatan akun admin manual).
    2. Email harus valid, domain @gmail.com / @googlemail.com atau email instansi/kampus/perusahaan yang sah.
       Mencegah dan memperingatkan salah ketik (contoh: nama@google.com -> harus nama@gmail.com).
    3. Password minimal 6 karakter.
    
    Returns:
        (is_valid: bool, error_message: str, detected_institution: str)
    """
    f_clean = (full_name or "").strip()
    e_clean = (email or "").strip().lower()
    p_clean = (password or "").strip()

    if not f_clean or len(f_clean) < 2:
        return False, "Nama lengkap wajib diisi minimal 2 karakter.", ""

    forbidden = ["admin", "administrator", "root", "superuser"]
    if not allow_admin and any(k in f_clean.lower() for k in forbidden):
        return False, "Nama lengkap tidak boleh mengandung kata terlarang (Administrator).", ""

    if not e_clean:
        return False, "Alamat email wajib diisi.", ""

    # Validasi format email RFC dasar
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, e_clean):
        return False, "Format alamat email tidak valid (contoh: nama@gmail.com atau nama@instansi.ac.id).", ""

    parts = e_clean.split("@")
    if len(parts) != 2:
        return False, "Format alamat email tidak valid.", ""

    domain = parts[1].strip()

    # 1. Cek salah ketik spesifik (Contoh: nama@google.com -> harus nama@gmail.com)
    if domain in EMAIL_TYPO_MAP:
        return False, f"Bentuk penulisan email salah: {EMAIL_TYPO_MAP[domain]}", ""

    # 2. Cek domain platform non-email
    if domain in NON_EMAIL_PLATFORMS:
        return False, f"Bentuk penulisan email salah: {NON_EMAIL_PLATFORMS[domain]}", ""

    # 3. Cek salah ketik pada ekstensi / TLD (.con, .comm, .cmo)
    if domain.endswith(".con"):
        return False, f"Bentuk penulisan domain salah: '@{domain}' berakhiran '.con'. Maksud Anda adalah berakhiran '.com'?", ""
    if domain.endswith(".comm"):
        return False, f"Bentuk penulisan domain salah: '@{domain}' berakhiran '.comm'. Maksud Anda adalah berakhiran '.com'?", ""
    if domain.endswith(".cmo"):
        return False, f"Bentuk penulisan domain salah: '@{domain}' berakhiran '.cmo'. Maksud Anda adalah berakhiran '.com'?", ""

    # 4. Blokir email sementara (disposable)
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False, "Domain email sementara/disposable tidak diizinkan. Harap gunakan @gmail.com atau email instansi resmi.", ""

    # 5. Klasifikasi jenis email & instansi (Wajib provider resmi Google/Yahoo/Outlook atau instansi resmi)
    TRUSTED_PUBLIC_DOMAINS = {
        "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.id",
        "outlook.com", "hotmail.com", "live.com", "icloud.com"
    }

    INSTITUTION_EXTENSIONS = (
        ".ac.id", ".edu", ".edu.id",    # Institusi Pendidikan / Kampus
        ".go.id", ".gov",               # Instansi Pemerintah / Lembaga Negara
        ".co.id",                       # Perusahaan / Korporat Resmi Indonesia (misal: idx.co.id, astra.co.id)
        ".or.id", ".sch.id", ".mil.id"  # Organisasi & Sekolah Resmi
    )

    if domain in ("gmail.com", "googlemail.com"):
        institution = "Akun Pribadi (@gmail.com)"
    elif domain in ("yahoo.com", "yahoo.co.id", "outlook.com", "hotmail.com", "live.com", "icloud.com"):
        institution = f"Akun Personal (@{domain})"
    elif any(domain.endswith(sfx) for sfx in [".ac.id", ".edu", ".edu.id"]):
        institution = f"Institusi Pendidikan / Kampus ({domain})"
    elif any(domain.endswith(sfx) for sfx in [".go.id", ".gov"]):
        institution = f"Instansi Pemerintah / Lembaga ({domain})"
    elif any(domain.endswith(sfx) for sfx in [".co.id", ".sch.id", ".or.id", ".mil.id"]):
        institution = f"Instansi / Korporat Resmi ({domain})"
    else:
        # Domain bebas/acak (seperti laman.com, rata.com, dll.) DITOLAK secara tegas
        return False, f"Domain '@{domain}' bukan penyedia email resmi yang valid. Harap gunakan alamat email dari Google (@gmail.com), penyedia email resmi (Yahoo, Outlook), atau email resmi instansi/kampus Anda (.ac.id, .co.id, .go.id).", ""

    if not p_clean:
        return False, "Kata sandi wajib diisi.", ""

    if len(p_clean) < 6:
        return False, "Kata sandi minimal 6 karakter demi keamanan akun Anda.", ""

    if p_clean.lower() in [f_clean.lower(), e_clean, "123456", "password"]:
        return False, "Kata sandi terlalu sederhana dan mudah ditebak. Gunakan kombinasi yang lebih aman.", ""

    return True, "", institution


INSTITUTION_EXTENSIONS = (
    ".ac.id", ".edu", ".edu.id",    # Institusi Pendidikan / Kampus
    ".go.id", ".gov",               # Instansi Pemerintah / Lembaga Negara
    ".co.id",                       # Perusahaan / Korporat Resmi Indonesia (misal: idx.co.id, astra.co.id)
    ".or.id", ".sch.id", ".mil.id"  # Organisasi & Sekolah Resmi
)


def is_institutional_email(email: str) -> bool:
    """Memeriksa apakah domain email tergolong instansi resmi/kampus/korporat (.ac.id, .edu, .co.id, .go.id, dll)."""
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1].strip().lower()
    return any(domain.endswith(sfx) for sfx in INSTITUTION_EXTENSIONS)


def derive_username(full_name: str, email: str = "", allow_admin: bool = False) -> str:
    """
    Mengambil username langsung dari Nama Lengkap (Full Name) tanpa tambahan underline (_) atau awalan email.
    Menghilangkan spasi ganda, membuang simbol berbahaya, dan menjaga nama lengkap asli yang rapi.
    """
    f_raw = (full_name or "").strip()
    # Rapikan spasi ganda
    clean_name = re.sub(r"\s+", " ", f_raw)
    # Hapus karakter aneh selain huruf, angka, titik, dan spasi (TIDAK menambahkan underline!)
    clean_name = re.sub(r"[^a-zA-Z0-9 .]", "", clean_name).strip(" .")

    if clean_name:
        cand_lower = clean_name.lower()
        if not allow_admin and cand_lower in {"admin", "administrator", "root", "superuser", "system", "moderator", "support"}:
            return f"{clean_name} User"
        return clean_name[:40]

    return "Pengguna"


def get_registration_passcode() -> str:
    """Mengambil kode akses pendaftaran instansi dari config.json."""
    try:
        cfg_path = BASE_DIR / "config.json"
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return str(data.get("registration_passcode", "DISTRESS2026")).strip()
    except Exception:
        pass
    return "DISTRESS2026"


def set_registration_passcode(new_code: str) -> bool:
    """Menyimpan kode akses pendaftaran instansi baru ke config.json."""
    if not new_code or not str(new_code).strip():
        return False
    try:
        cfg_path = BASE_DIR / "config.json"
        data = {}
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["registration_passcode"] = str(new_code).strip()
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def init_db():
    """Inisialisasi tabel users & predictions serta membuat akun default admin terenkripsi."""
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR(100) PRIMARY KEY,
                    password TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    email VARCHAR(255),
                    full_name VARCHAR(255)
                );
            """))
            try:
                for cname in ["email", "full_name", "phone_number", "institution", "user_type", "position", "city", "bio", "avatar_data", "created_at", "status", "failed_attempts", "locked_until"]:
                    conn.execute(sqlalchemy.text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {cname} TEXT;"))
                conn.execute(sqlalchemy.text("UPDATE users SET status = 'active' WHERE status IS NULL OR status = '';"))
                conn.execute(sqlalchemy.text("UPDATE users SET status = 'active' WHERE username = 'admin';"))
            except Exception:
                pass

            conn.execute(sqlalchemy.text("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100),
                    company VARCHAR(255),
                    ticker VARCHAR(50),
                    year INTEGER,
                    z_score DOUBLE PRECISION,
                    z_cls VARCHAR(50),
                    mda_score DOUBLE PRECISION,
                    mda_cls VARCHAR(50),
                    xgb_prob DOUBLE PRECISION,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            # Seed default admin jika belum ada
            res_admin = conn.execute(sqlalchemy.text("SELECT username FROM users WHERE username = 'admin'")).fetchone()
            if not res_admin:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    sqlalchemy.text("INSERT INTO users (username, password, role, email, full_name, institution, created_at) VALUES (:u, :p, :r, :e, :f, :i, :c)"),
                    {"u": "admin", "p": hash_password("admin123"), "r": "admin", "e": "admin@distress.ai", "f": "System Administrator", "i": "Sistem Internal", "c": now_str}
                )

            # Hapus akun uji coba dengan domain email yang tidak sah
            try:
                conn.execute(sqlalchemy.text("DELETE FROM users WHERE email LIKE '%@laman.com' OR email LIKE '%@rata.com'"))
            except Exception:
                pass
        return

    # Fallback ke SQLite
    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT,
            email TEXT,
            full_name TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    for cname in ["email", "full_name", "phone_number", "institution", "user_type", "position", "city", "bio", "avatar_data", "created_at", "status", "failed_attempts", "locked_until"]:
        if cname not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {cname} TEXT")
            except Exception:
                pass

    # Pastikan status default 'active' untuk user yang ada dan reset failed attempts jika null
    try:
        cursor.execute("UPDATE users SET status = 'active' WHERE status IS NULL OR status = ''")
        cursor.execute("UPDATE users SET status = 'active' WHERE username = 'admin'")
        cursor.execute("UPDATE users SET failed_attempts = 0 WHERE failed_attempts IS NULL")
    except Exception:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            company TEXT,
            ticker TEXT,
            year INTEGER,
            z_score REAL,
            z_cls TEXT,
            mda_score REAL,
            mda_cls TEXT,
            xgb_prob REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed default superadmin jika belum ada
    cursor.execute("SELECT password FROM users WHERE username = 'admin'")
    row_admin = cursor.fetchone()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not row_admin:
        cursor.execute(
            "INSERT INTO users (username, password, role, email, full_name, institution, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("admin", hash_password("admin123"), "admin", "admin@distress.ai", "System Administrator", "Sistem Internal", now_str)
        )
    elif not row_admin[0].startswith("pbkdf2:sha256:"):
        # Upgrade plaintext admin password ke hash
        cursor.execute("UPDATE users SET password = ? WHERE username = 'admin'", (hash_password(row_admin[0]),))

    # Seed default user jika belum ada (agar akun demo_user dan pengujian selalu valid)
    cursor.execute("SELECT password FROM users WHERE username = 'user'")
    row_user = cursor.fetchone()
    if not row_user:
        cursor.execute(
            "INSERT INTO users (username, password, role, email, full_name, institution, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("user", hash_password("user123"), "user", "user@distress.ai", "Financial Analyst", "Bursa Efek Indonesia (BEI)", now_str)
        )
    elif not row_user[0].startswith("pbkdf2:sha256:"):
        cursor.execute("UPDATE users SET password = ? WHERE username = 'user'", (hash_password(row_user[0]),))

    # Bersihkan akun uji coba dengan domain email yang tidak sah
    try:
        cursor.execute("DELETE FROM users WHERE email LIKE '%@laman.com' OR email LIKE '%@rata.com'")
    except Exception:
        pass

    conn.commit()
    conn.close()


# ==============================================================================
# 4. OPERASI PENGGUNA (AUTENTIKASI & MANAJEMEN AKUN)
# ==============================================================================
def verify_user_detailed(username: str, password: str) -> Tuple[bool, Optional[str], str, Optional[dict]]:
    """
    Memverifikasi username/email & password secara komprehensif:
    1. Pencegahan Brute-Force (Lockout 15 menit jika 5 kali salah kata sandi).
    2. Validasi Kata Sandi (Hash PBKDF2).
    3. Pengecekan Status Persetujuan Akun:
       - 'pending': Belum disetujui Administrator -> ditolak masuk dengan pesan informatif.
       - 'disabled': Akun dibekukan / dinonaktifkan -> ditolak masuk.
       - 'active': Berhasil masuk.
    4. Auto-reset counter percobaan gagal saat login sukses.

    Returns:
        (is_success: bool, role: Optional[str], message: str, user_profile: Optional[dict])
    """
    if not username or not password:
        return False, None, "Username/Email dan kata sandi wajib diisi.", None
    ident = username.strip().lower()
    now = datetime.now()

    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            res = conn.execute(
                sqlalchemy.text("""
                    SELECT username, password, role, status, failed_attempts, locked_until FROM users 
                    WHERE LOWER(username) = :u 
                       OR (email IS NOT NULL AND email != '' AND LOWER(email) = :u)
                       OR (full_name IS NOT NULL AND full_name != '' AND LOWER(full_name) = :u)
                       OR REPLACE(LOWER(username), ' ', '') = REPLACE(:u, ' ', '')
                       OR (full_name IS NOT NULL AND full_name != '' AND REPLACE(LOWER(full_name), ' ', '') = REPLACE(:u, ' ', ''))
                    LIMIT 1
                """),
                {"u": ident}
            ).fetchone()
            if not res:
                return False, None, "Username, nama lengkap, atau alamat email tidak terdaftar dalam sistem.", None

            actual_u, stored_pwd, role = res[0], res[1], res[2]
            status_val = res[3] or "active"
            failed_cnt = int(res[4] or 0)
            locked_until_str = res[5] or ""

            # 1. Cek Lockout Brute-Force
            if locked_until_str:
                try:
                    locked_dt = datetime.strptime(locked_until_str, "%Y-%m-%d %H:%M:%S")
                    if now < locked_dt:
                        mins_left = max(1, math.ceil((locked_dt - now).total_seconds() / 60))
                        return False, None, f"🔒 Akun dikunci sementara karena 5 kali percobaan salah. Silakan coba kembali dalam {mins_left} menit.", None
                    else:
                        with engine.begin() as wconn:
                            wconn.execute(
                                sqlalchemy.text("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = :u"),
                                {"u": actual_u}
                            )
                        failed_cnt = 0
                except Exception:
                    pass

            # 2. Cek Kata Sandi
            if not verify_password(password, stored_pwd):
                new_failed = failed_cnt + 1
                with engine.begin() as wconn:
                    if new_failed >= 5:
                        lock_dt_str = (now + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
                        wconn.execute(
                            sqlalchemy.text("UPDATE users SET failed_attempts = :f, locked_until = :l WHERE username = :u"),
                            {"f": new_failed, "l": lock_dt_str, "u": actual_u}
                        )
                        return False, None, "🔒 Terlalu banyak percobaan kata sandi salah! Akun Anda dikunci sementara selama 15 menit demi keamanan.", None
                    else:
                        wconn.execute(
                            sqlalchemy.text("UPDATE users SET failed_attempts = :f WHERE username = :u"),
                            {"f": new_failed, "u": actual_u}
                        )
                        sisa = 5 - new_failed
                        return False, None, f"Kata sandi yang Anda masukkan salah! (Sisa percobaan sebelum dikunci: {sisa} kali)", None

            # Reset percobaan gagal jika password benar
            with engine.begin() as wconn:
                wconn.execute(
                    sqlalchemy.text("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = :u"),
                    {"u": actual_u}
                )
                if not stored_pwd.startswith("pbkdf2:sha256:"):
                    wconn.execute(
                        sqlalchemy.text("UPDATE users SET password = :p WHERE username = :u"),
                        {"p": hash_password(password), "u": actual_u}
                    )

            # 3. Pengecekan Status Persetujuan Akun
            status_clean = str(status_val).strip().lower()
            if status_clean == "pending":
                return False, None, f"⚠️ Akun '{actual_u}' masih berstatus 'Menunggu Persetujuan' (Pending) dari Administrator. Silakan hubungi Administrator untuk verifikasi dan aktivasi akun Anda.", None
            if status_clean == "disabled":
                return False, None, f"🚫 Akun '{actual_u}' berstatus nonaktif (Disabled). Akses sistem ditutup oleh Administrator.", None

            prof = get_user_profile(actual_u)
            return True, role, "Login berhasil.", prof

    # SQLite
    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT username, password, role, status, failed_attempts, locked_until FROM users 
        WHERE LOWER(username) = ? 
           OR (email IS NOT NULL AND email != '' AND LOWER(email) = ?)
           OR (full_name IS NOT NULL AND full_name != '' AND LOWER(full_name) = ?)
           OR REPLACE(LOWER(username), ' ', '') = REPLACE(?, ' ', '')
           OR (full_name IS NOT NULL AND full_name != '' AND REPLACE(LOWER(full_name), ' ', '') = REPLACE(?, ' ', ''))
        LIMIT 1
        """,
        (ident, ident, ident, ident, ident)
    )
    res = cursor.fetchone()

    if not res:
        conn.close()
        return False, None, "Username, nama lengkap, atau alamat email tidak terdaftar dalam sistem.", None

    actual_u, stored_pwd, role = res[0], res[1], res[2]
    status_val = res[3] or "active"
    failed_cnt = int(res[4] or 0)
    locked_until_str = res[5] or ""

    # 1. Cek Lockout Brute-Force
    if locked_until_str:
        try:
            locked_dt = datetime.strptime(locked_until_str, "%Y-%m-%d %H:%M:%S")
            if now < locked_dt:
                mins_left = max(1, math.ceil((locked_dt - now).total_seconds() / 60))
                conn.close()
                return False, None, f"🔒 Akun dikunci sementara karena 5 kali percobaan salah. Silakan coba kembali dalam {mins_left} menit.", None
            else:
                cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = ?", (actual_u,))
                conn.commit()
                failed_cnt = 0
        except Exception:
            pass

    # 2. Cek Kata Sandi
    if not verify_password(password, stored_pwd):
        new_failed = failed_cnt + 1
        if new_failed >= 5:
            lock_dt_str = (now + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE username = ?", (new_failed, lock_dt_str, actual_u))
            conn.commit()
            conn.close()
            return False, None, "🔒 Terlalu banyak percobaan kata sandi salah! Akun Anda dikunci sementara selama 15 menit demi keamanan.", None
        else:
            cursor.execute("UPDATE users SET failed_attempts = ? WHERE username = ?", (new_failed, actual_u))
            conn.commit()
            conn.close()
            sisa = 5 - new_failed
            return False, None, f"Kata sandi yang Anda masukkan salah! (Sisa percobaan sebelum dikunci: {sisa} kali)", None

    # Reset percobaan gagal jika password benar
    cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = ?", (actual_u,))
    if not stored_pwd.startswith("pbkdf2:sha256:"):
        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hash_password(password), actual_u))
    conn.commit()
    conn.close()

    # 3. Pengecekan Status Persetujuan Akun
    status_clean = str(status_val).strip().lower()
    if status_clean == "pending":
        return False, None, f"⚠️ Akun '{actual_u}' masih berstatus 'Menunggu Persetujuan' (Pending) dari Administrator. Silakan hubungi Administrator untuk verifikasi dan aktivasi akun Anda.", None
    if status_clean == "disabled":
        return False, None, f"🚫 Akun '{actual_u}' berstatus nonaktif (Disabled). Akses sistem ditutup oleh Administrator.", None

    prof = get_user_profile(actual_u)
    return True, role, "Login berhasil.", prof


def verify_user(username: str, password: str) -> Optional[str]:
    """Memverifikasi username/email & password secara aman dengan enkripsi hash (kompatibilitas mundur)."""
    ok, role, _, _ = verify_user_detailed(username, password)
    return role if ok else None


def update_user_status(username: str, new_status: str) -> Tuple[bool, str]:
    """Mengubah status persetujuan akun pengguna ('active', 'pending', 'disabled'). Akun admin utama dilindungi."""
    if not username:
        return False, "Username tidak boleh kosong."
    u_clean = username.strip()
    s_clean = (new_status or "").strip().lower()
    if s_clean not in ("active", "pending", "disabled"):
        return False, f"Status '{new_status}' tidak valid. Pilihan status: active, pending, disabled."
    if u_clean.lower() == "admin" and s_clean != "active":
        return False, "Akun Administrator utama dilindungi dan tidak boleh dinonaktifkan atau ditunda!"

    is_pg, pg_url = is_postgres_available()
    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        try:
            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("UPDATE users SET status = :s WHERE LOWER(username) = :u"),
                    {"s": s_clean, "u": u_clean.lower()}
                )
            return True, f"Status akun '{u_clean}' berhasil diubah menjadi '{s_clean}'."
        except Exception as err:
            return False, f"Gagal memperbarui status akun: {err}"

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET status = ? WHERE LOWER(username) = ?", (s_clean, u_clean.lower()))
        conn.commit()
        conn.close()
        return True, f"Status akun '{u_clean}' berhasil diubah menjadi '{s_clean}'."
    except Exception as err:
        conn.close()
        return False, f"Gagal memperbarui status akun: {err}"


def update_user_role(username: str, new_role: str) -> Tuple[bool, str]:
    """Mengubah hak akses (role) akun pengguna ('user' atau 'admin'). Akun 'admin' utama dilindungi dari penurunan hak akses."""
    if not username:
        return False, "Username tidak boleh kosong."
    u_clean = username.strip()
    r_clean = (new_role or "").strip().lower()
    if r_clean not in ("user", "admin"):
        return False, f"Role '{new_role}' tidak valid. Pilihan role: user, admin."
    if u_clean.lower() == "admin" and r_clean != "admin":
        return False, "Akun Administrator utama dilindungi dan tidak boleh diubah menjadi pengguna biasa!"

    is_pg, pg_url = is_postgres_available()
    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        try:
            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("UPDATE users SET role = :r WHERE LOWER(username) = :u"),
                    {"r": r_clean, "u": u_clean.lower()}
                )
            return True, f"Hak akses akun '{u_clean}' berhasil diubah menjadi '{r_clean}'."
        except Exception as err:
            return False, f"Gagal memperbarui role akun: {err}"

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET role = ? WHERE LOWER(username) = ?", (r_clean, u_clean.lower()))
        conn.commit()
        conn.close()
        return True, f"Hak akses akun '{u_clean}' berhasil diubah menjadi '{r_clean}'."
    except Exception as err:
        conn.close()
        return False, f"Gagal memperbarui role akun: {err}"


def get_user_profile(identifier: str) -> Optional[dict]:
    """Mengambil profil lengkap pengguna berdasarkan username atau email."""
    if not identifier:
        return None
    ident = identifier.strip().lower()

    is_pg, pg_url = is_postgres_available()
    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            res = conn.execute(
                sqlalchemy.text("SELECT username, role, email, full_name, phone_number, institution, user_type, position, city, bio, avatar_data, status, created_at, failed_attempts, locked_until FROM users WHERE LOWER(username) = :u OR (email IS NOT NULL AND email != '' AND LOWER(email) = :u) OR (full_name IS NOT NULL AND full_name != '' AND LOWER(full_name) = :u) OR REPLACE(LOWER(username), ' ', '') = REPLACE(:u, ' ', '') LIMIT 1"),
                {"u": ident}
            ).fetchone()
            if res:
                return {
                    "username": res[0],
                    "role": res[1],
                    "email": res[2] or "",
                    "full_name": res[3] or "",
                    "phone_number": res[4] or "",
                    "institution": res[5] or "",
                    "user_type": res[6] or "",
                    "position": res[7] or "",
                    "city": res[8] or "",
                    "bio": res[9] or "",
                    "avatar_data": res[10] or "",
                    "status": res[11] or "active",
                    "created_at": str(res[12]) if res[12] else "",
                    "failed_attempts": int(res[13] or 0),
                    "locked_until": str(res[14]) if res[14] else "",
                }
        return None

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cursor.fetchall()]
    select_fields = ["username", "role", "email", "full_name"]
    optional_fields = ["phone_number", "institution", "user_type", "position", "city", "bio", "avatar_data", "status", "created_at", "failed_attempts", "locked_until"]
    for f in optional_fields:
        if f in cols:
            select_fields.append(f)
        else:
            select_fields.append(f"'' AS {f}")

    query = f"SELECT {', '.join(select_fields)} FROM users WHERE LOWER(username) = ? OR (email IS NOT NULL AND email != '' AND LOWER(email) = ?) OR (full_name IS NOT NULL AND full_name != '' AND LOWER(full_name) = ?) OR REPLACE(LOWER(username), ' ', '') = REPLACE(?, ' ', '') LIMIT 1"
    cursor.execute(query, (ident, ident, ident, ident))
    res = cursor.fetchone()
    conn.close()
    if res:
        col_map = {col_name: res[idx] for idx, col_name in enumerate(["username", "role", "email", "full_name"] + optional_fields)}
        return {
            "username": col_map.get("username") or "",
            "role": col_map.get("role") or "user",
            "email": col_map.get("email") or "",
            "full_name": col_map.get("full_name") or "",
            "phone_number": col_map.get("phone_number") or "",
            "institution": col_map.get("institution") or "",
            "user_type": col_map.get("user_type") or "",
            "position": col_map.get("position") or "",
            "city": col_map.get("city") or "",
            "bio": col_map.get("bio") or "",
            "avatar_data": col_map.get("avatar_data") or "",
            "status": col_map.get("status") or "active",
            "created_at": col_map.get("created_at") or "",
            "failed_attempts": int(col_map.get("failed_attempts") or 0) if col_map.get("failed_attempts") else 0,
            "locked_until": col_map.get("locked_until") or "",
        }
    return None


def get_all_users() -> pd.DataFrame:
    """Mengambil daftar seluruh pengguna lengkap dengan metadata profil, status, dan tanggal pendaftaran."""
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            try:
                df = pd.read_sql_query(
                    sqlalchemy.text("SELECT username, role, email, full_name, institution, status, created_at FROM users ORDER BY created_at DESC, username ASC"),
                    conn
                )
            except Exception:
                df = pd.read_sql_query(
                    sqlalchemy.text("SELECT username, role, email, full_name, institution FROM users ORDER BY username ASC"),
                    conn
                )
            if "status" not in df.columns:
                df["status"] = "active"
            else:
                df["status"] = df["status"].fillna("active").apply(lambda s: s if s in ("active", "pending", "disabled") else "active")
            return df

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    tbl_cols = [c[1] for c in cursor.fetchall()]
    cols_wanted = ["username", "role", "email", "full_name", "institution", "status", "created_at"]
    sel_cols = [c if c in tbl_cols else f"'' AS {c}" for c in cols_wanted]
    order_clause = "ORDER BY created_at DESC, username ASC" if "created_at" in tbl_cols else "ORDER BY username ASC"
    query = f"SELECT {', '.join(sel_cols)} FROM users {order_clause}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    if "status" not in df.columns:
        df["status"] = "active"
    else:
        df["status"] = df["status"].fillna("active").apply(lambda s: s if s in ("active", "pending", "disabled") else "active")
    return df


def add_new_user(
    username: str,
    password: str,
    role: str = "user",
    email: str = "",
    full_name: str = "",
    institution: str = "",
    passcode: str = "",
    status: Optional[str] = None,
    created_at: Optional[str] = None,
) -> AuthResult:
    """
    Mendaftarkan akun pengguna baru dengan verifikasi cerdas validitas email.
    Sistem secara otomatis mendeteksi dan memvalidasi kredibilitas email:
    - Email yang valid dan sah (Google @gmail.com, email instansi .ac.id, .co.id, .go.id, atau penyedia resmi):
      Otomatis langsung Disetujui (Active) tanpa perlu kode akses atau persetujuan manual Admin.
    - Email tidak sah/salah ketik/palsu (seperti @google.com, @gamil.com, medsos, email sementara):
      Dideteksi dan ditolak oleh sistem dengan peringatan yang jelas dan mendidik.
    """
    u_clean = (username or "").strip()
    p_clean = (password or "").strip()
    e_clean = (email or "").strip().lower()
    f_clean = (full_name or "").strip()
    i_clean = (institution or "").strip()
    r_clean = (role or "user").strip().lower()
    c_time = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not u_clean or not p_clean:
        return AuthResult(False, "Username dan password wajib diisi.")

    if len(p_clean) < 6:
        return AuthResult(False, "Password minimal 6 karakter demi keamanan akun.")

    # 1. Validasi Cerdas Format, Domain, dan Kredibilitas Email
    if e_clean:
        is_ok, err_msg, det_inst = validate_registration_data(
            f_clean or u_clean,
            e_clean,
            p_clean,
            allow_admin=(r_clean == "admin")
        )
        if not is_ok:
            return AuthResult(False, err_msg)
        if not i_clean:
            i_clean = det_inst

    is_inst = is_institutional_email(e_clean)

    # 2. Aturan Otomatis Persetujuan Akun:
    # Seluruh pendaftar dengan email yang lolos validasi cerdas sistem langsung disetujui otomatis (Active)
    if status is not None:
        s_clean = status.strip().lower()
        if s_clean not in ("active", "pending", "disabled"):
            s_clean = "active"
    else:
        s_clean = "active"

    # Penanganan Hak Akses (Role): Mendukung user biasa dan pembuatan manual admin oleh Administrator
    role_to_save = "admin" if r_clean == "admin" else "user"
    u_lower = u_clean.lower()
    e_lower = e_clean.lower()
    f_lower = f_clean.lower()

    # Jika bukan role admin (misal pendaftaran publik oleh pengguna umum):
    # Blokir upaya peniruan nama admin / sistem
    if role_to_save != "admin":
        forbidden_keywords = ["admin", "administrator", "root", "superuser"]

        if (
            any(k in u_lower for k in forbidden_keywords)
            or any(k in e_lower for k in forbidden_keywords)
            or any(k in f_lower for k in forbidden_keywords)
        ):
            return AuthResult(False, "Pembuatan akun dengan nama atau email Administrator diblokir demi keamanan sistem! Silakan gunakan nama atau email lain.")
    else:
        # Jika membuat akun Administrator baru secara manual:
        # Lindungi superadmin 'admin' agar tidak ditimpa jika sudah ada
        if u_clean.lower() == "admin":
            return AuthResult(False, "Username 'admin' sudah digunakan untuk Super Admin utama. Silakan gunakan nama lengkap atau username lain untuk admin baru.")

    # Jika instansi belum ditentukan, deteksi otomatis dari domain email
    if not i_clean and "@" in e_clean:
        dom = e_clean.split("@")[-1].strip()
        if dom in ("gmail.com", "googlemail.com"):
            i_clean = "Akun Pribadi (@gmail.com)"
        elif any(dom.endswith(sfx) for sfx in [".ac.id", ".edu", ".edu.id"]):
            i_clean = f"Akademik / Kampus ({dom})"
        elif any(dom.endswith(sfx) for sfx in [".go.id", ".gov"]):
            i_clean = f"Instansi Pemerintah ({dom})"
        elif any(dom.endswith(sfx) for sfx in [".co.id", ".sch.id", ".or.id", ".mil.id"]):
            i_clean = f"Instansi Resmi ({dom})"
        else:
            i_clean = f"Instansi / Perusahaan ({dom})"

    hashed = hash_password(p_clean)
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                if e_lower:
                    existing_email = conn.execute(
                        sqlalchemy.text("SELECT username FROM users WHERE LOWER(email) = :e"),
                        {"e": e_lower}
                    ).fetchone()
                    if existing_email:
                        return AuthResult(False, f"Alamat email '{e_clean}' sudah terdaftar. Silakan langsung masuk.")

                final_u = u_clean
                base_u = u_clean
                counter = 1
                while conn.execute(sqlalchemy.text("SELECT username FROM users WHERE LOWER(username) = :u"), {"u": final_u.lower()}).fetchone():
                    final_u = f"{base_u} {counter}"
                    counter += 1

            with engine.begin() as conn:
                try:
                    conn.execute(
                        sqlalchemy.text("INSERT INTO users (username, password, role, email, full_name, institution, status, failed_attempts, created_at) VALUES (:u, :p, :r, :e, :f, :i, :s, 0, :c)"),
                        {"u": final_u, "p": hashed, "r": role_to_save, "e": e_clean, "f": f_clean, "i": i_clean, "s": s_clean, "c": c_time}
                    )
                except Exception:
                    conn.execute(
                        sqlalchemy.text("INSERT INTO users (username, password, role, email, full_name) VALUES (:u, :p, :r, :e, :f)"),
                        {"u": final_u, "p": hashed, "r": role_to_save, "e": e_clean, "f": f_clean}
                    )
            if role_to_save == "admin":
                return AuthResult(True, f"🎉 Akun Administrator '{final_u}' berhasil didaftarkan dan langsung aktif!")
            elif is_inst:
                return AuthResult(True, f"🎉 Pendaftaran berhasil! Akun resmi instansi '{final_u}' telah diverifikasi dan langsung aktif. Silakan masuk.")
            else:
                return AuthResult(True, f"🎉 Pendaftaran berhasil! Alamat email '{e_clean}' terverifikasi valid. Akun '{final_u}' telah aktif otomatis. Silakan langsung masuk.")
        except Exception as err:
            return AuthResult(False, f"Gagal mendaftarkan akun: {err}")

    # SQLite
    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    try:
        # 1. Cek apakah alamat email sudah terdaftar
        if e_lower:
            cursor.execute("SELECT username FROM users WHERE LOWER(email) = ?", (e_lower,))
            if cursor.fetchone():
                conn.close()
                return AuthResult(False, f"Alamat email '{e_clean}' sudah terdaftar. Silakan langsung masuk.")

        # 2. Disambiguasi username jika sudah ada
        final_u = u_clean
        base_u = u_clean
        counter = 1
        cursor.execute("SELECT username FROM users WHERE LOWER(username) = ?", (final_u.lower(),))
        while cursor.fetchone():
            final_u = f"{base_u} {counter}"
            counter += 1
            cursor.execute("SELECT username FROM users WHERE LOWER(username) = ?", (final_u.lower(),))

        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        
        insert_cols = ["username", "password", "role", "email", "full_name"]
        insert_vals = [final_u, hashed, role_to_save, e_clean, f_clean]
        if "institution" in cols:
            insert_cols.append("institution")
            insert_vals.append(i_clean)
        if "status" in cols:
            insert_cols.append("status")
            insert_vals.append(s_clean)
        if "failed_attempts" in cols:
            insert_cols.append("failed_attempts")
            insert_vals.append(0)
        if "created_at" in cols:
            insert_cols.append("created_at")
            insert_vals.append(c_time)

        placeholders = ", ".join(["?"] * len(insert_vals))
        col_names = ", ".join(insert_cols)
        cursor.execute(
            f"INSERT INTO users ({col_names}) VALUES ({placeholders})",
            tuple(insert_vals)
        )
        conn.commit()
        conn.close()
        if role_to_save == "admin":
            return AuthResult(True, f"🎉 Akun Administrator '{final_u}' berhasil didaftarkan dan langsung aktif!")
        elif is_inst:
            return AuthResult(True, f"🎉 Pendaftaran berhasil! Akun resmi instansi '{final_u}' telah diverifikasi dan langsung aktif. Silakan masuk.")
        else:
            return AuthResult(True, f"🎉 Pendaftaran berhasil! Alamat email '{e_clean}' terverifikasi valid. Akun '{final_u}' telah aktif otomatis. Silakan langsung masuk.")
    except Exception as err:
        conn.close()
        return AuthResult(False, f"Gagal mendaftarkan akun: {err}")


def admin_reset_user_password(username: str, new_password: str) -> Tuple[bool, str]:
    """Admin mereset kata sandi akun pengguna."""
    u_clean = (username or "").strip()
    p_clean = (new_password or "").strip()
    if not u_clean or not p_clean:
        return False, "Username dan kata sandi baru tidak boleh kosong."
    if len(p_clean) < 6:
        return False, "Kata sandi baru minimal 6 karakter."
    return update_user_credentials(current_username=u_clean, new_password=p_clean)


def delete_user_by_username(username: str) -> Tuple[bool, str]:
    """Menghapus akun pengguna terpilih (admin utama dilindungi)."""
    if username.lower() == "admin":
        return False, "Akun 'admin' utama dilindungi dan tidak boleh dihapus!"

    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("DELETE FROM users WHERE username = :u"),
                {"u": username}
            )
        return True, f"Akun '{username}' berhasil dihapus dari sistem."

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return True, f"Akun '{username}' berhasil dihapus dari sistem."


def update_user_credentials(
    current_username: str,
    new_username: Optional[str] = None,
    new_password: Optional[str] = None,
    new_email: Optional[str] = None,
    new_full_name: Optional[str] = None,
    new_phone_number: Optional[str] = None,
    new_institution: Optional[str] = None,
    new_user_type: Optional[str] = None,
    new_position: Optional[str] = None,
    new_city: Optional[str] = None,
    new_bio: Optional[str] = None,
    new_avatar_data: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Memperbarui kredensial dan seluruh atribut data profil pengguna:
    username, kata sandi, email, nama lengkap, telepon, instansi, sebagai/kategori, jabatan, domisili, bio, dan foto profil.
    Mendukung PostgreSQL Cloud dan SQLite lokal secara konsisten.
    """
    c_u = (current_username or "").strip()
    if not c_u:
        return False, "Nama pengguna saat ini tidak valid."

    target_u = (new_username or c_u).strip()
    if not target_u:
        return False, "Nama pengguna baru tidak boleh kosong."

    target_u_lower = target_u.lower()
    c_u_lower = c_u.lower()

    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        try:
            with engine.begin() as conn:
                for cname in ["email", "full_name", "phone_number", "institution", "user_type", "position", "city", "bio", "avatar_data", "created_at"]:
                    try:
                        conn.execute(sqlalchemy.text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {cname} TEXT;"))
                    except Exception:
                        pass

            with engine.connect() as conn:
                user_row = conn.execute(
                    sqlalchemy.text("SELECT username, password, role, email, full_name, phone_number, institution, user_type, position, city, bio, avatar_data FROM users WHERE LOWER(username) = :u"),
                    {"u": c_u_lower}
                ).fetchone()

                if target_u_lower != c_u_lower:
                    conflict = conn.execute(
                        sqlalchemy.text("SELECT username FROM users WHERE LOWER(username) = :u"),
                        {"u": target_u_lower}
                    ).fetchone()
                    if conflict:
                        return False, f"Username '{target_u}' sudah digunakan oleh pengguna lain."

            pwd_to_save = user_row[1] if user_row else hash_password("user123")
            if new_password and new_password.strip():
                if len(new_password.strip()) < 4:
                    return False, "Kata sandi baru minimal 4 karakter."
                pwd_to_save = hash_password(new_password.strip())

            email_to_save = new_email.strip() if new_email is not None else ((user_row[3] or "") if user_row else "")
            name_to_save = new_full_name.strip() if new_full_name is not None else ((user_row[4] or "") if user_row else "")
            phone_to_save = new_phone_number.strip() if new_phone_number is not None else ((user_row[5] or "") if user_row else "")
            inst_to_save = new_institution.strip() if new_institution is not None else ((user_row[6] or "") if user_row else "")
            utype_to_save = new_user_type.strip() if new_user_type is not None else ((user_row[7] or "") if user_row else "")
            pos_to_save = new_position.strip() if new_position is not None else ((user_row[8] or "") if user_row else "")
            city_to_save = new_city.strip() if new_city is not None else ((user_row[9] or "") if user_row else "")
            bio_to_save = new_bio.strip() if new_bio is not None else ((user_row[10] or "") if user_row else "")
            avatar_to_save = new_avatar_data if new_avatar_data is not None else ((user_row[11] or "") if user_row else "")

            with engine.begin() as conn:
                role_to_insert = (user_row[2] if user_row else None) or ("admin" if (c_u_lower == "admin" or target_u_lower == "admin") else "user")
                if not user_row:
                    conn.execute(
                        sqlalchemy.text("""
                            INSERT INTO users (username, password, role, email, full_name, phone_number, institution, user_type, position, city, bio, avatar_data)
                            VALUES (:new_u, :p, :r, :e, :f, :phone, :inst, :utype, :pos, :city, :bio, :avatar)
                        """),
                        {
                            "new_u": target_u, "p": pwd_to_save, "r": role_to_insert, "e": email_to_save, "f": name_to_save,
                            "phone": phone_to_save, "inst": inst_to_save, "utype": utype_to_save,
                            "pos": pos_to_save, "city": city_to_save, "bio": bio_to_save, "avatar": avatar_to_save,
                        }
                    )
                else:
                    conn.execute(
                        sqlalchemy.text("""
                            UPDATE users SET 
                                username = :new_u, password = :p, email = :e, full_name = :f,
                                phone_number = :phone, institution = :inst, user_type = :utype,
                                position = :pos, city = :city, bio = :bio, avatar_data = :avatar
                            WHERE LOWER(username) = :old_u
                        """),
                        {
                            "new_u": target_u, "p": pwd_to_save, "e": email_to_save, "f": name_to_save,
                            "phone": phone_to_save, "inst": inst_to_save, "utype": utype_to_save,
                            "pos": pos_to_save, "city": city_to_save, "bio": bio_to_save, "avatar": avatar_to_save,
                            "old_u": c_u_lower
                        }
                    )
                    if target_u_lower != c_u_lower:
                        conn.execute(
                            sqlalchemy.text("UPDATE predictions SET username = :new_u WHERE LOWER(username) = :old_u"),
                            {"new_u": target_u, "old_u": c_u_lower}
                        )
            return True, "Profil dan kelengkapan identitas akun berhasil diperbarui."
        except Exception as err:
            return False, f"Gagal memperbarui profil: {err}"

    # SQLite Lokal
    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    try:
        # 1. Pastikan seluruh kolom ada di tabel users
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        for cname in ["email", "full_name", "phone_number", "institution", "user_type", "position", "city", "bio", "avatar_data", "created_at"]:
            if cname not in cols:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {cname} TEXT")
                    conn.commit()
                except Exception:
                    pass

        # Ambil daftar kolom terkini setelah migrasi
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        sel_cols = ["username", "password", "role", "email", "full_name"]
        for opt_col in ["phone_number", "institution", "user_type", "position", "city", "bio", "avatar_data"]:
            if opt_col in cols:
                sel_cols.append(opt_col)
            else:
                sel_cols.append(f"'' AS {opt_col}")

        cursor.execute(f"SELECT {', '.join(sel_cols)} FROM users WHERE LOWER(username) = ?", (c_u_lower,))
        user_row = cursor.fetchone()

        if target_u_lower != c_u_lower:
            cursor.execute("SELECT username FROM users WHERE LOWER(username) = ?", (target_u_lower,))
            if cursor.fetchone():
                conn.close()
                return False, f"Username '{target_u}' sudah digunakan oleh pengguna lain."

        pwd_to_save = user_row[1] if user_row else hash_password("user123")
        if new_password and new_password.strip():
            if len(new_password.strip()) < 4:
                conn.close()
                return False, "Kata sandi baru minimal 4 karakter."
            pwd_to_save = hash_password(new_password.strip())

        email_to_save = new_email.strip() if new_email is not None else ((user_row[3] or "") if user_row else "")
        name_to_save = new_full_name.strip() if new_full_name is not None else ((user_row[4] or "") if user_row else "")
        phone_to_save = new_phone_number.strip() if new_phone_number is not None else ((user_row[5] if len(user_row) > 5 else "") if user_row else "")
        inst_to_save = new_institution.strip() if new_institution is not None else ((user_row[6] if len(user_row) > 6 else "") if user_row else "")
        utype_to_save = new_user_type.strip() if new_user_type is not None else ((user_row[7] if len(user_row) > 7 else "") if user_row else "")
        pos_to_save = new_position.strip() if new_position is not None else ((user_row[8] if len(user_row) > 8 else "") if user_row else "")
        city_to_save = new_city.strip() if new_city is not None else ((user_row[9] if len(user_row) > 9 else "") if user_row else "")
        bio_to_save = new_bio.strip() if new_bio is not None else ((user_row[10] if len(user_row) > 10 else "") if user_row else "")
        avatar_to_save = new_avatar_data if new_avatar_data is not None else ((user_row[11] if len(user_row) > 11 else "") if user_row else "")

        role_to_insert = (user_row[2] if user_row else None) or ("admin" if (c_u_lower == "admin" or target_u_lower == "admin") else "user")
        if not user_row:
            # Akun belum terdaftar di tabel users, otomatis buat entri baru (upsert)
            cursor.execute(
                """
                INSERT INTO users (username, password, role, email, full_name, phone_number, institution, user_type, position, city, bio, avatar_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    target_u, pwd_to_save, role_to_insert, email_to_save, name_to_save,
                    phone_to_save, inst_to_save, utype_to_save,
                    pos_to_save, city_to_save, bio_to_save, avatar_to_save
                )
            )
        else:
            cursor.execute(
                """
                UPDATE users SET 
                    username = ?, password = ?, email = ?, full_name = ?,
                    phone_number = ?, institution = ?, user_type = ?,
                    position = ?, city = ?, bio = ?, avatar_data = ?
                WHERE LOWER(username) = ?
                """,
                (
                    target_u, pwd_to_save, email_to_save, name_to_save,
                    phone_to_save, inst_to_save, utype_to_save,
                    pos_to_save, city_to_save, bio_to_save, avatar_to_save,
                    c_u_lower
                )
            )
            if target_u_lower != c_u_lower:
                cursor.execute("UPDATE predictions SET username = ? WHERE LOWER(username) = ?", (target_u, c_u_lower))

        conn.commit()
        conn.close()
        return True, "Profil dan kelengkapan identitas akun berhasil diperbarui."
    except Exception as err:
        conn.close()
        return False, f"Gagal memperbarui profil: {err}"


# ==============================================================================
# 5. OPERASI RIWAYAT PREDIKSI (PREDICTIONS)
# ==============================================================================
def save_prediction_to_db(
    username: str,
    company: str,
    ticker: str,
    year: int,
    z: float,
    z_cls: str,
    mda: float,
    mda_cls: str,
    xgb_prob: float,
):
    """Menyimpan hasil analisis prediksi ke basis data riwayat."""
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO predictions (username, company, ticker, year, z_score, z_cls, mda_score, mda_cls, xgb_prob)
                    VALUES (:username, :company, :ticker, :year, :z, :z_cls, :mda, :mda_cls, :xgb_prob)
                """),
                {
                    "username": username,
                    "company": company,
                    "ticker": ticker,
                    "year": int(year),
                    "z": float(z),
                    "z_cls": str(z_cls),
                    "mda": float(mda),
                    "mda_cls": str(mda_cls),
                    "xgb_prob": float(xgb_prob or 0.0),
                }
            )
        return

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO predictions (username, company, ticker, year, z_score, z_cls, mda_score, mda_cls, xgb_prob)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, company, ticker, int(year), float(z), str(z_cls), float(mda), str(mda_cls), float(xgb_prob or 0.0)))
    conn.commit()
    conn.close()


def get_all_predictions() -> pd.DataFrame:
    """Mengambil seluruh riwayat data prediksi dari basis data."""
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            df = pd.read_sql_query(
                sqlalchemy.text("SELECT * FROM predictions ORDER BY id DESC"),
                conn
            )
            return df

    conn = _get_sqlite_conn()
    df = pd.read_sql_query("SELECT * FROM predictions ORDER BY id DESC", conn)
    conn.close()
    return df


def delete_prediction_by_id(pred_id: int):
    """Menghapus entri riwayat prediksi berdasarkan ID spesifik."""
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text("DELETE FROM predictions WHERE id = :id"),
                {"id": int(pred_id)}
            )
        return

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions WHERE id = ?", (int(pred_id),))
    conn.commit()
    conn.close()


def clear_all_predictions():
    """Mengosongkan seluruh riwayat prediksi."""
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text("DELETE FROM predictions"))
        return

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM predictions")
    conn.commit()
    conn.close()
