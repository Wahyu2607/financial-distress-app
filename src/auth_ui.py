"""
Module: auth_ui.py
Deskripsi: Komponen antarmuka pengguna (UI) modern dan responsif untuk alur autentikasi publik:
           - User Login & Registrasi
           - Portal Khusus Login Admin
           - Permintaan & Pembaruan Reset Kata Sandi
           - Landing Page / Ikhtisar Platform
Terhubung langsung dengan Supabase Auth & PostgreSQL profiles via src.auth.
"""

import html
import re
import streamlit as st

from src.supabase_client import is_supabase_configured
from src.auth import (
    sign_in_user,
    sign_in_admin,
    sign_up_user,
    request_password_reset,
    update_user_password,
    validate_email,
    validate_password,
    validate_username,
    validate_full_name,
)


def _init_auth_session():
    """Inisialisasi state publik autentikasi bila belum disetel."""
    if "public_view" not in st.session_state:
        st.session_state.public_view = "login_user"
    if "auth_flash_success" not in st.session_state:
        st.session_state.auth_flash_success = ""
    if "auth_flash_error" not in st.session_state:
        st.session_state.auth_flash_error = ""


def _set_user_session(profile: dict, role: str):
    """Menyetel sesi pengguna setelah login terverifikasi."""
    st.session_state.logged_in = True
    st.session_state.user_id = profile.get("id", "")
    st.session_state.username = profile.get("username", "") or (profile.get("email", "").split("@")[0] if profile.get("email") else "user")
    st.session_state.role = role
    st.session_state.user_fullname = profile.get("full_name") or "Pengguna Sistem"
    st.session_state.user_email = profile.get("email", "")
    st.session_state.user_phone = profile.get("phone", "")
    st.session_state.user_institution = profile.get("institution", "")
    st.session_state.user_type = profile.get("user_type", "Pekerja / Profesional")
    st.session_state.user_position = profile.get("position", "")
    st.session_state.user_city = profile.get("city", "")
    st.session_state.user_bio = profile.get("bio", "")
    st.session_state.user_avatar = profile.get("avatar_url", "")
    st.session_state.page = "Dashboard"
    if hasattr(st, "query_params"):
        st.query_params.clear()


