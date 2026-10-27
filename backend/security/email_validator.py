from __future__ import annotations

import re
import socket
from typing import Tuple, List, Optional
from backend.config import settings

# Daftar domain email sekali pakai / disposable yang wajib diblokir
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "throwawaymail.com",
    "guerrillamail.com", "yopmail.com", "trashmail.com", "sharklasers.com",
    "dispostable.com", "getairmail.com", "fake.com", "test.com", "example.com",
    "generator.email", "temp-mail.org", "nada.ltd", "mohmal.com", "burnermail.io"
}

# Kamus deteksi salah ketik / typo umum untuk panduan perbaikan
TYPO_DOMAIN_MAP = {
    "google.com": "Domain '@google.com' bukan layanan email publik. Gunakan '@gmail.com'.",
    "gmai.com": "Salah ketik pada domain '@gmai.com'. Gunakan '@gmail.com'.",
    "gamil.com": "Salah ketik pada domain '@gamil.com'. Gunakan '@gmail.com'.",
    "gmial.com": "Salah ketik pada domain '@gmial.com'. Gunakan '@gmail.com'.",
    "gmaill.com": "Salah ketik pada domain '@gmaill.com'. Gunakan '@gmail.com'.",
    "gmail.con": "Salah ketik pada ekstensi '@gmail.con'. Gunakan '@gmail.com'.",
    "gmail.co": "Salah ketik pada domain '@gmail.co'. Gunakan '@gmail.com'.",
    "yaho.com": "Salah ketik pada domain '@yaho.com'. Gunakan '@yahoo.com'.",
    "hotmial.com": "Salah ketik pada domain '@hotmial.com'. Gunakan '@hotmail.com'.",
    "outlok.com": "Salah ketik pada domain '@outlok.com'. Gunakan '@outlook.com'.",
}

NON_EMAIL_PLATFORMS = {
    "facebook.com": "Domain '@facebook.com' bukan penyedia email akun.",
    "instagram.com": "Domain '@instagram.com' bukan penyedia email akun.",
    "twitter.com": "Domain '@twitter.com' bukan penyedia email akun.",
    "tiktok.com": "Domain '@tiktok.com' bukan penyedia email akun.",
    "youtube.com": "Domain '@youtube.com' bukan penyedia email akun.",
}

RESERVED_USERNAMES = {
    "admin", "administrator", "root", "superuser", "system", "moderator",
    "support", "owner", "guest", "anonymous", "null", "undefined", "operator"
}


def normalize_email(email: str) -> str:
    """Normalisasi alamat email ke bentuk huruf kecil dan menghapus spasi ekstra."""
    if not email:
        return ""
    return email.strip().lower()


