from __future__ import annotations

import hashlib
import hmac
import secrets

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _argon2_hasher = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1)
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False


def hash_password(password: str) -> str:
    """
    Hash password menggunakan standar industri yang aman:
    - Argon2id jika argon2-cffi tersedia.
    - Fallback ke PBKDF2-HMAC-SHA256 (100,000 iterasi + salt acak) standar Python hashlib.
    """
    if not password:
        raise ValueError("Password tidak boleh kosong")

    if HAS_ARGON2:
        return _argon2_hasher.hash(password)

    # Standar PBKDF2-HMAC-SHA256
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Memverifikasi password secara aman dengan constant-time comparison.
    Mendukung Argon2id, PBKDF2-HMAC-SHA256, dan fallback jika ada password lama.
    """
    if not plain_password or not stored_hash:
        return False

    # 1. Cek format Argon2
    if stored_hash.startswith("$argon2"):
        if HAS_ARGON2:
            try:
                return _argon2_hasher.verify(stored_hash, plain_password)
            except VerifyMismatchError:
                return False
            except Exception:
                return False
        return False

    # 2. Cek format PBKDF2
    if stored_hash.startswith("pbkdf2:sha256:"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 3:
                _, salt, key_hex = parts
                test_key = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain_password.encode("utf-8"),
                    salt.encode("utf-8"),
                    100000,
                )
                return hmac.compare_digest(test_key.hex(), key_hex)
        except Exception:
            return False

    # 3. Fallback constant-time untuk string hashing lain
    return hmac.compare_digest(plain_password, stored_hash)


def hash_token(raw_token: str) -> str:
    """
    Menghasilkan hash SHA-256 untuk token reset password, token verifikasi, dan session token.
    Token rahasia tidak pernah disimpan dalam bentuk mentah di database.
    """
    if not raw_token:
        return ""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
