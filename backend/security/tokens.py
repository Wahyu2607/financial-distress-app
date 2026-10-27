from __future__ import annotations

import base64
import json
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from backend.config import settings


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("ascii"))


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Membuat JSON Web Token (JWT) yang ditandatangani dengan HMAC-SHA256.
    Implementasi independen murni Python untuk portabilitas maksimal tanpa ketergantungan library luar.
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16),  # Unique token ID
    })

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(to_encode, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256
    ).digest()
    sig_b64 = _base64url_encode(signature)

    return f"{signing_input}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Memverifikasi tanda tangan kriptografis dan masa berlaku JWT.
    Mengembalikan payload dict jika valid, atau None jika token cacat/kedaluwarsa.
    """
    if not token or token.count(".") != 2:
        return None

    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"

        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256
        ).digest()

        actual_sig = _base64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Cek kedaluwarsa
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            return None

        return payload
    except Exception:
        return None


def generate_secure_token(nbytes: int = 32) -> str:
    """Menghasilkan string token acak kriptografis (misal untuk email confirmation link & password reset)."""
    return secrets.token_urlsafe(nbytes)


def generate_otp(length: int = 6) -> str:
    """Menghasilkan kode numerik acak kriptografis (misal 6 digit OTP)."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))
