#!/usr/bin/env python3
"""
==============================================================================
SKRIP ADMINISTRASI: BOOTSTRAP AKUN ADMINISTRATOR AWAL
Project: Financial Distress Prediction System
==============================================================================
Skrip ini digunakan oleh Pemilik Proyek / DevOps Engineer untuk membuat
atau mempromosikan akun Administrator pertama secara aman di Supabase.

PANDUAN KEAMANAN:
- Skrip ini membutuhkan SUPABASE_SERVICE_ROLE_KEY.
- HANYA jalankan skrip ini di terminal lokal atau server tepercaya.
- JANGAN PERNAH menyertakan service role key di repositori publik atau commit git.
- Kata sandi diinput secara interaktif melalui getpass (tidak terlihat di layar).
==============================================================================
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

# Tambahkan direktori root proyek ke path Python
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from src.supabase_client import (
        get_supabase_url,
        get_supabase_service_role_key,
        get_supabase_admin_client,
    )
    from src.auth import (
        validate_email,
        validate_password,
        validate_username,
        validate_full_name,
    )
except ImportError as e:
    print(f"❌ Error importing module: {e}")
    sys.exit(1)


def print_banner():
    print("=" * 72)
    print("  🛡️  SUPABASE INITIAL ADMIN BOOTSTRAP UTILITY")
    print("  Financial Distress Prediction System")
    print("=" * 72)


def main():
    print_banner()

    # 1. Periksa ketersediaan Supabase URL dan Service Role Key
    supabase_url = get_supabase_url()
    service_key = get_supabase_service_role_key()

    if not supabase_url:
        print("⚠️  SUPABASE_URL belum ditemukan di environment atau secrets.")
        supabase_url = input("Masukkan Supabase Project URL (contoh: https://xyz.supabase.co): ").strip()
        if not supabase_url:
            print("❌ Error: SUPABASE_URL wajib diisi.")
            sys.exit(1)

    if not service_key:
        print("⚠️  SUPABASE_SERVICE_ROLE_KEY belum ditemukan di environment.")
        print("   (Dapatkan dari: Supabase Dashboard -> Project Settings -> API -> service_role key)")
        service_key = getpass.getpass("Masukkan Supabase Service Role Key: ").strip()
        if not service_key:
            print("❌ Error: Service Role Key wajib diisi untuk operasi bootstrap.")
            sys.exit(1)

    # 2. Inisialisasi client admin
    admin_client = get_supabase_admin_client(service_role_key=service_key)
    if not admin_client:
        print("❌ Error: Gagal menginisialisasi Supabase Admin Client. Periksa URL dan Service Key Anda.")
        sys.exit(1)

    print("\n✅ Supabase Admin Client berhasil terhubung!")
    print("\nPilih Operasi Bootstrap:")
    print("1. Buat Akun Administrator Baru (Supabase Auth + Role Admin)")
    print("2. Promosikan Pengguna yang Sudah Terdaftar Menjadi Administrator")
    print("3. Tampilkan Daftar Administrator Aktif Saat Ini")
    print("4. Keluar")

    choice = input("\nPilihan Anda (1/2/3/4): ").strip()

    if choice == "1":
        bootstrap_new_admin(admin_client)
    elif choice == "2":
        promote_existing_user(admin_client)
    elif choice == "3":
        list_active_admins(admin_client)
    else:
        print("\nSelesai. Tidak ada perubahan yang dilakukan.")
        sys.exit(0)


def bootstrap_new_admin(client):
    print("\n--- ➕ PEMBUATAN AKUN ADMINISTRATOR BARU ---")

    # Input Email
    email = input("Email Administrator: ").strip().lower()
    val_e, err_e = validate_email(email)
    if not val_e:
        print(f"❌ Error: {err_e}")
        return

    # Input Full Name
    full_name = input("Nama Lengkap Administrator: ").strip()
    val_fn, err_fn = validate_full_name(full_name)
    if not val_fn:
        print(f"❌ Error: {err_fn}")
        return

    # Input Username
    username = input("Username Administrator (contoh: super_admin): ").strip().lower()
    if not username:
        username = "admin_" + email.split("@")[0]
    
    # Input Kata Sandi
    password = getpass.getpass("Kata Sandi Administrator (min. 8 karakter): ")
    val_p, err_p = validate_password(password)
    if not val_p:
        print(f"❌ Error: {err_p}")
        return

    confirm_pass = getpass.getpass("Konfirmasi Kata Sandi: ")
    if password != confirm_pass:
        print("❌ Error: Konfirmasi kata sandi tidak cocok!")
        return

    print("\n⏳ Mendaftarkan akun ke Supabase Auth...")
    try:
        # 1. Buat akun di auth.users dengan email_confirm=True via Admin API
        user_res = client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name,
                "username": username
            }
        })
        user = user_res.user
        if not user:
            print("❌ Gagal membuat user di Supabase Auth.")
            return

        print(f"✅ Akun Auth berhasil dibuat dengan UUID: {user.id}")

        # 2. Pastikan atau update record di public.profiles dengan role 'admin'
        print("⏳ Menetapkan role 'admin' dan status 'active' di public.profiles...")
        profile_data = {
            "id": user.id,
            "full_name": full_name,
            "username": username,
            "email": email,
            "role": "admin",
            "status": "active",
            "institution": "System Administrator",
        }

        # Gunakan upsert agar jika trigger on_auth_user_created sudah jalan, role langsung diupdate ke admin
        upsert_res = client.table("profiles").upsert(profile_data).execute()
        if upsert_res.data:
            print("🎉 SUKSES! Akun Administrator berhasil dibuat dan diotorisasi:")
            print(f"   - Email: {email}")
            print(f"   - Username: {username}")
            print(f"   - Role: admin")
            print(f"   - Status: active")
            print("\nAnda sekarang dapat masuk ke aplikasi web melalui menu 'Login Admin'.")
        else:
            print("⚠️ User auth dibuat, tetapi gagal memperbarui role di tabel profiles.")

    except Exception as exc:
        print(f"❌ Gagal memproses pembuatan Admin: {exc}")


def promote_existing_user(client):
    print("\n--- ⬆️ PROMOSI PENGGUNA TERDAFTAR MENJADI ADMIN ---")
    ident = input("Masukkan Email atau Username pengguna: ").strip().lower()
    if not ident:
        print("❌ Identitas pengguna tidak boleh kosong.")
        return

    try:
        # Cari di tabel profiles
        query = client.table("profiles").select("*")
        if "@" in ident:
            res = query.eq("email", ident).execute()
        else:
            res = query.eq("username", ident).execute()

        if not res.data:
            print(f"❌ Pengguna dengan identitas '{ident}' tidak ditemukan di tabel profiles.")
            return

        user_prof = res.data[0]
        user_id = user_prof["id"]
        current_role = user_prof.get("role", "user")

        print(f"Ditemukan: {user_prof.get('full_name')} (@{user_prof.get('username')}) - Role saat ini: {current_role}")

        if current_role == "admin":
            print("ℹ️ Pengguna ini sudah memiliki role 'admin'.")
            return

        confirm = input("Apakah Anda yakin ingin menaikkan hak akses pengguna ini menjadi ADMIN? (y/N): ").strip().lower()
        if confirm != "y":
            print("Dibatalkan.")
            return

        update_res = client.table("profiles").update({"role": "admin", "status": "active"}).eq("id", user_id).execute()
        if update_res.data:
            print(f"🎉 SUKSES! Pengguna '{user_prof.get('username')}' sekarang berstatus ADMINISTRATOR.")
        else:
            print("❌ Gagal memperbarui role.")

    except Exception as exc:
        print(f"❌ Error: {exc}")


def list_active_admins(client):
    print("\n--- 📋 DAFTAR ADMINISTRATOR SISTEM AKTIF ---")
    try:
        res = client.table("profiles").select("id, full_name, username, email, role, status, created_at").eq("role", "admin").execute()
        admins = res.data or []
        if not admins:
            print("⚠️ Belum ada akun dengan role 'admin' di database.")
            return

        print(f"Total Administrator: {len(admins)}\n")
        print(f"{'No':<4} {'Username':<18} {'Nama Lengkap':<26} {'Email':<30} {'Status':<10}")
        print("-" * 90)
        for idx, adm in enumerate(admins, 1):
            print(f"{idx:<4} {adm.get('username', '-'):<18} {adm.get('full_name', '-'):<26} {adm.get('email', '-'):<30} {adm.get('status', '-'):<10}")

    except Exception as exc:
        print(f"❌ Gagal mengambil data: {exc}")


if __name__ == "__main__":
    main()