def check_mx_record(domain: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """
    Memeriksa keberadaan record MX / DNS host untuk domain email.
    Mendukung dnspython jika terinstal, atau fallback ke socket.getaddrinfo dengan timeout.
    """
    clean_domain = domain.strip().lower()

    # Cek dnspython jika terinstal
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.lifetime = timeout
        resolver.timeout = timeout
        try:
            records = resolver.resolve(clean_domain, "MX")
            if records and len(records) > 0:
                return True, "MX record ditemukan."
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return False, f"Domain '@{clean_domain}' tidak memiliki mail server (MX record) yang valid."
        except dns.exception.Timeout:
            return False, f"Pemeriksaan DNS untuk domain '@{clean_domain}' mengalami timeout."
        except Exception as e:
            return False, f"Gagal memverifikasi DNS domain: {str(e)}"
    except ImportError:
        pass

    # Fallback menggunakan socket standar Python
    try:
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            # Domain harus dapat di-resolve ke IP address
            socket.gethostbyname(clean_domain)
            return True, "Host domain berhasil di-resolve."
        except socket.gaierror:
            return False, f"Domain '@{clean_domain}' tidak terdaftar atau tidak dapat dihubungi melalui DNS."
        except socket.timeout:
            return False, f"Pemeriksaan DNS untuk domain '@{clean_domain}' waktu habis (timeout)."
        finally:
            socket.setdefaulttimeout(old_timeout)
    except Exception as e:
        return False, f"Gagal memverifikasi DNS domain: {str(e)}"


def validate_email_address(email: str, verify_dns: Optional[bool] = None) -> Tuple[bool, str]:
    """
    Validasi komprehensif email:
    1. Format RFC & panjang batas (max 254 karakter)
    2. Blokir typo domain populer (@google.com, .con)
    3. Blokir domain platform non-email
    4. Blokir email sekali pakai (disposable email)
    5. Pembatasan domain organisasi (jika ALLOWED_EMAIL_DOMAINS diset)
    6. Pemeriksaan DNS MX record jika CHECK_DNS_MX aktif
    """
    if not email:
        return False, "Alamat email wajib diisi."

    clean_email = normalize_email(email)

    if len(clean_email) > 254:
        return False, "Alamat email terlalu panjang (maksimal 254 karakter)."

    # Regex validasi email ketat
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, clean_email):
        return False, "Format alamat email tidak valid (contoh: nama@domain.com atau nama@instansi.ac.id)."

    parts = clean_email.split("@")
    if len(parts) != 2:
        return False, "Format alamat email tidak valid."

    local_part, domain = parts[0].strip(), parts[1].strip()

    if len(local_part) > 64:
        return False, "Bagian nama akun email terlalu panjang (maksimal 64 karakter)."

    # 1. Cek Typo Domain
    if domain in TYPO_DOMAIN_MAP:
        return False, f"Bentuk penulisan email salah: {TYPO_DOMAIN_MAP[domain]}"

    if domain in NON_EMAIL_PLATFORMS:
        return False, f"Bentuk penulisan email salah: {NON_EMAIL_PLATFORMS[domain]}"

    if domain.endswith(".con"):
        return False, f"Salah ketik: domain '@{domain}' berakhiran '.con'. Maksud Anda berakhiran '.com'?"

    # 2. Cek Disposable Email
    if domain in DISPOSABLE_DOMAINS:
        return False, "Domain email sementara/disposable tidak diizinkan demi keamanan akun."

    # 3. Cek Kebijakan Domain Organisasi Terbatas
    if settings.ALLOWED_EMAIL_DOMAINS:
        if domain not in settings.ALLOWED_EMAIL_DOMAINS:
            allowed_str = ", ".join(settings.ALLOWED_EMAIL_DOMAINS)
            return False, f"Pendaftaran dibatasi hanya untuk domain yang disetujui: {allowed_str}."

    # 4. Validasi Struktur & Kategori Domain (Wajib Google/Yahoo/Outlook atau Instansi Resmi)
    domain_parts = domain.split(".")
    if len(domain_parts) < 2 or len(domain_parts[-1]) < 2:
        return False, f"Domain email '@{domain}' tidak lengkap atau tidak valid."

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

    # 5. Pemeriksaan DNS MX Record
    do_dns = verify_dns if verify_dns is not None else settings.CHECK_DNS_MX
    if do_dns:
        ok_mx, msg_mx = check_mx_record(domain, timeout=settings.DNS_TIMEOUT_SECONDS)
        if not ok_mx:
            return False, msg_mx

    return True, ""


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validasi kebijakan kekuatan kata sandi:
    - Minimal panjang sesuai konfigurasi (default 8)
    - Mengandung huruf besar dan kecil
    - Mengandung angka atau simbol
    - Menolak kata sandi terlalu umum / sederhana
    """
    if not password:
        return False, "Kata sandi wajib diisi."

    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Kata sandi harus memiliki panjang minimal {settings.PASSWORD_MIN_LENGTH} karakter."

    if not re.search(r"[a-z]", password):
        return False, "Kata sandi harus mengandung minimal satu huruf kecil (a-z)."

    if not re.search(r"[A-Z]", password):
        return False, "Kata sandi harus mengandung minimal satu huruf besar (A-Z)."

    if not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Kata sandi harus mengandung minimal satu angka (0-9) atau simbol unik."

    common_passwords = {"password", "12345678", "admin123", "qwertyuiop", "administrator"}
    if password.lower() in common_passwords:
        return False, "Kata sandi terlalu umum dan mudah ditebak. Gunakan kombinasi yang lebih aman."

    return True, ""


def validate_username_policy(username: str) -> Tuple[bool, str]:
    """
    Validasi aturan username:
    - Panjang 3 hingga 30 karakter
    - Alfanumerik dan garis bawah (_) saja
    - Tidak boleh menggunakan kata terlarang sistem (admin, root, dsb.)
    """
    if not username:
        return False, "Username wajib diisi."

    clean_u = username.strip().lower()

    if len(clean_u) < 3 or len(clean_u) > 30:
        return False, "Username harus memiliki panjang antara 3 hingga 30 karakter."

    if not re.match(r"^[a-zA-Z0-9_]+$", clean_u):
        return False, "Username hanya boleh mengandung huruf, angka, dan garis bawah (_)."

    if clean_u in RESERVED_USERNAMES:
        return False, f"Username '{clean_u}' merupakan kata cadangan sistem dan tidak dapat digunakan."

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
