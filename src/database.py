from __future__ import annotations

import os
import hashlib
import hmac
import secrets
import sqlite3
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


def init_db():
    """Inisialisasi tabel users & predictions serta membuat akun default terenkripsi."""
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
                conn.execute(sqlalchemy.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);"))
                conn.execute(sqlalchemy.text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);"))
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

            # Seed default admin & user jika belum ada
            res_admin = conn.execute(sqlalchemy.text("SELECT username FROM users WHERE username = 'admin'")).fetchone()
            if not res_admin:
                conn.execute(
                    sqlalchemy.text("INSERT INTO users (username, password, role, email, full_name) VALUES (:u, :p, :r, :e, :f)"),
                    {"u": "admin", "p": hash_password("admin123"), "r": "admin", "e": "admin@distress.ai", "f": "System Administrator"}
                )

            res_user = conn.execute(sqlalchemy.text("SELECT username FROM users WHERE username = 'user'")).fetchone()
            if not res_user:
                conn.execute(
                    sqlalchemy.text("INSERT INTO users (username, password, role, email, full_name) VALUES (:u, :p, :r, :e, :f)"),
                    {"u": "user", "p": hash_password("user123"), "r": "user", "e": "user@distress.ai", "f": "Financial Analyst"}
                )
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
    if "email" not in existing_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        except Exception:
            pass
    if "full_name" not in existing_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
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

    # Seed default user jika belum ada
    cursor.execute("SELECT password FROM users WHERE username = 'admin'")
    row_admin = cursor.fetchone()
    if not row_admin:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", ("admin", hash_password("admin123"), "admin", "admin@distress.ai", "System Administrator"))
    elif not row_admin[0].startswith("pbkdf2:sha256:"):
        # Upgrade plaintext admin password ke hash
        cursor.execute("UPDATE users SET password = ? WHERE username = 'admin'", (hash_password(row_admin[0]),))

    cursor.execute("SELECT password FROM users WHERE username = 'user'")
    row_user = cursor.fetchone()
    if not row_user:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", ("user", hash_password("user123"), "user", "user@distress.ai", "Financial Analyst"))
    elif not row_user[0].startswith("pbkdf2:sha256:"):
        # Upgrade plaintext user password ke hash
        cursor.execute("UPDATE users SET password = ? WHERE username = 'user'", (hash_password(row_user[0]),))

    conn.commit()
    conn.close()


# ==============================================================================
# 4. OPERASI PENGGUNA (AUTENTIKASI & MANAJEMEN AKUN)
# ==============================================================================
def verify_user(username: str, password: str) -> Optional[str]:
    """Memverifikasi username/email & password secara aman dengan enkripsi hash."""
    if not username or not password:
        return None
    ident = username.strip().lower()

    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            res = conn.execute(
                sqlalchemy.text("SELECT username, password, role FROM users WHERE LOWER(username) = :u OR (email IS NOT NULL AND email != '' AND LOWER(email) = :u)"),
                {"u": ident}
            ).fetchone()
            if not res:
                return None
            actual_u, stored_pwd, role = res[0], res[1], res[2]
            if verify_password(password, stored_pwd):
                # Auto-upgrade plaintext ke hash jika belum ter-hash
                if not stored_pwd.startswith("pbkdf2:sha256:"):
                    with engine.begin() as wconn:
                        wconn.execute(
                            sqlalchemy.text("UPDATE users SET password = :p WHERE username = :u"),
                            {"p": hash_password(password), "u": actual_u}
                        )
                return role
        return None

    # SQLite
    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, password, role FROM users WHERE LOWER(username) = ? OR (email IS NOT NULL AND email != '' AND LOWER(email) = ?)",
        (ident, ident)
    )
    res = cursor.fetchone()

    if not res:
        conn.close()
        return None

    actual_u, stored_pwd, role = res[0], res[1], res[2]
    if verify_password(password, stored_pwd):
        if not stored_pwd.startswith("pbkdf2:sha256:"):
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hash_password(password), actual_u))
            conn.commit()
        conn.close()
        return role

    conn.close()
    return None


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
                sqlalchemy.text("SELECT username, role, email, full_name FROM users WHERE LOWER(username) = :u OR (email IS NOT NULL AND email != '' AND LOWER(email) = :u) LIMIT 1"),
                {"u": ident}
            ).fetchone()
            if res:
                return {"username": res[0], "role": res[1], "email": res[2] or "", "full_name": res[3] or ""}
        return None

    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, role, email, full_name FROM users WHERE LOWER(username) = ? OR (email IS NOT NULL AND email != '' AND LOWER(email) = ?) LIMIT 1",
        (ident, ident)
    )
    res = cursor.fetchone()
    conn.close()
    if res:
        return {"username": res[0], "role": res[1], "email": res[2] or "", "full_name": res[3] or ""}
    return None


