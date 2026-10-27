from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

try:
    from dotenv import load_dotenv
    # Load .env file jika ada di root project
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    # 1. Aplikasi
    APP_NAME: str = os.getenv("APP_NAME", "Financial Distress Auth Service")
    APP_ENV: str = os.getenv("APP_ENV", "development")  # development / production
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    API_V1_STR: str = "/api/v1"

    # 2. Database
    # Default menggunakan SQLite lokal jika DATABASE_URL tidak diisi
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'financial_distress.db'}"
    )

    # 3. Kriptografi & Token (JWT & Sesi)
    # Wajib diubah pada lingkungan produksi menggunakan secrets.token_hex(32)
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "super-secret-key-change-in-production-min-32-chars-length-123456"
    )
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # 4. Kebijakan Keamanan Password & Login
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    MAX_LOGIN_FAILED_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_FAILED_ATTEMPTS", "5"))
    ACCOUNT_LOCKOUT_MINUTES: int = int(os.getenv("ACCOUNT_LOCKOUT_MINUTES", "15"))

    # 5. Kebijakan Verifikasi Email & OTP
    REQUIRE_EMAIL_VERIFICATION: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "true").lower() in ("true", "1", "yes")
    EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES", "15"))
    OTP_LENGTH: int = int(os.getenv("OTP_LENGTH", "6"))
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    RESEND_COOLDOWN_SECONDS: int = int(os.getenv("RESEND_COOLDOWN_SECONDS", "60"))
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15"))

    # 6. Validasi Domain Email
    CHECK_DNS_MX: bool = os.getenv("CHECK_DNS_MX", "true").lower() in ("true", "1", "yes")
    DNS_TIMEOUT_SECONDS: float = float(os.getenv("DNS_TIMEOUT_SECONDS", "3.0"))
    # Jika diisi (comma-separated), hanya domain ini yang diizinkan (misal: "idx.co.id,ui.ac.id")
    # Jika kosong, semua domain publik valid & non-disposable diizinkan
    ALLOWED_EMAIL_DOMAINS: List[str] = [
        d.strip().lower() for d in os.getenv("ALLOWED_EMAIL_DOMAINS", "").split(",") if d.strip()
    ]

    # 7. Konfigurasi SMTP (Pengiriman Email Nyata)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@distress.ai")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Financial Distress Auth")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
    # Mode simulasi (mock) jika SMTP belum diset sehingga email dicetak ke console / log
    EMAIL_MOCK_MODE: bool = os.getenv("EMAIL_MOCK_MODE", "true").lower() in ("true", "1", "yes")

    # 8. Initial Admin Bootstrap (Hanya digunakan saat bootstrap pertama kali)
    INITIAL_ADMIN_EMAIL: str = os.getenv("INITIAL_ADMIN_EMAIL", "admin@distress.ai")
    INITIAL_ADMIN_USERNAME: str = os.getenv("INITIAL_ADMIN_USERNAME", "admin")
    INITIAL_ADMIN_FULLNAME: str = os.getenv("INITIAL_ADMIN_FULLNAME", "System Administrator")
    INITIAL_ADMIN_PASSWORD: Optional[str] = os.getenv("INITIAL_ADMIN_PASSWORD", None)

settings = Settings()