def render_auth_header():
    """Menampilkan header brand platform analitik financial distress."""
    st.markdown(
        """
        <style>
        .auth-container {
            max-width: 520px;
            margin: 0 auto;
            padding: 8px 0;
        }
        .auth-brand-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(37, 99, 235, 0.12);
            border: 1px solid rgba(37, 99, 235, 0.3);
            color: #2563eb;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }
        .auth-title {
            font-size: 26px;
            font-weight: 900;
            letter-spacing: -0.5px;
            margin-top: 10px;
            margin-bottom: 4px;
            color: #1e293b;
        }
        .auth-subtitle {
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
            line-height: 1.5;
            margin-bottom: 18px;
        }
        .auth-nav-pill-active {
            background: #2563eb;
            color: white;
            font-weight: 700;
            border-radius: 8px;
            padding: 8px 14px;
            text-align: center;
        }
        .admin-security-badge {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(245, 158, 11, 0.12) 100%);
            border: 1.5px solid rgba(239, 68, 68, 0.35);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_auth_navigation():
    """Bilah navigasi cepat antar halaman publik."""
    _init_auth_session()
    cur = st.session_state.public_view

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🏠 Beranda", use_container_width=True, type="primary" if cur == "landing" else "secondary"):
            st.session_state.public_view = "landing"
            st.rerun()
    with c2:
        if st.button("👤 Masuk User", use_container_width=True, type="primary" if cur == "login_user" else "secondary"):
            st.session_state.public_view = "login_user"
            st.rerun()
    with c3:
        if st.button("📝 Daftar Akun", use_container_width=True, type="primary" if cur == "register_user" else "secondary"):
            st.session_state.public_view = "register_user"
            st.rerun()
    with c4:
        if st.button("🛡️ Portal Admin", use_container_width=True, type="primary" if cur == "login_admin" else "secondary"):
            st.session_state.public_view = "login_admin"
            st.rerun()


def render_user_login():
    """Halaman Formulir Login Pengguna Biasa."""
    render_auth_header()

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:18px;">
            <div class="auth-brand-badge">🔐 Sistem Autentikasi Terverifikasi</div>
            <h2 class="auth-title">Masuk ke Akun Anda</h2>
            <div class="auth-subtitle">Akses platform analitik financial distress multi-model (Altman Z'', MDA, XGBoost AI)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_supabase_configured():
        st.warning(
            "⚠️ **Koneksi Supabase Belum Dikonfigurasi:** "
            "Sistem saat ini belum mendeteksi kredensial Supabase di `.streamlit/secrets.toml` atau environment variable. "
            "Silakan konfigurasi `SUPABASE_URL` dan `SUPABASE_ANON_KEY` sesuai panduan untuk mengaktifkan autentikasi cloud."
        )

    # Flash messages
    if st.session_state.auth_flash_success:
        st.success(st.session_state.auth_flash_success)
        st.session_state.auth_flash_success = ""
    if st.session_state.auth_flash_error:
        st.error(st.session_state.auth_flash_error)
        st.session_state.auth_flash_error = ""

    with st.container(border=True):
        with st.form("form_user_login", clear_on_submit=False):
            email = st.text_input("Alamat Email", placeholder="nama@email.com", key="auth_user_email")
            password = st.text_input("Kata Sandi", type="password", placeholder="Masukkan kata sandi akun Anda", key="auth_user_pwd")
            
            c_sub1, c_sub2 = st.columns([1.5, 1])
            with c_sub1:
                submit = st.form_submit_button("🚀 Masuk Sekarang", type="primary", use_container_width=True)
            with c_sub2:
                forgot = st.form_submit_button("🔑 Lupa Kata Sandi?", use_container_width=True)

        if forgot:
            st.session_state.public_view = "forgot_password"
            st.rerun()

        if submit:
            val_ok, err_msg = validate_email(email)
            if not val_ok:
                st.error(f"❌ {err_msg}")
            elif not password:
                st.error("❌ Kata sandi tidak boleh kosong.")
            else:
                with st.spinner("Memverifikasi kredensial akun..."):
                    ok, user, profile, err = sign_in_user(email, password)
                    if ok and profile:
                        _set_user_session(profile, role="user")
                        st.toast(f"Selamat datang, {st.session_state.user_fullname}!", icon="👋")
                        st.rerun()
                    else:
                        st.error(f"❌ {err or 'Kredensial login tidak valid.'}")

    # Footer navigation
    c_reg, c_adm = st.columns(2)
    with c_reg:
        if st.button("Belum punya akun? **Daftar di sini**", use_container_width=True):
            st.session_state.public_view = "register_user"
            st.rerun()
    with c_adm:
        if st.button("Pengelola Sistem? **Login Admin**", use_container_width=True):
            st.session_state.public_view = "login_admin"
            st.rerun()


def render_user_registration():
    """Halaman Formulir Pendaftaran Akun Pengguna Baru."""
    render_auth_header()

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:18px;">
            <div class="auth-brand-badge">📝 Registrasi Pengguna Baru</div>
            <h2 class="auth-title">Buat Akun Platform</h2>
            <div class="auth-subtitle">Daftarkan akun untuk menganalisis risiko kebangkrutan emiten Bursa Efek Indonesia</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not is_supabase_configured():
        st.warning("⚠️ **Pemberitahuan:** Supabase belum dikonfigurasi. Registrasi memerlukan koneksi aktif ke Supabase.")

    with st.container(border=True):
        with st.form("form_user_registration"):
            full_name = st.text_input("Nama Lengkap", placeholder="Contoh: Sarah Wijaya", help="Nama lengkap resmi Anda")
            username = st.text_input("Username (Nama Pengguna)", placeholder="Contoh: sarah_w", help="3-30 karakter: huruf kecil, angka, garis bawah")
            email = st.text_input("Alamat Email", placeholder="sarah@email.com", help="Gunakan alamat email aktif Anda")
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                password = st.text_input("Kata Sandi", type="password", placeholder="Min. 8 karakter (huruf & angka)", help="Minimal 8 karakter, wajib kombinasi huruf besar/kecil dan angka/simbol")
            with c_p2:
                password_confirm = st.text_input("Konfirmasi Kata Sandi", type="password", placeholder="Ulangi kata sandi")

            agree_terms = st.checkbox("Saya menyetujui ketentuan penggunaan dan pemrosesan data analisis finansial.")

            submit_reg = st.form_submit_button("✨ Buat Akun Pengguna", type="primary", use_container_width=True)

        if submit_reg:
            # Validasi nama lengkap
            fn_ok, fn_msg = validate_full_name(full_name)
            if not fn_ok:
                st.error(f"❌ {fn_msg}")
                return

            # Validasi username
            u_ok, u_msg = validate_username(username)
            if not u_ok:
                st.error(f"❌ {u_msg}")
                return

            # Validasi email
            e_ok, e_msg = validate_email(email)
            if not e_ok:
                st.error(f"❌ {e_msg}")
                return

            # Validasi kata sandi
            p_ok, p_msg = validate_password(password)
            if not p_ok:
                st.error(f"❌ {p_msg}")
                return

            # Konfirmasi kesesuaian sandi
            if password != password_confirm:
                st.error("❌ Konfirmasi kata sandi tidak cocok. Harap periksa kembali.")
                return

            # Persetujuan syarat & ketentuan
            if not agree_terms:
                st.error("❌ Anda wajib menyetujui ketentuan penggunaan sebelum melanjutkan pendaftaran.")
                return

            # Eksekusi registrasi aman (selalu role='user')
            with st.spinner("Membuat akun di basis data Supabase..."):
                ok, user, msg, is_email_req = sign_up_user(
                    email=email.strip().lower(),
                    password=password,
                    confirm_password=password_confirm,
                    full_name=full_name.strip(),
                    username=username.strip().lower(),
                    agreed_terms=agree_terms,
                )
                if ok:
                    st.session_state.auth_flash_success = f"🎉 {msg}"
                    st.session_state.public_view = "login_user"
                    st.rerun()
                else:
                    st.error(f"❌ Pendaftaran gagal: {msg}")

    st.markdown("<div style='text-align:center; margin-top:10px;'>", unsafe_allow_html=True)
    if st.button("Sudah memiliki akun? **Masuk ke Akun Anda**", use_container_width=True):
        st.session_state.public_view = "login_user"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def render_admin_login():
    """Halaman Formulir Login Khusus Administrator."""
    render_auth_header()

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:14px;">
            <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(239, 68, 68, 0.12); border:1px solid rgba(239, 68, 68, 0.35); color:#ef4444; padding:4px 12px; border-radius:999px; font-size:11px; font-weight:800; letter-spacing:0.8px; text-transform:uppercase;">
                🛡️ Restricted Administrative Portal
            </div>
            <h2 class="auth-title" style="color:#b91c1c;">Login Administrator</h2>
            <div class="auth-subtitle">Gerbang otentikasi khusus pengelola sistem, manajemen model, dan audit prediksi</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="admin-security-badge">
            <span style="font-size:24px;">🔒</span>
            <div style="font-size:12px; color:#991b1b; line-height:1.45;">
                <strong>Perhatian Keamanan:</strong> Portal ini dilindungi oleh otorisasi berbasis peran (Role-Based Access Control). 
                Akun pengguna biasa yang mencoba login di sini akan otomatis ditolak dan sesinya ditutup secara aman.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        with st.form("form_admin_login"):
            admin_email = st.text_input("Alamat Email Administrator", placeholder="admin@domain.com", key="auth_adm_email")
            admin_password = st.text_input("Kata Sandi Administrator", type="password", placeholder="Masukkan kata sandi admin", key="auth_adm_pwd")

            submit_adm = st.form_submit_button("🛡️ Masuk sebagai Administrator", type="primary", use_container_width=True)

        if submit_adm:
            val_ok, err_msg = validate_email(admin_email)
            if not val_ok:
                st.error(f"❌ {err_msg}")
            elif not admin_password:
                st.error("❌ Kata sandi Administrator tidak boleh kosong.")
            else:
                with st.spinner("Memvalidasi hak akses administratif..."):
                    ok, user, profile, err = sign_in_admin(admin_email, admin_password)
                    if ok and profile:
                        _set_user_session(profile, role="admin")
                        st.toast(f"Selamat datang Administrator: {st.session_state.user_fullname}!", icon="🛡️")
                        st.rerun()
                    else:
                        st.error(f"❌ {err or 'Akses ditolak: Kredensial Administrator salah.'}")

    c_b1, c_b2 = st.columns(2)
    with c_b1:
        if st.button("⬅️ Kembali ke Login Pengguna", use_container_width=True):
            st.session_state.public_view = "login_user"
            st.rerun()
    with c_b2:
        if st.button("ℹ️ Panduan Inisialisasi Admin", use_container_width=True):
            st.info(
                "Untuk membuat akun Admin pertama secara aman, jalankan skrip bootstrap CLI lokal:\n"
                "`python scripts/bootstrap_admin.py`\n"
                "Pendaftaran Admin publik dilarang demi keamanan sistem."
            )


def render_forgot_password():
    """Halaman Permintaan Reset Kata Sandi Pengguna."""
    render_auth_header()

    st.markdown(
        """
        <div style="text-align:center; margin-bottom:18px;">
            <div class="auth-brand-badge">🔑 Pemulihan Akun</div>
            <h2 class="auth-title">Reset Kata Sandi</h2>
            <div class="auth-subtitle">Masukkan alamat email terdaftar Anda untuk menerima tautan pemulihan sandi</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        with st.form("form_forgot_password"):
            reset_email = st.text_input("Alamat Email Terdaftar", placeholder="nama@email.com")
            submit_reset = st.form_submit_button("📨 Kirim Tautan Reset Sandi", type="primary", use_container_width=True)

        if submit_reset:
            val_ok, err_msg = validate_email(reset_email)
            if not val_ok:
                st.error(f"❌ {err_msg}")
            else:
                with st.spinner("Mengirimkan instruksi reset kata sandi..."):
                    ok, msg = request_password_reset(reset_email)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ Gagal memproses permintaan: {msg}")

    if st.button("⬅️ Kembali ke Halaman Login", use_container_width=True):
        st.session_state.public_view = "login_user"
        st.rerun()


def render_landing_page():
    """Halaman Beranda / Informasi Publik Platform."""
    render_auth_header()

    st.markdown(
        """
        <div style="text-align:center; padding: 20px 0 10px 0;">
            <div class="auth-brand-badge">IDX Risk Intelligence Platform</div>
            <h1 style="font-size:32px; font-weight:900; letter-spacing:-0.8px; margin-top:12px; margin-bottom:8px; color:#1e293b;">
                Sistem Deteksi Dini Financial Distress Perusahaan BEI
            </h1>
            <p style="font-size:15px; color:#64748b; max-width:680px; margin:0 auto 24px auto; line-height:1.6;">
                Platform komputasi terpadu berbasis tiga metodologi komparatif: <strong>Altman Z''-Score (1995)</strong>, 
                <strong>Model Z''-Score Koefisien Baru (MDA 2024)</strong> hasil kalibrasi 704 observasi emiten Bursa Efek Indonesia, 
                dan <strong>Kecerdasan Buatan XGBoost Classifier</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 📐 Altman Z''-Score")
            st.caption("Model Teoretis Baku (1995)")
            st.markdown(
                "Mengevaluasi 4 rasio likuiditas, solvabilitas, profitabilitas, dan struktur modal "
                "dengan ambang batas Distress (< 1.10) dan Safe (> 2.60)."
            )
    with c2:
        with st.container(border=True):
            st.markdown("### 📊 Koefisien Baru MDA")
            st.caption("Model Empiris Terkalibrasi BEI")
            st.markdown(
                "Model diskriminan linear hasil estimasi data empiris 704 laporan keuangan emiten BEI "
                "dengan ambang batas optimal $Z = 0.3844$."
            )
    with c3:
        with st.container(border=True):
            st.markdown("### 🤖 XGBoost AI Model")
            st.caption("Gradient Boosted Trees Classifier")
            st.markdown(
                "Ensemble machine learning non-linear dengan aktivasi Sigmoid untuk menghitung "
                "probabilitas presisi kebangkrutan korporasi."
            )

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    col_act1, col_act2 = st.columns(2)
    with col_act1:
        if st.button("🚀 Masuk / Buat Akun Pengguna", type="primary", use_container_width=True):
            st.session_state.public_view = "login_user"
            st.rerun()
    with col_act2:
        if st.button("🛡️ Masuk sebagai Administrator", use_container_width=True):
            st.session_state.public_view = "login_admin"
            st.rerun()


def render_auth_portal():
    """Router tampilan autentikasi publik utama."""
    _init_auth_session()
    render_auth_navigation()
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    view = st.session_state.public_view
    if view == "landing":
        render_landing_page()
    elif view == "register_user":
        render_user_registration()
    elif view == "login_admin":
        render_admin_login()
    elif view == "forgot_password":
        render_forgot_password()
    else:
        render_user_login()
