from __future__ import annotations

import time
import threading
from typing import Dict, List, Tuple


class SlidingWindowRateLimiter:
    """
    Rate limiter berbasis sliding window memory yang thread-safe.
    Digunakan untuk membatasi:
    - Percobaan login per IP / user (mencegah brute-force)
    - Pendaftaran per IP (mencegah spam pendaftaran akun)
    - Permintaan kirim ulang OTP (mencegah spam email)
    """

    def __init__(self):
        self._lock = threading.Lock()
        # Key: identifier -> List of timestamps
        self._requests: Dict[str, List[float]] = {}
        # Key: identifier -> locked_until timestamp
        self._lockouts: Dict[str, float] = {}

    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        lockout_seconds: int = 0
    ) -> Tuple[bool, int]:
        """
        Memeriksa apakah permintaan melampaui batas yang ditentukan.
        Returns:
            (is_limited: bool, retry_after_seconds: int)
        """
        now = time.time()

        with self._lock:
            # 1. Cek apakah key sedang dalam masa lockout (hukuman blokir sementara)
            locked_until = self._lockouts.get(key, 0)
            if now < locked_until:
                return True, int(locked_until - now)
            elif key in self._lockouts:
                del self._lockouts[key]

            # 2. Ambil riwayat timestamp dan bersihkan yang di luar window
            history = self._requests.get(key, [])
            window_start = now - window_seconds
            valid_history = [t for t in history if t > window_start]

            if len(valid_history) >= max_requests:
                # Terapkan lockout jika diatur
                if lockout_seconds > 0:
                    self._lockouts[key] = now + lockout_seconds
                    self._requests[key] = []
                    return True, lockout_seconds

                oldest_in_window = valid_history[0]
                retry_after = int(oldest_in_window + window_seconds - now)
                return True, max(1, retry_after)

            # Tambahkan timestamp baru
            valid_history.append(now)
            self._requests[key] = valid_history
            return False, 0

    def reset(self, key: str) -> None:
        """Mereset riwayat dan lockout untuk key tertentu (misal setelah login berhasil)."""
        with self._lock:
            if key in self._requests:
                del self._requests[key]
            if key in self._lockouts:
                del self._lockouts[key]


# Singleton rate limiter instance
limiter = SlidingWindowRateLimiter()
