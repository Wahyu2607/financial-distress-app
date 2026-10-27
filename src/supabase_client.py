from __future__ import annotations

import os
from typing import Optional

try:
    import streamlit as st
except ImportError:
    st = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from supabase import create_client, Client
    SUPABASE_SDK_AVAILABLE = True
except ImportError:
    create_client = None
    Client = None
    SUPABASE_SDK_AVAILABLE = False


def get_supabase_url() -> Optional[str]:
    """Mengambil SUPABASE_URL dari Streamlit Secrets atau Environment Variable."""
    if st is not None:
        try:
            if hasattr(st, "secrets") and "SUPABASE_URL" in st.secrets:
                return str(st.secrets["SUPABASE_URL"]).strip()
        except Exception:
            pass
    return os.environ.get("SUPABASE_URL", "").strip() or None


def get_supabase_anon_key() -> Optional[str]:
    """Mengambil SUPABASE_ANON_KEY dari Streamlit Secrets atau Environment Variable."""
    if st is not None:
        try:
            if hasattr(st, "secrets") and "SUPABASE_ANON_KEY" in st.secrets:
                return str(st.secrets["SUPABASE_ANON_KEY"]).strip()
        except Exception:
            pass
    return os.environ.get("SUPABASE_ANON_KEY", "").strip() or None


def get_supabase_service_role_key() -> Optional[str]:
    """
    Mengambil SUPABASE_SERVICE_ROLE_KEY untuk skrip administrasi server (bootstrap).
    PERINGATAN: Kunci ini tidak boleh dipublikasikan ke sisi client / frontend.
    """
    if st is not None:
        try:
            if hasattr(st, "secrets") and "SUPABASE_SERVICE_ROLE_KEY" in st.secrets:
                return str(st.secrets["SUPABASE_SERVICE_ROLE_KEY"]).strip()
        except Exception:
            pass
    return os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip() or None


def is_supabase_configured() -> bool:
    """Mengecek apakah SDK Supabase terpasang dan kredensial (URL & Anon Key) sudah diset."""
    if not SUPABASE_SDK_AVAILABLE:
        return False
    url = get_supabase_url()
    key = get_supabase_anon_key()
    return bool(url and key and not url.startswith("https://your-project-id"))


# Cache client anon agar tidak membuat koneksi baru berulang kali di Streamlit
_cached_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """
    Mengembalikan client Supabase publik (Anon Key) untuk operasi otentikasi
    dan query pengguna yang mematuhi aturan Row Level Security (RLS).
    """
    global _cached_client
    if not is_supabase_configured():
        return None

    if _cached_client is not None:
        return _cached_client

    url = get_supabase_url()
    anon_key = get_supabase_anon_key()

    try:
        _cached_client = create_client(url, anon_key)
        return _cached_client
    except Exception as exc:
        print(f"[Supabase Client Error] Gagal menginisialisasi client: {exc}")
        return None


def get_supabase_admin_client(service_role_key: Optional[str] = None) -> Optional[Client]:
    """
    Mengembalikan client Supabase administratif dengan Service Role Key.
    HANYA digunakan untuk script bootstrap awal di lingkungan lokal tepercaya.
    """
    if not SUPABASE_SDK_AVAILABLE:
        return None

    url = get_supabase_url()
    key = service_role_key or get_supabase_service_role_key()

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception as exc:
        print(f"[Supabase Admin Client Error] Gagal menginisialisasi admin client: {exc}")
        return None