def get_all_users() -> pd.DataFrame:
    """Mengambil daftar seluruh pengguna (tanpa mengekspos hash password)."""
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        with engine.connect() as conn:
            df = pd.read_sql_query(
                sqlalchemy.text("SELECT username, role, email, full_name FROM users ORDER BY username ASC"),
                conn
            )
            return df

    conn = _get_sqlite_conn()
    df = pd.read_sql_query("SELECT username, role, email, full_name FROM users ORDER BY username ASC", conn)
    conn.close()
    return df


def add_new_user(
    username: str,
    password: str,
    role: str = "user",
    email: str = "",
    full_name: str = "",
) -> AuthResult:
    """
    Mendaftarkan akun baru dengan password terenkripsi.
    Secara ketat memblokir pembuatan akun dengan nama atau role 'admin'.
    """
    u_clean = (username or "").strip()
    p_clean = (password or "").strip()
    e_clean = (email or "").strip()
    f_clean = (full_name or "").strip()
    r_clean = (role or "user").strip().lower()

    if not u_clean or not p_clean:
        return AuthResult(False, "Username dan password wajib diisi.")

    if len(p_clean) < 4:
        return AuthResult(False, "Password minimal 4 karakter.")

    # BLOKIR KETAT PEMBUATAN AKUN ADMIN (Strictest Security Policy)
    forbidden_keywords = ["admin", "administrator", "root", "superuser"]
    u_lower = u_clean.lower()
    e_lower = e_clean.lower()
    f_lower = f_clean.lower()

    if (
        r_clean == "admin"
        or any(k in u_lower for k in forbidden_keywords)
        or any(k in e_lower for k in forbidden_keywords)
        or any(k in f_lower for k in forbidden_keywords)
    ):
        return AuthResult(False, "Pembuatan akun Administrator diblokir demi keamanan sistem! Silakan gunakan nama atau email lain.")

    # Paksa role selalu user biasa
    role_to_save = "user"
    hashed = hash_password(p_clean)
    is_pg, pg_url = is_postgres_available()

    if is_pg and pg_url:
        import sqlalchemy
        engine = sqlalchemy.create_engine(pg_url, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                existing = conn.execute(
                    sqlalchemy.text("SELECT username FROM users WHERE LOWER(username) = :u OR (email IS NOT NULL AND email != '' AND LOWER(email) = :e)"),
                    {"u": u_lower, "e": e_lower if e_lower else u_lower}
                ).fetchone()
                if existing:
                    return AuthResult(False, f"Username '{u_clean}' atau email '{e_clean}' sudah digunakan.")

            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("INSERT INTO users (username, password, role, email, full_name) VALUES (:u, :p, :r, :e, :f)"),
                    {"u": u_clean, "p": hashed, "r": role_to_save, "e": e_clean, "f": f_clean}
                )
            return AuthResult(True, f"Akun '{u_clean}' berhasil didaftarkan.")
        except Exception as err:
            return AuthResult(False, f"Gagal mendaftarkan akun: {err}")

    # SQLite
    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    try:
        # Cek apakah username atau email sudah ada
        if e_lower:
            cursor.execute(
                "SELECT username FROM users WHERE LOWER(username) = ? OR (email IS NOT NULL AND email != '' AND LOWER(email) = ?)",
                (u_lower, e_lower)
            )
        else:
            cursor.execute("SELECT username FROM users WHERE LOWER(username) = ?", (u_lower,))
        if cursor.fetchone():
            conn.close()
            return AuthResult(False, f"Username '{u_clean}' atau email sudah terdaftar.")

        cursor.execute(
            "INSERT INTO users (username, password, role, email, full_name) VALUES (?, ?, ?, ?, ?)",
            (u_clean, hashed, role_to_save, e_clean, f_clean)
        )
        conn.commit()
        conn.close()
        return AuthResult(True, f"Akun '{u_clean}' berhasil didaftarkan.")
    except Exception as err:
        conn.close()
        return AuthResult(False, f"Gagal mendaftarkan akun: {err}")


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
) -> Tuple[bool, str]:
    """
    Memperbarui kredensial dan data profil pengguna (username, kata sandi, email, nama lengkap).
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
            with engine.connect() as conn:
                user_row = conn.execute(
                    sqlalchemy.text("SELECT username, password, role, email, full_name FROM users WHERE LOWER(username) = :u"),
                    {"u": c_u_lower}
                ).fetchone()
                if not user_row:
                    return False, f"Akun '{c_u}' tidak ditemukan."

                if target_u_lower != c_u_lower:
                    conflict = conn.execute(
                        sqlalchemy.text("SELECT username FROM users WHERE LOWER(username) = :u"),
                        {"u": target_u_lower}
                    ).fetchone()
                    if conflict:
                        return False, f"Username '{target_u}' sudah digunakan oleh pengguna lain."

            pwd_to_save = user_row[1]
            if new_password and new_password.strip():
                if len(new_password.strip()) < 4:
                    return False, "Kata sandi baru minimal 4 karakter."
                pwd_to_save = hash_password(new_password.strip())

            email_to_save = new_email.strip() if new_email is not None else (user_row[3] or "")
            name_to_save = new_full_name.strip() if new_full_name is not None else (user_row[4] or "")

            with engine.begin() as conn:
                conn.execute(
                    sqlalchemy.text("UPDATE users SET username = :new_u, password = :p, email = :e, full_name = :f WHERE LOWER(username) = :old_u"),
                    {"new_u": target_u, "p": pwd_to_save, "e": email_to_save, "f": name_to_save, "old_u": c_u_lower}
                )
                if target_u_lower != c_u_lower:
                    conn.execute(
                        sqlalchemy.text("UPDATE predictions SET username = :new_u WHERE LOWER(username) = :old_u"),
                        {"new_u": target_u, "old_u": c_u_lower}
                    )
            return True, "Profil dan kredensial akun berhasil diperbarui."
        except Exception as err:
            return False, f"Gagal memperbarui profil: {err}"

    # SQLite Lokal
    conn = _get_sqlite_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, password, role, email, full_name FROM users WHERE LOWER(username) = ?", (c_u_lower,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            return False, f"Akun '{c_u}' tidak ditemukan."

        if target_u_lower != c_u_lower:
            cursor.execute("SELECT username FROM users WHERE LOWER(username) = ?", (target_u_lower,))
            if cursor.fetchone():
                conn.close()
                return False, f"Username '{target_u}' sudah digunakan oleh pengguna lain."

        pwd_to_save = user_row[1]
        if new_password and new_password.strip():
            if len(new_password.strip()) < 4:
                conn.close()
                return False, "Kata sandi baru minimal 4 karakter."
            pwd_to_save = hash_password(new_password.strip())

        email_to_save = new_email.strip() if new_email is not None else (user_row[3] or "")
        name_to_save = new_full_name.strip() if new_full_name is not None else (user_row[4] or "")

        cursor.execute(
            "UPDATE users SET username = ?, password = ?, email = ?, full_name = ? WHERE LOWER(username) = ?",
            (target_u, pwd_to_save, email_to_save, name_to_save, c_u_lower)
        )
        if target_u_lower != c_u_lower:
            cursor.execute("UPDATE predictions SET username = ? WHERE LOWER(username) = ?", (target_u, c_u_lower))
        conn.commit()
        conn.close()
        return True, "Profil dan kredensial akun berhasil diperbarui."
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
