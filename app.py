from __future__ import annotations

import datetime
import html
import io
import json
import math
from pathlib import Path
import re
import sqlite3

import pandas as pd
import streamlit as st

# st.set_page_config HARUS DI BARIS PERTAMA SEBELUM PERINTAH STREAMLIT LAINNYA
st.set_page_config(
    page_title="Prediksi Financial Distress Industri Manufaktur BEI",
    page_icon="📉",
    layout="wide",
)

import time
import streamlit.components.v1 as components
import sys
import importlib

# Matikan penulisan file bytecode cache (.pyc) agar Streamlit selalu membaca file terbaru dari disk
sys.dont_write_bytecode = True

# Hapus dan reload modul src dari memori sys.modules untuk mencegah module caching usang pada server Streamlit yang berjalan
for mod_name in ["src.calculations", "src.io_utils", "src.ui", "src.styles", "src.database", "src.financial_api", "src.supabase_client", "src.auth", "src"]:
    if mod_name in sys.modules:
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception:
            del sys.modules[mod_name]

import src.database
try:
    importlib.reload(src.database)
except Exception:
    pass

import src.financial_api
try:
    importlib.reload(src.financial_api)
except Exception:
    pass

from src.financial_api import (
    FinancialAPIClient,
    TickerNotFoundError,
    FinancialDataUnavailableError,
    AllProvidersExhaustedError,
    MOCK_IDX_DATA,
)

import src.calculations
try:
    importlib.reload(src.calculations)
except Exception:
    pass

import src.io_utils
try:
    importlib.reload(src.io_utils)
except Exception:
    pass

from src.calculations import (
    altman_classification,
    altman_z_score,
    mda_score,
    mda_classification,
    xgboost_predict,
    build_features_from_financials,
    diagnose_distress_drivers,
    calculate_advanced_metrics,
    evaluate_financial_resilience,
    generate_stakeholder_recommendations,
    simulate_what_if,
    calculate_distress_breakeven,
    generate_executive_memo_text,
    analyze_equity_investor,
    analyze_lender_creditor,
    get_split_benchmark_table,
    evaluate_ensemble_weight_portion,
)

# Ambil fungsi-fungsi lanjutan dengan fallback defensif agar aplikasi 100% tahan terhadap anomali import
xgboost_predict_detailed = getattr(src.calculations, "xgboost_predict_detailed", None)
if xgboost_predict_detailed is None:
    def xgboost_predict_detailed(ratios: dict, model_path: str | None, threshold: float = 0.5) -> dict:
        pred, label = xgboost_predict(ratios, model_path, threshold)
        if pred is None:
            return {"available": False}
        prob = float(pred)
        import numpy as _np
        eps = 1e-7
        p_c = _np.clip(prob, eps, 1.0 - eps)
        margin = float(_np.log(p_c / (1.0 - p_c)))
        return {
            "available": True,
            "probability": prob,
            "prob_non_distress": 1.0 - prob,
            "margin": margin,
            "threshold": float(threshold),
            "label": label,
            "status": "DISTRESS" if label == 1 else "NON-DISTRESS",
            "features_used": {k: float(ratios.get(k, 0.0)) for k in ["X1", "X2", "X3", "X4"]},
        }

get_model_metadata = getattr(src.calculations, "get_model_metadata", None)
if get_model_metadata is None:
    def get_model_metadata(model_path: str | None) -> dict:
        if not model_path or not Path(model_path).exists():
            return {"exists": False}
        return {
            "exists": True,
            "path": str(model_path),
            "features": ["X1", "X2", "X3", "X4"],
            "num_features": 4,
            "num_trees": 50,
            "target": "Klasifikasi Biner (1 = Distress, 0 = Non-Distress)",
            "description": "Model XGBoost dengan 4 rasio keuangan (X1 - X4).",
        }

train_xgboost_classifier = getattr(src.calculations, "train_xgboost_classifier", None)
get_xgboost_evaluation_metrics = getattr(src.calculations, "get_xgboost_evaluation_metrics", None)
batch_screen_financials = getattr(src.calculations, "batch_screen_financials", None)
altman_1968_score = getattr(src.calculations, "altman_1968_score", None)
evaluate_warning_factors = getattr(src.calculations, "evaluate_warning_factors", None)
evaluate_model_concordance = getattr(src.calculations, "evaluate_model_concordance", None)
clean_and_cap_ratios = getattr(src.calculations, "clean_and_cap_ratios", None)
validate_financials_and_ratios = getattr(src.calculations, "validate_financials_and_ratios", None)
get_split_benchmark_table = getattr(src.calculations, "get_split_benchmark_table", None)
evaluate_ensemble_weight_portion = getattr(src.calculations, "evaluate_ensemble_weight_portion", None)
HISTORICAL_BENCHMARKS = getattr(src.calculations, "HISTORICAL_BENCHMARKS", {})
calculate_xgb_equivalent_z_score = getattr(src.calculations, "calculate_xgb_equivalent_z_score", None)
if calculate_xgb_equivalent_z_score is None:
    def calculate_xgb_equivalent_z_score(prob: float | None) -> float:
        if prob is None:
            return 0.0
        p = float(prob)
        if p <= 0.35:
            ratio = (0.35 - p) / 0.35
            return round(2.99 + (3.01 * ratio), 2)
        elif p <= 0.65:
            ratio = (0.65 - p) / 0.30
            return round(1.81 + (1.18 * ratio), 2)
        else:
            ratio = max(0.0, (1.0 - p) / 0.35)
            return round(1.81 * ratio, 2)

from src.io_utils import (
    FINANCIAL_FIELDS,
    VARIABLE_SCHEMA,
    complete_financial_values,
    read_csv_file,
    read_excel_file,
    extract_pdf_pages,
    extract_financial_values_from_pages,
    extract_financial_values_from_df,
    extract_financial_values_from_idx_data,
    extract_financial_values_from_excel,
    is_idx_xbrl_data,
    get_idx_document_years,
    parse_financial_number,
    get_pdf_document_years,
    get_sample_template_csv_bytes,
    get_sample_template_excel_bytes,
)


def format_display_value(key: str, val):
    """Memformat nilai variabel untuk tampilan tabel secara jelas: tahun tanpa koma, nilai besar berratusan/ribuan terformat penuh, dan nol eksplisit."""
    if val is None or val == "":
        return "-"
    if key == "report_year":
        try:
            return str(int(float(val)))
        except Exception:
            return str(val)
    if key == "ticker":
        return str(val).upper()

    num = None
    if isinstance(val, (int, float)):
        num = val
    elif isinstance(val, str):
        num = parse_financial_number(val)

    if num is not None:
        if num == 0 or num == 0.0:
            return "0"
        if float(num).is_integer():
            return f"{int(num):,}"
        return f"{num:,.4f}"
    return str(val)


def render_api_error_feedback(error: Exception, ticker: str):
    """Menampilkan pesan error yang ramah, informatif, dan memberikan panduan tindakan alternatif jika seluruh sumber API gagal."""
    t_clean = ticker.strip().upper() if ticker else "EMITEN"
    st.error(f"❌ **Gagal Menarik Laporan Keuangan Otomatis untuk Emiten '{t_clean}'**")
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="font-size:13.5px;color:#fca5a5;font-weight:750;margin-bottom:6px;">
                ⚠️ Ringkasan Kendala Multi-Source API Pipeline:
            </div>
            <div style="font-size:12px;color:#cbd5e1;background:rgba(15,23,42,0.6);padding:8px 12px;border-radius:6px;border-left:3px solid #ef4444;margin-bottom:10px;white-space:pre-wrap;font-family:monospace;">
{html.escape(str(error))}
            </div>
            <div style="font-size:13px;font-weight:750;color:#38bdf8;margin-bottom:6px;">
                💡 Solusi dan Rekomendasi Langkah Alternatif (Fallback):
            </div>
            <ul style="font-size:12px;color:#94a3b8;margin:0 0 8px 0;padding-left:18px;line-height:1.6;">
                <li><b>Upload File Excel Resmi BEI:</b> Unduh file laporan keuangan <code>.xlsx</code> resmi dari situs <a href="https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan" target="_blank" style="color:#38bdf8;text-decoration:underline;">idx.co.id</a>, lalu pilih metode <b>📊 Upload Excel (BEI/IDX)</b>. Format XBRL multi-sheet akan dikenali dan diekstrak secara otomatis.</li>
                <li><b>Upload Dokumen PDF / CSV:</b> Unggah dokumen PDF laporan tahunan resmi atau file CSV pada opsi di atas.</li>
                <li><b>Koreksi Manual:</b> Masukkan langsung angka pos keuangan (Total Aset, Liabilitas, Laba Bersih, dll.) pada form input.</li>
                <li><b>Cek Kode Saham:</b> Pastikan kode ticker tepat 4 huruf kapital (misal: <code>KICI</code>, <code>ICBP</code>, <code>INDF</code>, <code>ASII</code>, <code>UNVR</code>).</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )


from src.styles import inject_css
from src.ui import (
    is_light_theme,
    sidebar_brand,
    metric_card,
    section_title,
    info_table,
    probability_badge,
    conclusion_box,
    render_gauge,
    render_quantum_gauge,
    render_radar_chart,
    render_factor_chart,
    render_feature_importance_chart,
    render_resilience_card,
    render_recommendation_card,
    render_equity_investor_dashboard,
    render_lender_creditor_dashboard,
    render_evaluation_summary_cards,
    render_confusion_matrix_section,
    render_roc_curve_section,
    render_model_evaluation_dashboard,
    render_batch_screening_results,
    render_warning_factors_checklist,
    render_concordance_badge,
    render_multi_model_benchmark_section,
    render_proposal_mockup_dashboard,
    render_score_distribution_chart,
    render_styled_dataframe,
    run_animated_analysis_pipeline,
    run_animated_loading_process,
)


def is_light_theme() -> bool:
    """Helper untuk memeriksa apakah tema antarmuka saat ini adalah Light Mode."""
    return st.session_state.get("theme", "light") == "light"


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
MODEL_PATH = BASE_DIR / "models" / "xgb_model.json"
DB_PATH = BASE_DIR / "financial_distress.db"

# Inisialisasi preferensi tema global (Default: Light Mode)
st.session_state.setdefault("theme", "light")
inject_css(st.session_state.theme)

# ---------- Supabase Client & Autentikasi Cloud (Dual-Mode) ----------
try:
    from src.supabase_client import is_supabase_configured, get_supabase_client
    from src.auth import sign_up_user, sign_out_user
    SUPABASE_AVAILABLE = True
except Exception:
    SUPABASE_AVAILABLE = False
    def is_supabase_configured():
        return False

# ---------- Database Management (Dual-Mode: SQLite Lokal & Cloud PostgreSQL) ----------
from src.database import (
    init_db,
    verify_user,
    verify_user_detailed,
    update_user_status,
    update_user_role,
    get_user_profile,
    update_user_credentials,
    save_prediction_to_db,
    get_all_users,
    add_new_user,
    delete_user_by_username,
    delete_prediction_by_id,
    get_all_predictions,
    clear_all_predictions,
    get_db_info,
    validate_registration_data,
    admin_reset_user_password,
    get_registration_passcode,
    set_registration_passcode,
    is_institutional_email,
    derive_username,
)

# Inisialisasi struktur database saat aplikasi dimulai
init_db()

# ==============================================================================
# Master Data Pintasan Emiten IDX (Dikhususkan untuk Industri Manufaktur)
# Sesuai Kalibrasi Sampel Empiris Model Altman Z''-Score dan XGBoost
# ==============================================================================
MANUFACTURING_GROUPS = {
    "🏭 Manufaktur (Pilihan Utama)": [
        ("ICBP", "Indofood CBP", "Barang Konsumsi / F&B"),
        ("AISA", "FKS Food Sejahtera", "F&B / Eks TPSF (Distress)"),
        ("ANDI", "Andira Agro", "Agro-Manufaktur (Distress)"),
        ("ALTO", "Tri Banyan Tirta", "AMDK / F&B (Distress)"),
        ("ADES", "Akasha Wira", "Barang Konsumsi / Minuman Kemasan"),
        ("AALI", "Astra Agro", "Agro-Manufaktur CPO"),
        ("INDF", "Indofood Sukses", "Barang Konsumsi / F&B"),
        ("UNVR", "Unilever Indonesia", "Consumer Goods / FMCG"),
        ("KLBF", "Kalbe Farma", "Farmasi dan Kesehatan"),
        ("ASII", "Astra International", "Aneka Industri / Otomotif"),
        ("AUTO", "Astra Otoparts", "Komponen Otomotif"),
        ("SMGR", "Semen Indonesia", "Industri Dasar / Semen"),
        ("HMSP", "HM Sampoerna", "Barang Konsumsi / Rokok"),
        ("KICI", "Kedaung Indah Can", "Kemasan dan Enamel (Lapis 3)"),
    ],
    "🚨 Kasus Financial Distress": [
        ("AISA", "FKS Food Sejahtera", "Restrukturisasi dan Defisit Saldo Laba"),
        ("ANDI", "Andira Agro", "Defisit Modal Kerja dan Going Concern"),
        ("ALTO", "Tri Banyan Tirta", "AMDK Utang Tinggi dan Distress"),
        ("KICI", "Kedaung Indah Can", "Kemasan Kaleng (Lapis 3)"),
    ],
    "🍪 Barang Konsumsi": [
        ("ICBP", "Indofood CBP", "Makanan Olahan dan Minuman"),
        ("AISA", "FKS Food Sejahtera", "Bihun dan Snack Taro (F&B)"),
        ("ADES", "Akasha Wira", "Air Mineral dan Kosmetik"),
        ("ALTO", "Tri Banyan Tirta", "Air Minum / Total 8+"),
        ("INDF", "Indofood Sukses", "Agribisnis dan Makanan"),
        ("UNVR", "Unilever Indonesia", "FMCG / Perawatan Tubuh"),
        ("KLBF", "Kalbe Farma", "Farmasi dan Suplemen"),
        ("HMSP", "HM Sampoerna", "Tembakau dan Rokok"),
        ("GGRM", "Gudang Garam", "Tembakau dan Rokok"),
        ("MYOR", "Mayora Indah", "Makanan Ringan dan Biskuit"),
        ("SIDO", "Sido Muncul", "Jamu Herbal dan Suplemen"),
    ],
    "⚙️ Aneka Industri": [
        ("ASII", "Astra International", "Konglomerasi Otomotif"),
        ("AUTO", "Astra Otoparts", "Suku Cadang Otomotif"),
        ("SMSM", "Selamat Sempurna", "Filter dan Radiator"),
        ("GJTL", "Gajah Tunggal", "Ban Kendaraan"),
    ],
    "🧱 Industri Dasar dan Kimia": [
        ("SMGR", "Semen Indonesia (SIG)", "Semen dan Bahan Bangunan"),
        ("INTP", "Indocement Tunggal", "Semen dan Mortar"),
        ("BRPT", "Barito Pacific", "Petrokimia Terintegrasi"),
        ("TPIA", "Chandra Asri", "Petrokimia Hulu"),
        ("AALI", "Astra Agro Lestari", "Agribisnis Pengolahan Sawit"),
        ("ANDI", "Andira Agro", "Agroindustri Sawit (CPO)"),
        ("KICI", "Kedaung Indah Can", "Kemasan Kaleng dan Logam"),
    ],
}

ALL_OTHER_SECTORS = [
    ("TLKM", "Telkom Indonesia", "Telekomunikasi"),
    ("BBCA", "Bank Central Asia", "Perbankan (Non-Manufaktur)*"),
    ("BBRI", "Bank Rakyat Indo", "Perbankan (Non-Manufaktur)*"),
    ("BMRI", "Bank Mandiri", "Perbankan (Non-Manufaktur)*"),
    ("ADRO", "Adaro Energy", "Energi dan Batubara"),
    ("ANTM", "Aneka Tambang", "Pertambangan Mineral"),
    ("GOTO", "GoTo Gojek Tokopedia", "Teknologi Digital"),
    ("ISAT", "Indosat Ooredoo", "Telekomunikasi"),
]


def render_emiten_shortcuts(key_prefix: str) -> str | None:
    """
    Menampilkan antarmuka navigasi pintasan emiten IDX dengan penekanan utama
    pada Industri Manufaktur (sesuai basis empiris 704 data observasi BEI),
    disertai opsi pemilihan semua sektor lainnya (non-manufaktur).
    Mengembalikan simbol ticker yang diklik pengguna, atau None jika tidak ada.
    """
    st.markdown(
        """
        <div style="margin: 12px 0 8px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 11.5px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.6px; background: rgba(56, 189, 248, 0.12); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(56, 189, 248, 0.28);">
                    🏭 KHUSUS INDUSTRI MANUFAKTUR
                </span>
                <span style="font-size: 12.5px; font-weight: 700; color: #f1f5f9;">
                    Pintasan Cepat Emiten Bursa Efek Indonesia (IDX)
                </span>
            </div>
            <span style="font-size: 11px; color: #94a3b8; font-style: italic;">
                *Model Altman Z''-Score dan XGBoost dikalibrasi primer pada manufaktur
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "🏭 Manufaktur (Pilihan Utama)",
        "🚨 Kasus Financial Distress",
        "🍪 Barang Konsumsi",
        "⚙️ Aneka Industri",
        "🧱 Industri Dasar dan Kimia",
        "🌐 Semua Sektor (Termasuk Non-Manufaktur)",
    ])

    clicked_symbol: str | None = None

    # Tab 1: Manufaktur Unggulan
    with tabs[0]:
        st.caption("⚡ Koleksi emiten manufaktur terpopuler lintas subsektor (Barang Konsumsi, Otomotif, Semen):")
        cols = st.columns(4)
        for i, (sym, name, sub) in enumerate(MANUFACTURING_GROUPS["🏭 Manufaktur (Pilihan Utama)"]):
            with cols[i % 4]:
                if st.button(
                    f"🏭 {sym} — {name[:14]}",
                    key=f"{key_prefix}_mfg_main_{sym}",
                    help=f"{sym}: {name} ({sub}). Klik untuk menarik data otomatis.",
                    use_container_width=True,
                ):
                    clicked_symbol = sym

    # Tab 2: Kasus Financial Distress
    with tabs[1]:
        st.caption("🚨 Emiten manufaktur BEI dengan catatan Going Concern, defisit modal kerja, dan akumulasi rugi:")
        cols = st.columns(4)
        for i, (sym, name, sub) in enumerate(MANUFACTURING_GROUPS["🚨 Kasus Financial Distress"]):
            with cols[i % 4]:
                if st.button(
                    f"🚨 {sym} — {name[:14]}",
                    key=f"{key_prefix}_mfg_distress_{sym}",
                    help=f"{sym}: {name} ({sub}). Klik untuk menarik data otomatis.",
                    use_container_width=True,
                ):
                    clicked_symbol = sym

    # Tab 3: Barang Konsumsi
    with tabs[2]:
        st.caption("🍪 Subsektor Consumer Goods (Makanan dan Minuman, Farmasi, Kosmetik, Tembakau):")
        cols = st.columns(4)
        for i, (sym, name, sub) in enumerate(MANUFACTURING_GROUPS["🍪 Barang Konsumsi"]):
            with cols[i % 4]:
                if st.button(
                    f"🍪 {sym} — {name[:14]}",
                    key=f"{key_prefix}_mfg_cns_{sym}",
                    help=f"{sym}: {name} ({sub}). Klik untuk menarik data otomatis.",
                    use_container_width=True,
                ):
                    clicked_symbol = sym

    # Tab 4: Aneka Industri dan Otomotif
    with tabs[3]:
        st.caption("⚙️ Subsektor Aneka Industri, Perakitan Otomotif, Suku Cadang dan Mesin:")
        cols = st.columns(4)
        for i, (sym, name, sub) in enumerate(MANUFACTURING_GROUPS["⚙️ Aneka Industri"]):
            with cols[i % 4]:
                if st.button(
                    f"⚙️ {sym} — {name[:14]}",
                    key=f"{key_prefix}_mfg_ind_{sym}",
                    help=f"{sym}: {name} ({sub}). Klik untuk menarik data otomatis.",
                    use_container_width=True,
                ):
                    clicked_symbol = sym

    # Tab 5: Industri Dasar dan Kimia
    with tabs[4]:
        st.caption("🧱 Subsektor Bahan Bangunan, Semen, Logam, Kimia Industri dan Petrokimia:")
        cols = st.columns(4)
        for i, (sym, name, sub) in enumerate(MANUFACTURING_GROUPS["🧱 Industri Dasar dan Kimia"]):
            with cols[i % 4]:
                if st.button(
                    f"🧱 {sym} — {name[:14]}",
                    key=f"{key_prefix}_mfg_mat_{sym}",
                    help=f"{sym}: {name} ({sub}). Klik untuk menarik data otomatis.",
                    use_container_width=True,
                ):
                    clicked_symbol = sym

    # Tab 6: Semua Sektor / Non-Manufaktur
    with tabs[5]:
        st.caption("🌐 Emiten sektor lainnya di luar manufaktur (Perbankan, Telekomunikasi, Energi, Tambang, Teknologi):")
        st.info(
            "💡 **Catatan Metodologi:** Model Altman Z''-Score Emerging Market didesain khusus untuk perusahaan non-keuangan/manufaktur. "
            "Sektor perbankan memiliki format neraca tersendiri tanpa pos modal kerja konvensional.",
            icon="ℹ️",
        )
        cols = st.columns(4)
        for i, (sym, name, sub) in enumerate(ALL_OTHER_SECTORS):
            with cols[i % 4]:
                if st.button(
                    f"🌐 {sym} — {name[:14]}",
                    key=f"{key_prefix}_all_{sym}",
                    help=f"{sym}: {name} ({sub}). Klik untuk menarik data otomatis.",
                    use_container_width=True,
                ):
                    clicked_symbol = sym

    return clicked_symbol


# ---------- Session State Defaults ----------
defaults = {
    "theme": "light",
    "logged_in": False,
    "user_id": "",
    "username": "",
    "role": "user",
    "user_fullname": "",
    "user_email": "",
    "user_phone": "",
    "user_institution": "",
    "user_type": "Pekerja / Profesional",
    "user_position": "",
    "user_city": "",
    "user_bio": "",
    "user_avatar": "",
    "user_division": "",
    "page": "Dashboard",
    "custom_page_menu": "Dashboard",
    "_last_nav_page": "Dashboard",
    "company": "",
    "ticker": "",
    "sector": "",
    "year": 2024,
    "analysis_date": "2026-06-06",
    "source_mode": "Input Manual",
    "financials": {},
    "ratios": {"X1": 0.0, "X2": 0.0, "X3": 0.0, "X4": 0.0, "X5": 0.0},
    "sidebar_visible": True,
    "sidebar_collapsed": False,
    "xgb_probability": None,
    "has_analyzed": False,
    "api_emiten_data": None,
    "api_selected_ticker": "",
    "menu_scroll_top": True,
    "_prev_page_seen": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def determine_3category_status(z, z_cls, mda, mda_cls, xgb_prob, xgb_thresh=0.5, altman_thresh=None):
    """
    Menghitung konsensus status 3 Kategori Operasional:
    1. 🔴 Safe Zone (Zona Aman) - Hijau (#10b981)
    2. 🟡 Grey Area (Zona Abu-Abu / Waspada) - Kuning / Amber (#f59e0b)
    3. 🟢 Distress Zone (Zona Bahaya / Distress) - Merah (#f43f5e)
    """
    # 1. Pemetaan Zona Altman Z''-Score
    z_cls_str = str(z_cls).lower()
    if z_cls_str == "distress":
        altman_zone = "DISTRESS ZONE"
    elif z_cls_str in ("grey", "grey area", "waspada"):
        altman_zone = "GREY AREA"
    else:
        altman_zone = "SAFE ZONE"

    # 2. Pemetaan Zona MDA Koefisien Baru
    mda_cls_str = str(mda_cls).lower()
    if mda_cls_str == "distress":
        mda_zone = "DISTRESS ZONE"
    elif mda_cls_str in ("grey", "grey area", "waspada"):
        mda_zone = "GREY AREA"
    else:
        mda_zone = "SAFE ZONE"

    # 3. Pemetaan Zona XGBoost Classifier
    if xgb_prob is not None:
        if isinstance(xgb_thresh, dict):
            safe_p = float(xgb_thresh.get("safe", 0.35))
            dist_p = float(xgb_thresh.get("distress", 0.65))
        else:
            mid_p = float(xgb_thresh or 0.50)
            safe_p = max(0.05, mid_p - 0.15)
            dist_p = min(0.95, mid_p + 0.15)

        if xgb_prob > dist_p:
            xgb_zone = "DISTRESS ZONE"
        elif xgb_prob >= safe_p:
            xgb_zone = "GREY AREA"
        else:
            xgb_zone = "SAFE ZONE"
    else:
        xgb_zone = None

    # Hitung pemungutan suara konsensus
    active_zones = [altman_zone, mda_zone]
    if xgb_zone is not None:
        active_zones.append(xgb_zone)

    distress_votes = sum(1 for v in active_zones if v == "DISTRESS ZONE")
    grey_votes = sum(1 for v in active_zones if v == "GREY AREA")
    safe_votes = sum(1 for v in active_zones if v == "SAFE ZONE")
    total_models = len(active_zones)

    if distress_votes >= 2 or (distress_votes == 1 and grey_votes >= 1 and (xgb_prob is not None and xgb_prob >= 0.55)):
        status = "DISTRESS ZONE"
        tone = "red"
        color = "#f43f5e"
        badge_icon = "🔴"
        desc = "Zona Bahaya (Distress Zone) — Terindikasi risiko kepailitan akut dan tekanan solvabilitas berat."
        summary_note = f"Mayoritas ({distress_votes}/{total_models} Model Menyatakan Distress Zone)"
    elif safe_votes >= 2 and distress_votes == 0:
        status = "SAFE ZONE"
        tone = "emerald"
        color = "#10b981"
        badge_icon = "🟢"
        desc = "Zona Aman (Safe Zone) — Struktur permodalan sehat, kinerja profitabilitas solid, dan likuiditas lancar."
        summary_note = f"Mayoritas ({safe_votes}/{total_models} Model di Zona Aman)"
    else:
        status = "GREY AREA"
        tone = "amber"
        color = "#f59e0b"
        badge_icon = "🟡"
        desc = "Zona Abu-Abu / Waspada (Grey Area) — Kerentanan finansial perbatasan terdeteksi, diperlukan pemantauan ketat."
        summary_note = f"Zona Waspada (Altman: {altman_zone}, MDA: {mda_zone}, XGB: {xgb_zone or 'N/A'})"

    return {
        "status": status,
        "tone": tone,
        "color": color,
        "badge_icon": badge_icon,
        "desc": desc,
        "summary_note": summary_note,
        "distress_votes": distress_votes,
        "grey_votes": grey_votes,
        "safe_votes": safe_votes,
        "altman_zone": altman_zone,
        "mda_zone": mda_zone,
        "xgb_zone": xgb_zone or "STANDBY",
    }


PAGE_ALIASES_ADMIN = {
    "Dashboard Sistem": "Dashboard",
    "Dashboard Prediksi": "Dashboard",
    "Data Perusahaan": "Data dan Laporan Keuangan",
    "Laporan Keuangan": "Data dan Laporan Keuangan",
    "Input Data": "Data dan Laporan Keuangan",
    "Input Data Keuangan": "Data dan Laporan Keuangan",
    "Data & Laporan Keuangan": "Data dan Laporan Keuangan",
    "Data dan Laporan Keuangan": "Data dan Laporan Keuangan",
    "Rasio Keuangan": "Rasio dan Hasil Prediksi",
    "Hasil Prediksi": "Rasio dan Hasil Prediksi",
    "Rasio & Hasil Prediksi": "Rasio dan Hasil Prediksi",
    "Rasio dan Hasil Prediksi": "Rasio dan Hasil Prediksi",
    "Perbandingan Hasil": "Perbandingan dan Evaluasi Model",
    "Evaluasi Model": "Perbandingan dan Evaluasi Model",
    "Perbandingan & Evaluasi Model": "Perbandingan dan Evaluasi Model",
    "Perbandingan dan Evaluasi Model": "Perbandingan dan Evaluasi Model",
    "Histori Prediksi": "Histori Prediksi",
    "Manajemen Pengguna": "Pengaturan Model",
    "Data Pengguna": "Pengaturan Model",
    "Data Pengguna Terdaftar": "Pengaturan Model",
    "Integrasi API Pasar": "Integrasi API (Tahun)",
    "Integrasi API Tahun": "Integrasi API (Tahun)",
    "Pengaturan Profil": "Pengaturan Profil",
    "Pengaturan Akun": "Pengaturan Profil",
    "Profil": "Pengaturan Profil",
    "Profile": "Pengaturan Profil",
}

PAGE_ALIASES_USER = {
    "Dashboard": "Dashboard",
    "Dashboard Sistem": "Dashboard",
    "Dashboard & Analisis": "Dashboard",
    "Dashboard dan Analisis": "Dashboard",
    "Dashboard Prediksi": "Hasil Prediksi",
    "Data & Laporan Keuangan": "Data dan Laporan Keuangan",
    "Data dan Laporan Keuangan": "Data dan Laporan Keuangan",
    "Data Perusahaan": "Data dan Laporan Keuangan",
    "Laporan Keuangan": "Data dan Laporan Keuangan",
    "Input Data": "Data dan Laporan Keuangan",
    "Input Data Keuangan": "Data dan Laporan Keuangan",
    "Rasio Keuangan": "Hasil Prediksi",
    "Rasio & Hasil Prediksi": "Hasil Prediksi",
    "Rasio dan Hasil Prediksi": "Hasil Prediksi",
    "Perbandingan & Evaluasi Model": "Perbandingan dan Evaluasi Model",
    "Perbandingan dan Evaluasi Model": "Perbandingan dan Evaluasi Model",
    "Perbandingan Hasil": "Perbandingan dan Evaluasi Model",
    "Evaluasi Model": "Perbandingan dan Evaluasi Model",
    "Integrasi API Pasar": "Integrasi API (Tahun)",
    "Integrasi API Tahun": "Integrasi API (Tahun)",
    "Pengaturan Profil": "Pengaturan Profil",
    "Pengaturan Akun": "Pengaturan Profil",
    "Profil": "Pengaturan Profil",
    "Profile": "Pengaturan Profil",
}

def set_page(page_name):
    role = st.session_state.get("role", "admin")
    if role == "admin":
        target = PAGE_ALIASES_ADMIN.get(page_name, page_name)
    else:
        target = PAGE_ALIASES_USER.get(page_name, page_name)
    st.session_state.page = target
    st.session_state.menu_scroll_top = True
    try:
        if target in ("Pengaturan Profil", "Pengaturan Akun", "Profil", "Profile"):
            st.session_state.custom_page_menu = None
            st.session_state._last_nav_page = target
        else:
            st.session_state.custom_page_menu = target
            st.session_state._last_nav_page = target
    except Exception:
        pass


def logout_user():
    """Melakukan logout pengguna dan mereset sesi autentikasi dengan aman tanpa memicu StreamlitWidgetAlreadyInstantiatedError."""
    if SUPABASE_AVAILABLE:
        try:
            sign_out_user()
        except Exception:
            pass
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.username = ""
    st.session_state.role = "user"
    st.session_state.user_fullname = ""
    st.session_state.user_email = ""
    st.session_state.user_phone = ""
    st.session_state.user_institution = ""
    st.session_state.user_type = "Pekerja / Profesional"
    st.session_state.user_position = ""
    st.session_state.user_city = ""
    st.session_state.user_bio = ""
    st.session_state.user_avatar = ""
    st.session_state.page = "Dashboard"
    # CATATAN KRUSIAL: JANGAN memodifikasi st.session_state.custom_page_menu di sini!
    # custom_page_menu sudah diinstansiasi oleh st.radio pada run saat ini.
    # Mengubahnya akan menyebabkan StreamlitWidgetAlreadyInstantiatedError.
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        else:
            st.experimental_set_query_params()
    except Exception:
        pass
    st.rerun()


def render_clean_html(html_str: str):
    """
    Render HTML di Streamlit dengan menjamin tidak ada leading whitespace (indentasi >= 4 spasi)
    pada tiap baris agar tidak diinterpretasikan oleh parser Markdown CommonMark sebagai blok kode (<pre><code>).
    """
    cleaned = "\n".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


# ---------- Halaman Login & Registrasi (Spacer Sliding Theme) ----------
if not st.session_state.logged_in:
    # Helper untuk membaca dan membersihkan parameter query URL
    def _get_auth_param(key: str, default: str = "") -> str:
        try:
            if hasattr(st, "query_params"):
                val = st.query_params.get(key, default)
            else:
                qp = st.experimental_get_query_params()
                val = qp.get(key, [default])
                if isinstance(val, list):
                    val = val[0] if val else default
            if isinstance(val, list):
                val = val[0] if val else default
            return str(val) if val is not None else default
        except Exception:
            return default

    def _clear_auth_params():
        try:
            if hasattr(st, "query_params"):
                st.query_params.clear()
            else:
                st.experimental_set_query_params()
        except Exception:
            pass

    # Ambil pesan flash dari sesi sebelumnya jika ada
    auth_error_msg = st.session_state.pop("auth_flash_error", "")
    auth_success_msg = st.session_state.pop("auth_flash_success", "")

    # Proses aksi autentikasi dari form / pintasan URL
    auth_action = _get_auth_param("auth_action")

    if auth_action in ("demo_admin", "demo_user"):
        st.session_state.auth_flash_error = "Akses instan tanpa sandi dinonaktifkan demi keamanan. Harap masuk menggunakan kredensial akun terdaftar."
        st.session_state.auth_mode = "signin"
        _clear_auth_params()
        st.rerun()

    elif auth_action == "signin":
        in_user = _get_auth_param("in_user").strip()
        in_pass = _get_auth_param("in_pass").strip()
        if not in_user or not in_pass:
            st.session_state.auth_flash_error = "Mohon isi username/email dan password."
            st.session_state.auth_mode = "signin"
        else:
            authenticated = False
            user_role = None
            user_prof = {}
            user_uuid = ""

            # 1. Cek autentikasi Supabase jika aktif
            if SUPABASE_AVAILABLE and is_supabase_configured():
                try:
                    sb_client = get_supabase_client()
                    if sb_client:
                        login_email = in_user.lower()
                        # Jika user memasukkan username tanpa @, cari email padanannya di tabel profiles
                        if "@" not in login_email:
                            u_query = sb_client.table("profiles").select("email").eq("username", login_email).execute()
                            if u_query.data:
                                login_email = u_query.data[0]["email"]

                        auth_res = sb_client.auth.sign_in_with_password({
                            "email": login_email,
                            "password": in_pass
                        })
                        if auth_res.user:
                            user_uuid = auth_res.user.id
                            p_query = sb_client.table("profiles").select("*").eq("id", user_uuid).execute()
                            user_prof = p_query.data[0] if p_query.data else {}
                            if user_prof.get("status") == "disabled":
                                try:
                                    sb_client.auth.sign_out()
                                except Exception:
                                    pass
                                st.session_state.auth_flash_error = "Akun Anda berstatus nonaktif. Silakan hubungi Administrator."
                                st.session_state.auth_mode = "signin"
                                _clear_auth_params()
                                st.rerun()

                            user_role = user_prof.get("role", "user")
                            user_prof["email"] = auth_res.user.email
                            authenticated = True
                except Exception as exc:
                    err_text = str(exc)
                    if "Email not confirmed" in err_text:
                        st.session_state.auth_flash_error = "Alamat email Anda belum diverifikasi. Harap periksa email Anda."
                        st.session_state.auth_mode = "signin"
                        _clear_auth_params()
                        st.rerun()

            # 2. Fallback autentikasi lokal (SQLite / Database Internal) jika Supabase belum aktif atau akun lokal
            if not authenticated:
                ok_local, local_role, local_err_msg, u_prof = verify_user_detailed(in_user, in_pass)
                if ok_local:
                    user_role = local_role
                    user_prof = u_prof or get_user_profile(in_user) or {}
                    authenticated = True
                else:
                    st.session_state.auth_flash_error = local_err_msg
                    st.session_state.auth_mode = "signin"
                    _clear_auth_params()
                    st.rerun()

            if authenticated and user_role:
                canon_u = user_prof.get("username", in_user)
                st.session_state.logged_in = True
                st.session_state.user_id = user_uuid or str(user_prof.get("id", ""))
                st.session_state.username = canon_u
                st.session_state.role = user_role
                st.session_state.user_fullname = user_prof.get("full_name") or ("System Administrator" if user_role == "admin" else canon_u)
                st.session_state.user_email = user_prof.get("email") or (f"{canon_u.lower()}@distress.ai" if "@" not in canon_u else canon_u)
                st.session_state.user_phone = user_prof.get("phone_number", "")
                st.session_state.user_institution = user_prof.get("institution", "")
                st.session_state.user_type = user_prof.get("user_type", "Pekerja / Profesional")
                st.session_state.user_position = user_prof.get("position", "")
                st.session_state.user_city = user_prof.get("city", "")
                st.session_state.user_bio = user_prof.get("bio", "")
                st.session_state.user_avatar = user_prof.get("avatar_data", "")
                set_page("Dashboard")
                _clear_auth_params()
                st.rerun()
            else:
                st.session_state.auth_flash_error = "Username/Email atau password salah!"
                st.session_state.auth_mode = "signin"
        _clear_auth_params()
        st.rerun()

    elif auth_action == "signup":
        up_user = _get_auth_param("up_user").strip()  # Email Address
        up_pass = _get_auth_param("up_pass").strip()  # Password
        up_name = _get_auth_param("up_name").strip()  # Full Name

        # 1. Validasi Input Ketat via validate_registration_data
        is_val, err_msg, detected_inst = validate_registration_data(up_name, up_user, up_pass)
        if not is_val:
            st.session_state.auth_flash_error = f"❌ {err_msg}"
            st.session_state.auth_mode = "signup"
        else:
            # 2. Derive unique clean username langsung dari Nama Lengkap (Full Name) tanpa tambahan underline atau email
            clean_u = derive_username(up_name, up_user)
            
            # 3. Sinkronkan ke Supabase Auth jika aktif
            if SUPABASE_AVAILABLE and is_supabase_configured():
                try:
                    ok_sb, user_sb, msg_sb, is_req = sign_up_user(
                        email=up_user,
                        password=up_pass,
                        confirm_password=up_pass,
                        full_name=up_name,
                        username=clean_u,
                        agreed_terms=True
                    )
                    if not ok_sb and "already registered" not in msg_sb.lower():
                        st.session_state.auth_flash_error = f"❌ {msg_sb}"
                        st.session_state.auth_mode = "signup"
                        _clear_auth_params()
                        st.rerun()
                except Exception:
                    pass

            # 4. Simpan ke database lokal dengan aturan deteksi otomatis email valid (Langsung Aktif Otomatis)
            res = add_new_user(
                username=clean_u,
                password=up_pass,
                role="user",
                email=up_user,
                full_name=up_name,
                institution=detected_inst,
                status=None,  # Menggunakan aturan auto-approval deteksi cerdas email
            )
            if res.success:
                st.session_state.auth_flash_success = res.message
                st.session_state.auth_mode = "signin"
                st.session_state.prefill_user = up_user
            else:
                st.session_state.auth_flash_error = f"❌ {res.message}"
                st.session_state.auth_mode = "signup"
                st.session_state.prefill_user = up_user
        _clear_auth_params()
        st.rerun()

    # Sinkronisasi parameter query umum jika ada
    param_auth = _get_auth_param("auth")
    if param_auth in ["signin", "signup"]:
        st.session_state.auth_mode = param_auth

    st.session_state.setdefault("auth_mode", "signin")
    checked_signup = "checked" if st.session_state.auth_mode == "signup" else ""
    checked_signin = "checked" if st.session_state.auth_mode == "signin" else ""
    card_mode_class = "is-signin-mode" if st.session_state.auth_mode == "signin" else "is-signup-mode"
    prefill_val = html.escape(st.session_state.pop("prefill_user", ""))
    val_attr = f'defaultValue="{prefill_val}"' if prefill_val else ""

    # Latar belakang bersih Halaman Login (Clean Modern FinTech Gradient)
    # Default gradien halus agar tampilan selalu profesional dan tidak tertimpa screenshot/grafik lokal
    bg_image_css = """
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #f1f5f9 !important;
        background-image: radial-gradient(circle at 50% 30%, #ffffff 0%, #f1f5f9 60%, #e2e8f0 100%) !important;
    }
    """
    # Hanya gunakan file gambar jika secara spesifik bernama login_bg atau login_wallpaper
    candidate_bg_names = ["login_bg.jpg", "login_bg.png", "login_wallpaper.jpg"]
    found_bg_path = None
    for bname in candidate_bg_names:
        cand = BASE_DIR / bname
        if cand.exists() and cand.is_file():
            found_bg_path = cand
            break

    if found_bg_path:
        import base64
        try:
            with open(found_bg_path, "rb") as _bf:
                _b64 = base64.b64encode(_bf.read()).decode("utf-8")
            mime_type = "image/png" if found_bg_path.suffix.lower() == ".png" else "image/jpeg"
            bg_image_css = f"""
            .stApp, [data-testid="stAppViewContainer"] {{
                background-image: url("data:{mime_type};base64,{_b64}") !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
                background-attachment: fixed !important;
            }}
            """
        except Exception:
            pass

    # Format pesan alert jika ada
    floating_toast_html = ""
    alert_html_signin = ""
    alert_html_signup = ""
    if auth_error_msg:
        if st.session_state.auth_mode == "signup":
            alert_html_signup = f'<div class="auth-alert alert-error"><span class="alert-icon">⚠️</span><span>{auth_error_msg}</span></div>'
        else:
            alert_html_signin = f'<div class="auth-alert alert-error"><span class="alert-icon">⚠️</span><span>{auth_error_msg}</span></div>'
    elif auth_success_msg:
        # Notifikasi sukses registrasi mengambang (Floating Toast Notification)
        clean_msg = auth_success_msg.replace("🎉", "").strip()
        floating_toast_html = f"""
        <div class="floating-toast" id="floatingToast">
            <div class="toast-icon-pulse">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <div class="toast-content">
                <div class="toast-title">Pendaftaran Akun Berhasil</div>
                <div class="toast-msg">{clean_msg}</div>
            </div>
            <button type="button" class="toast-close-btn" title="Tutup Notifikasi" onclick="var t=document.getElementById('floatingToast'); if(t) t.style.display='none';">&times;</button>
        </div>
        """
        try:
            st.toast(clean_msg, icon="🎉")
        except Exception:
            pass

    # Render CSS Lengkap (Dipisahkan agar tidak ada konflik parser Markdown)
    css_rules = f"""
    html, body {{
        margin: 0 !important;
        padding: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
        overflow-x: hidden !important;
        overflow-y: hidden !important;
    }}

    ::-webkit-scrollbar {{
        display: none !important;
        width: 0px !important;
        height: 0px !important;
    }}
    * {{
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
        box-sizing: border-box;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    header[data-testid="stHeader"], footer, #MainMenu, .stDeployButton, div[data-testid="stDecoration"],
    [data-testid="stHeaderActionElements"], div[data-testid="stHeadingWithActionElements"] > div,
    a.anchorjs-link, .anchorjs-link, h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }}

    .stApp, 
    .stAppViewContainer, 
    [data-testid="stAppViewContainer"], 
    section.stMain,
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer {{
        background: transparent !important;
        background-color: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100vw !important;
        max-width: 100vw !important;
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
        overflow-x: hidden !important;
        overflow-y: hidden !important;
    }}

    {bg_image_css}

    .auth-viewport-wrapper {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 20px;
        box-sizing: border-box;
        overflow: hidden;
        z-index: 100;
    }}

    .ambient-orb {{
        position: absolute;
        border-radius: 50%;
        filter: blur(85px);
        pointer-events: none;
        z-index: 1;
        opacity: 0.55;
    }}
    .orb-1 {{
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(37, 99, 235, 0.38) 0%, rgba(37, 99, 235, 0) 70%);
        top: calc(50% - 270px);
        left: calc(50% - 430px);
        animation: orbFloat1 9s ease-in-out infinite alternate;
    }}
    .orb-2 {{
        width: 360px;
        height: 360px;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.32) 0%, rgba(14, 165, 233, 0) 70%);
        bottom: calc(50% - 250px);
        right: calc(50% - 400px);
        animation: orbFloat2 8s ease-in-out infinite alternate;
    }}
    @keyframes orbFloat1 {{
        0% {{ transform: translate(0, 0) scale(1); }}
        100% {{ transform: translate(35px, 25px) scale(1.08); }}
    }}
    @keyframes orbFloat2 {{
        0% {{ transform: translate(0, 0) scale(1); }}
        100% {{ transform: translate(-30px, -20px) scale(1.06); }}
    }}

    .slider-card {{
        position: relative;
        width: 860px;
        max-width: calc(100vw - 36px);
        height: 520px;
        max-height: calc(100vh - 40px);
        background: #ffffff;
        border-radius: 28px;
        box-shadow: 0 25px 60px -15px rgba(15, 60, 201, 0.25), 0 12px 30px -10px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(226, 232, 240, 0.85);
        overflow: hidden;
        z-index: 10;
    }}

    .auth-radio-toggle {{
        position: fixed !important;
        opacity: 0 !important;
        top: -9999px !important;
        left: -9999px !important;
        pointer-events: none !important;
        width: 1px !important;
        height: 1px !important;
        margin: 0 !important;
    }}

    .form-panel {{
        position: absolute;
        top: 0;
        height: 100%;
        width: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 24px 38px;
        box-sizing: border-box;
        transition: all 0.65s cubic-bezier(0.65, 0, 0.35, 1);
        z-index: 10;
        background: #ffffff;
    }}

    /* Keadaan Dasar Default: Sign In (Aktif & Interaktif) */
    .sign-in-panel {{
        left: 0;
        opacity: 1;
        transform: translateX(0);
        pointer-events: auto !important;
        z-index: 20;
    }}

    .sign-up-panel {{
        right: 0;
        opacity: 0;
        transform: translateX(35px);
        pointer-events: none !important;
        z-index: 5;
    }}

    .brand-overlay {{
        position: absolute;
        top: 0;
        left: 0;
        width: 50%;
        height: 100%;
        background: linear-gradient(135deg, #1056e8 0%, #1a58eb 50%, #0d42bf 100%);
        color: #ffffff;
        z-index: 30;
        transform: translateX(100%);
        transition: transform 0.65s cubic-bezier(0.65, 0, 0.35, 1);
        overflow: visible;
    }}

    .overlay-card {{
        position: absolute;
        inset: 26px 28px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        text-align: center;
        transition: all 0.5s ease-in-out;
        box-sizing: border-box;
    }}

    .card-for-signup {{
        opacity: 0;
        transform: translateX(-35px);
        pointer-events: none !important;
    }}

    .card-for-signin {{
        opacity: 1;
        transform: translateX(0);
        pointer-events: auto !important;
    }}

    .cloud-divider-right {{
        position: absolute;
        right: -1px;
        top: 0;
        bottom: 0;
        width: 44px;
        height: 100%;
        z-index: 35;
        pointer-events: none;
        transition: opacity 0.35s ease;
        opacity: 0;
    }}
    .cloud-divider-left {{
        position: absolute;
        left: -1px;
        top: 0;
        bottom: 0;
        width: 44px;
        height: 100%;
        z-index: 35;
        pointer-events: none;
        transform: scaleX(-1);
        transition: opacity 0.35s ease;
        opacity: 1;
    }}

    /* ================= 1. ATURAN AKTIF: SIGN IN (SLIDING KE KANAN) ================= */
    #tab-signin:checked ~ .brand-overlay,
    #tab-signin:checked ~ .slider-card .brand-overlay,
    .slider-card.is-signin-mode .brand-overlay {{
        transform: translateX(100%) !important;
    }}
    #tab-signin:checked ~ .sign-in-panel,
    #tab-signin:checked ~ .slider-card .sign-in-panel,
    .slider-card.is-signin-mode .sign-in-panel {{
        opacity: 1 !important;
        transform: translateX(0) !important;
        pointer-events: auto !important;
        z-index: 25 !important;
    }}
    #tab-signin:checked ~ .sign-up-panel,
    #tab-signin:checked ~ .slider-card .sign-up-panel,
    .slider-card.is-signin-mode .sign-up-panel {{
        opacity: 0 !important;
        transform: translateX(35px) !important;
        pointer-events: none !important;
        z-index: 5 !important;
    }}
    #tab-signin:checked ~ .brand-overlay .card-for-signup,
    #tab-signin:checked ~ .slider-card .card-for-signup,
    .slider-card.is-signin-mode .card-for-signup {{
        opacity: 0 !important;
        transform: translateX(-35px) !important;
        pointer-events: none !important;
    }}
    #tab-signin:checked ~ .brand-overlay .card-for-signin,
    #tab-signin:checked ~ .slider-card .card-for-signin,
    .slider-card.is-signin-mode .card-for-signin {{
        opacity: 1 !important;
        transform: translateX(0) !important;
        pointer-events: auto !important;
    }}
    #tab-signin:checked ~ .brand-overlay .cloud-divider-right,
    #tab-signin:checked ~ .slider-card .cloud-divider-right,
    .slider-card.is-signin-mode .cloud-divider-right {{
        opacity: 0 !important;
    }}
    #tab-signin:checked ~ .brand-overlay .cloud-divider-left,
    #tab-signin:checked ~ .slider-card .cloud-divider-left,
    .slider-card.is-signin-mode .cloud-divider-left {{
        opacity: 1 !important;
    }}

    /* ================= 2. ATURAN AKTIF: SIGN UP (SLIDING KE KIRI) ================= */
    #tab-signup:checked ~ .brand-overlay,
    #tab-signup:checked ~ .slider-card .brand-overlay,
    .slider-card.is-signup-mode .brand-overlay {{
        transform: translateX(0) !important;
    }}
    #tab-signup:checked ~ .sign-in-panel,
    #tab-signup:checked ~ .slider-card .sign-in-panel,
    .slider-card.is-signup-mode .sign-in-panel {{
        opacity: 0 !important;
        transform: translateX(-35px) !important;
        pointer-events: none !important;
        z-index: 5 !important;
    }}
    #tab-signup:checked ~ .sign-up-panel,
    #tab-signup:checked ~ .slider-card .sign-up-panel,
    .slider-card.is-signup-mode .sign-up-panel {{
        opacity: 1 !important;
        transform: translateX(0) !important;
        pointer-events: auto !important;
        z-index: 25 !important;
    }}
    #tab-signup:checked ~ .brand-overlay .card-for-signup,
    #tab-signup:checked ~ .slider-card .card-for-signup,
    .slider-card.is-signup-mode .card-for-signup {{
        opacity: 1 !important;
        transform: translateX(0) !important;
        pointer-events: auto !important;
    }}
    #tab-signup:checked ~ .brand-overlay .card-for-signin,
    #tab-signup:checked ~ .slider-card .card-for-signin,
    .slider-card.is-signup-mode .card-for-signin {{
        opacity: 0 !important;
        transform: translateX(35px) !important;
        pointer-events: none !important;
    }}
    #tab-signup:checked ~ .brand-overlay .cloud-divider-right,
    #tab-signup:checked ~ .slider-card .cloud-divider-right,
    .slider-card.is-signup-mode .cloud-divider-right {{
        opacity: 1 !important;
    }}
    #tab-signup:checked ~ .brand-overlay .cloud-divider-left,
    #tab-signup:checked ~ .slider-card .cloud-divider-left,
    .slider-card.is-signup-mode .cloud-divider-left {{
        opacity: 0 !important;
    }}

    .form-header {{
        text-align: center;
        margin-bottom: 12px;
        width: 100%;
        background: transparent !important;
        background-color: transparent !important;
    }}
    .form-title {{
        font-size: 22px;
        font-weight: 850;
        color: #0f172a;
        letter-spacing: -0.5px;
        margin: 0 auto 3px auto;
        text-align: center;
        width: 100%;
        display: block;
        background: transparent !important;
        background-color: transparent !important;
        user-select: none !important;
        -webkit-user-select: none !important;
    }}
    .form-subtitle {{
        font-size: 11.5px;
        color: #64748b;
        margin: 0;
        background: transparent !important;
        background-color: transparent !important;
        user-select: none !important;
        -webkit-user-select: none !important;
    }}

    .form-panel form {{
        width: 100%;
        background: transparent !important;
        background-color: transparent !important;
        pointer-events: auto !important;
    }}

    .input-group {{
        margin-bottom: 9px;
        text-align: left;
        width: 100%;
        background: transparent !important;
        background-color: transparent !important;
        pointer-events: auto !important;
    }}
    .input-label-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        background: transparent !important;
        background-color: transparent !important;
        pointer-events: auto !important;
    }}
    .input-label {{
        font-size: 11.5px;
        font-weight: 750;
        color: #1e293b;
        letter-spacing: -0.2px;
        cursor: pointer;
        background: transparent !important;
        background-color: transparent !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        pointer-events: auto !important;
    }}
    .forgot-pass-link {{
        font-size: 10.5px;
        color: #2563eb;
        cursor: pointer;
        text-decoration: none;
        font-weight: 600;
        background: transparent !important;
        background-color: transparent !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        pointer-events: auto !important;
    }}
    .forgot-pass-link:hover {{
        text-decoration: underline;
    }}

    .form-panel ::selection {{
        background: rgba(37, 99, 235, 0.15) !important;
        color: #0f172a !important;
    }}

    input[type="text"],
    input[type="password"],
    input[type="email"],
    .auth-input,
    input.auth-input,
    #in_user,
    #in_pass,
    #up_name,
    #up_user,
    #up_pass {{
        width: 100% !important;
        height: 38px !important;
        background: #ffffff !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 0 12px !important;
        font-size: 13px !important;
        font-weight: 550 !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        caret-color: #175cf2 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        outline: none !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        pointer-events: auto !important;
        cursor: text !important;
        user-select: text !important;
        -webkit-user-select: text !important;
        position: relative !important;
        z-index: 50 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }}
    input[type="text"]:hover,
    input[type="password"]:hover,
    input[type="email"]:hover,
    .auth-input:hover,
    #in_user:hover,
    #in_pass:hover,
    #up_name:hover,
    #up_user:hover,
    #up_pass:hover {{
        border-color: #94a3b8 !important;
    }}
    input[type="text"]:focus,
    input[type="password"]:focus,
    input[type="email"]:focus,
    .auth-input:focus,
    #in_user:focus,
    #in_pass:focus,
    #up_name:focus,
    #up_user:focus,
    #up_pass:focus {{
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.16) !important;
        background: #ffffff !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        -webkit-text-fill-color: #0f172a !important;
        caret-color: #175cf2 !important;
    }}
    .auth-input::placeholder,
    input[type="text"]::placeholder,
    input[type="password"]::placeholder,
    input[type="email"]::placeholder {{
        color: #94a3b8 !important;
        -webkit-text-fill-color: #94a3b8 !important;
        font-weight: 400 !important;
        font-size: 12px !important;
    }}

    .btn-auth-submit {{
        width: 100%;
        height: 40px;
        background: linear-gradient(135deg, #175cf2 0%, #1046c4 100%) !important;
        color: #ffffff !important;
        border: none;
        border-radius: 10px !important;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        cursor: pointer;
        user-select: none !important;
        -webkit-user-select: none !important;
        box-shadow: 0 8px 20px -3px rgba(23, 92, 242, 0.42);
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 5px;
    }}
    .btn-auth-submit *, .btn-auth-submit span {{
        background: transparent !important;
        background-color: transparent !important;
        color: #ffffff !important;
    }}
    .btn-auth-submit:hover {{
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 12px 24px -2px rgba(23, 92, 242, 0.55);
    }}
    .btn-auth-submit:active {{
        transform: translateY(0) scale(0.985);
    }}

    .checkbox-row {{
        margin: 6px 0 8px 0;
        width: 100%;
    }}
    .checkbox-label {{
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        font-size: 11px !important;
        color: #64748b !important;
        cursor: pointer !important;
        user-select: none !important;
    }}
    input[type="checkbox"],
    .checkbox-input,
    input.checkbox-input {{
        width: 16px !important;
        height: 16px !important;
        min-width: 16px !important;
        max-width: 16px !important;
        min-height: 16px !important;
        max-height: 16px !important;
        accent-color: #2563eb !important;
        cursor: pointer !important;
        margin: 0 !important;
        padding: 0 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 4px !important;
        display: inline-block !important;
        flex-shrink: 0 !important;
        position: static !important;
        z-index: 10 !important;
    }}
    .terms-link {{
        color: #334155;
        text-decoration: underline;
    }}

    .bottom-switch-text {{
        margin-top: 9px;
        text-align: center;
        font-size: 11px;
        color: #64748b;
        background: transparent !important;
        background-color: transparent !important;
        user-select: none !important;
        -webkit-user-select: none !important;
    }}
    .bottom-switch-text span {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    .link-switch {{
        color: #175cf2;
        font-weight: 800;
        cursor: pointer;
        margin-left: 4px;
        background: transparent !important;
        background-color: transparent !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        transition: all 0.2s ease;
    }}
    .link-switch:hover {{
        color: #0d42bf;
        text-decoration: underline;
    }}

    .brand-item-greeting {{
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 1.5px;
        color: #ffffff;
        opacity: 0.95;
        text-transform: uppercase;
    }}
    .brand-item-center {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: auto 0;
        position: relative;
        z-index: 5;
    }}
    .brand-rocket-badge {{
        width: 66px;
        height: 66px;
        border-radius: 50%;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 10px 24px rgba(10, 37, 100, 0.28);
        margin: 0 auto 12px auto;
        animation: rocketFloatAnim 3.2s ease-in-out infinite;
    }}
    .brand-rocket-badge svg {{
        width: 36px;
        height: 36px;
        color: #155dfc;
    }}
    @keyframes rocketFloatAnim {{
        0%, 100% {{ transform: translateY(0); }}
        50% {{ transform: translateY(-5px); }}
    }}
    .brand-title {{
        font-size: 26px;
        font-weight: 850;
        letter-spacing: -0.5px;
        color: #ffffff;
        margin-bottom: 6px;
    }}
    .brand-desc {{
        font-size: 12px;
        line-height: 1.55;
        color: #ffffff;
        opacity: 0.92;
        max-width: 250px;
        font-weight: 350;
        margin: 0 auto 18px auto;
    }}
    .btn-overlay-nav {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 9px 22px;
        border: 1.5px solid rgba(255, 255, 255, 0.85);
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(8px);
        border-radius: 10px;
        color: #ffffff;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        user-select: none;
    }}
    .btn-overlay-nav:hover {{
        background: #ffffff;
        color: #1056e8;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    }}
    .brand-item-footer {{
        font-size: 8px;
        font-weight: 700;
        letter-spacing: 0.4px;
        color: #ffffff;
        opacity: 0.9;
        text-transform: uppercase;
        text-align: center;
        line-height: 1.35;
        max-width: 92%;
        margin: 0 auto;
    }}

    .auth-alert {{
        padding: 6px 10px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
        text-align: left;
        width: 100%;
    }}
    .alert-error {{
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #b91c1c;
    }}
    .alert-success {{
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #15803d;
    }}

    /* Notifikasi Mengambang (Floating Toast Notification) */
    .floating-toast {{
        position: fixed;
        top: 24px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999999;
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(255, 255, 255, 0.97);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1.5px solid rgba(16, 185, 129, 0.45);
        padding: 10px 18px;
        border-radius: 50px;
        box-shadow: 0 16px 36px rgba(16, 185, 129, 0.22), 0 4px 16px rgba(15, 23, 42, 0.08);
        animation: toastFloatIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards, toastAutoFade 0.6s ease-in 6s forwards;
        max-width: 90vw;
        pointer-events: auto;
    }}

    @keyframes toastFloatIn {{
        0% {{
            opacity: 0;
            transform: translateX(-50%) translateY(-28px) scale(0.92);
        }}
        100% {{
            opacity: 1;
            transform: translateX(-50%) translateY(0) scale(1);
        }}
    }}

    @keyframes toastAutoFade {{
        0% {{
            opacity: 1;
            transform: translateX(-50%) translateY(0) scale(1);
        }}
        100% {{
            opacity: 0;
            transform: translateX(-50%) translateY(-20px) scale(0.95);
            visibility: hidden;
            pointer-events: none;
        }}
    }}

    .toast-icon-pulse {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
        flex-shrink: 0;
    }}

    .toast-content {{
        display: flex;
        flex-direction: column;
        gap: 1px;
    }}

    .toast-title {{
        font-size: 13px;
        font-weight: 800;
        color: #065f46;
        line-height: 1.2;
    }}

    .toast-msg {{
        font-size: 12px;
        font-weight: 500;
        color: #047857;
        line-height: 1.3;
    }}

    .toast-close-btn {{
        background: transparent;
        border: none;
        color: #059669;
        font-size: 20px;
        line-height: 1;
        cursor: pointer;
        padding: 2px 6px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.7;
        transition: opacity 0.2s, background 0.2s;
        margin-left: 6px;
    }}

    .toast-close-btn:hover {{
        opacity: 1;
        background: rgba(16, 185, 129, 0.15);
    }}

    .email-live-feedback {{
        display: none;
        font-size: 11px;
        font-weight: 600;
        margin-top: 5px;
        padding: 5px 9px;
        border-radius: 6px;
        line-height: 1.35;
        background: #fff1f2;
        border: 1px solid #fecdd3;
        color: #be123c;
        text-align: left;
        animation: fadeInMsg 0.2s ease-in-out;
    }}
    @keyframes fadeInMsg {{
        from {{ opacity: 0; transform: translateY(-4px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @media (max-width: 820px) {{
        .auth-viewport-wrapper {{
            height: auto !important;
            min-height: 100vh !important;
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
            padding: 20px 12px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        .slider-card {{
            width: 100% !important;
            max-width: 440px !important;
            height: auto !important;
            min-height: 520px !important;
            border-radius: 22px !important;
            margin: auto !important;
        }}
        .form-panel {{
            width: 100% !important;
            padding: 24px 20px !important;
        }}
        .brand-overlay {{
            display: none !important;
        }}
        .sign-in-panel, .sign-up-panel {{
            position: relative !important;
            transform: none !important;
        }}
        .sign-in-panel {{
            display: flex !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }}
        .sign-up-panel {{
            display: none !important;
            pointer-events: none !important;
        }}
        #tab-signup:checked ~ .sign-in-panel,
        #tab-signup:checked ~ .slider-card .sign-in-panel,
        .slider-card.is-signup-mode .sign-in-panel {{
            display: none !important;
            pointer-events: none !important;
        }}
        #tab-signup:checked ~ .sign-up-panel,
        #tab-signup:checked ~ .slider-card .sign-up-panel,
        .slider-card.is-signup-mode .sign-up-panel {{
            display: flex !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }}
        #tab-signin:checked ~ .sign-up-panel,
        #tab-signin:checked ~ .slider-card .sign-up-panel,
        .slider-card.is-signin-mode .sign-up-panel {{
            display: none !important;
            pointer-events: none !important;
        }}
        #tab-signin:checked ~ .sign-in-panel,
        #tab-signin:checked ~ .slider-card .sign-in-panel,
        .slider-card.is-signin-mode .sign-in-panel {{
            display: flex !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }}
    }}
    """
    clean_css = "\n".join(l.strip() for l in css_rules.splitlines() if l.strip())
    st.markdown("<style>\n" + clean_css + "\n</style>", unsafe_allow_html=True)

    # Render Markup HTML Bersih (Setiap baris di-strip untuk mencegah Markdown menganggapnya indented code block)
    raw_html = f"""
<base target="_self">
<div class="auth-viewport-wrapper">
{floating_toast_html}
<div class="ambient-orb orb-1"></div>
<div class="ambient-orb orb-2"></div>

<div class="slider-card {card_mode_class}" id="authCard">

<input type="radio" id="tab-signup" name="auth_state" class="auth-radio-toggle" {checked_signup}>
<input type="radio" id="tab-signin" name="auth_state" class="auth-radio-toggle" {checked_signin}>

<div class="form-panel sign-in-panel">
<div class="form-header">
<div class="form-title">Sign In</div>
<p class="form-subtitle">Financial Distress Analysis System</p>
</div>

{alert_html_signin}

<form action="" method="GET" target="_self">
<input type="hidden" name="auth_action" value="signin">

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="in_user">Username / E-mail</label>
</div>
<input type="text" id="in_user" name="in_user" {val_attr} placeholder="Enter your username or email" required class="auth-input" autocomplete="username">
</div>

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="in_pass">Password</label>
<span class="forgot-pass-link" onclick="alert('Silakan hubungi administrator sistem untuk mereset kata sandi akun Anda.')">Lupa?</span>
</div>
<input type="password" id="in_pass" name="in_pass" placeholder="Enter your password" required class="auth-input" autocomplete="current-password">
</div>

<button type="submit" class="btn-auth-submit">
SIGN IN
</button>

<div class="bottom-switch-text">
<span>Belum punya akun?</span>
<label for="tab-signup" class="link-switch" onclick="switchAuthMode('signup')">Daftar sekarang</label>
</div>
</form>
</div>

<div class="form-panel sign-up-panel">
<div class="form-header">
<div class="form-title">Create account</div>
<p class="form-subtitle">create to your account for sign in</p>
</div>

{alert_html_signup}

<form action="" method="GET" target="_self" onsubmit="return validateSignUpSubmit(event)">
<input type="hidden" name="auth_action" value="signup">

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="up_name">Full Name</label>
</div>
<input type="text" id="up_name" name="up_name" placeholder="Enter your full name" required class="auth-input" autocomplete="name">
</div>

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="up_user">E-mail Address (@gmail / Instansi)</label>
</div>
<input type="email" id="up_user" name="up_user" placeholder="name@gmail.com or name@institution.ac.id" required class="auth-input" autocomplete="email" oninput="validateEmailLive(this)" onblur="validateEmailLive(this)">
<div id="email_validation_msg" class="email-live-feedback"></div>
</div>

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="up_pass">Password (Min. 6 Karakter)</label>
</div>
<input type="password" id="up_pass" name="up_pass" placeholder="Enter password (min. 6 chars)" required minlength="6" class="auth-input" autocomplete="new-password">
</div>

<div class="checkbox-row">
<label class="checkbox-label">
<input type="checkbox" name="up_terms" checked required class="checkbox-input">
<span>By Signing Up, I agree with <strong class="terms-link">Terms & Conditions</strong></span>
</label>
</div>

<button type="submit" class="btn-auth-submit">
SIGN UP
</button>

<div class="bottom-switch-text">
<span>Sudah punya akun?</span>
<label for="tab-signin" class="link-switch" onclick="switchAuthMode('signin')">Masuk di sini</label>
</div>
</form>
</div>

<div class="brand-overlay">
<div class="cloud-divider-right">
<svg viewBox="0 0 100 500" preserveAspectRatio="none" style="width:100%; height:100%;">
<path d="M 100,0 L 52,0 Q 8,60 48,125 Q 0,185 42,250 Q 6,325 50,385 Q 16,445 62,500 L 100,500 Z" fill="#60a5fa" opacity="0.45" />
<path d="M 100,0 L 68,0 Q 28,65 62,135 Q 18,205 58,275 Q 24,345 68,405 Q 34,465 78,500 L 100,500 Z" fill="#93c5fd" opacity="0.65" />
<path d="M 100,0 L 82,0 Q 45,70 78,145 Q 35,225 72,295 Q 38,365 82,425 Q 52,485 88,500 L 100,500 Z" fill="#ffffff" />
</svg>
</div>

<div class="cloud-divider-left">
<svg viewBox="0 0 100 500" preserveAspectRatio="none" style="width:100%; height:100%;">
<path d="M 100,0 L 52,0 Q 8,60 48,125 Q 0,185 42,250 Q 6,325 50,385 Q 16,445 62,500 L 100,500 Z" fill="#60a5fa" opacity="0.45" />
<path d="M 100,0 L 68,0 Q 28,65 62,135 Q 18,205 58,275 Q 24,345 68,405 Q 34,465 78,500 L 100,500 Z" fill="#93c5fd" opacity="0.65" />
<path d="M 100,0 L 82,0 Q 45,70 78,145 Q 35,225 72,295 Q 38,365 82,425 Q 52,485 88,500 L 100,500 Z" fill="#ffffff" />
</svg>
</div>

<div class="overlay-card card-for-signup">
<div class="brand-item-greeting">Welcome to</div>
<div class="brand-item-center">
<div class="brand-rocket-badge">
<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
<path d="M16 3 C23.18 3 29 8.82 29 16 C29 23.18 23.18 29 16 29 C8.82 29 3 23.18 3 16" />
<path d="M16 8 C20.42 8 24 11.58 24 16 C24 20.42 20.42 24 16 24 C11.58 24 8 20.42 8 16" />
<path d="M16 13 C17.66 13 19 14.34 19 16 C19 17.66 17.66 19 16 19 C14.34 19 13 17.66 13 16" />
</svg>
</div>
<div class="brand-title">Distress Prediction</div>
<div class="brand-desc">Bergabunglah dengan ekosistem analisis finansial distress.</div>
<label for="tab-signin" class="btn-overlay-nav" onclick="switchAuthMode('signin')">
<span>Sudah Punya Akun?</span>
<strong>Sign In ➔</strong>
</label>
</div>
<div class="brand-item-footer">535220037 &nbsp;|&nbsp; WAHYU PAMUNGKAS</div>
</div>

<div class="overlay-card card-for-signin">
<div class="brand-item-greeting">Welcome Back!</div>
<div class="brand-item-center">
<div class="brand-rocket-badge">
<svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
<path d="M16 3 C23.18 3 29 8.82 29 16 C29 23.18 23.18 29 16 29 C8.82 29 3 23.18 3 16" />
<path d="M16 8 C20.42 8 24 11.58 24 16 C24 20.42 20.42 24 16 24 C11.58 24 8 20.42 8 16" />
<path d="M16 13 C17.66 13 19 14.34 19 16 C19 17.66 17.66 19 16 19 C14.34 19 13 17.66 13 16" />
</svg>
</div>
<div class="brand-title">Halo, Pengguna!</div>
<div class="brand-desc">Masuk kembali untuk mengakses pengujian emiten, evaluasi XGBoost dan Altman Z'', dan histori prediksi.</div>
<label for="tab-signup" class="btn-overlay-nav" onclick="switchAuthMode('signup')">
<span>⬅ Belum Ada Akun?</span>
<strong>Sign Up</strong>
</label>
</div>
<div class="brand-item-footer">Prediksi Financial Distress pada Industri Manufaktur yang Terdaftar di Bursa Efek Indonesia dengan Pendekatan XGBoost dan Altman Z Score</div>
</div>

</div>
</div>
</div>
<img src="data:image/svg+xml;utf8,<svg></svg>" style="display:none;" onload="window.switchAuthMode=function(m){{try{{var c=document.getElementById('authCard'),i=document.getElementById('tab-signin'),u=document.getElementById('tab-signup');if(m==='signin'){{if(c){{c.classList.remove('is-signup-mode');c.classList.add('is-signin-mode');}}if(i)i.checked=true;if(u)u.checked=false;}}else{{if(c){{c.classList.remove('is-signin-mode');c.classList.add('is-signup-mode');}}if(u)u.checked=true;if(i)i.checked=false;}}}}catch(e){{}}}}; window.getEmailWarning=function(v){{try{{var s=(v||'').trim().toLowerCase();if(s.indexOf('@')===-1)return '';var p=s.split('@');if(p.length!==2)return '';var d=p[1].trim();if(!d)return '';if(d==='google.com')return 'Domain @google.com bukan layanan email pengguna. Harap gunakan @gmail.com atau email instansi resmi.';var gt=['gmai.com','gamil.com','gmial.com','gmaill.com','gmaik.com','gmal.com','gemail.com','gmeil.com','gmail.co','gmai.co','gmaul.com','gmaild.com'];if(gt.indexOf(d)!==-1)return 'Terdapat salah ketik pada domain. Maksud Anda @gmail.com?';if(d.indexOf('.con')!==-1&&d.slice(-4)==='.con')return 'Salah ketik: Ekstensi berakhiran .con. Maksud Anda berakhiran .com?';if(d.slice(-5)==='.comm'||d.slice(-4)==='.cmo')return 'Salah ketik ekstensi domain. Harap gunakan domain resmi seperti .com atau .ac.id.';var yt=['yaho.com','yahooo.com','yhaoo.com','yaho.co.id','yahooo.co.id'];if(yt.indexOf(d)!==-1)return 'Terdapat salah ketik pada domain. Maksud Anda @yahoo.com?';var mt=['hotmial.com','hotmai.com','outlok.com','outloo.com','outluk.com'];if(mt.indexOf(d)!==-1)return 'Terdapat salah ketik pada domain. Maksud Anda @outlook.com atau @hotmail.com?';var at=['iclou.com','icloude.com'];if(at.indexOf(d)!==-1)return 'Terdapat salah ketik pada domain. Maksud Anda @icloud.com?';var st=['facebook.com','instagram.com','twitter.com','x.com','tiktok.com','youtube.com','whatsapp.com','telegram.org'];if(st.indexOf(d)!==-1)return 'Domain @'+d+' bukan penyedia email pendaftaran akun. Harap gunakan @gmail.com atau email instansi resmi.';var dt=['mailinator.com','tempmail.com','10minutemail.com','guerrillamail.com','yopmail.com','trashmail.com'];if(dt.indexOf(d)!==-1)return 'Domain email sementara tidak diizinkan. Harap gunakan @gmail.com atau email instansi resmi.';if(d.indexOf('.')!==-1){{var okP=['gmail.com','googlemail.com','yahoo.com','yahoo.co.id','outlook.com','hotmail.com','live.com','icloud.com'];if(okP.indexOf(d)!==-1)return '';var okE=['.ac.id','.edu','.edu.id','.go.id','.gov','.co.id','.or.id','.sch.id','.mil.id'];var isI=false;for(var k=0;k!==okE.length;k++){{var ex=okE[k];if(d.indexOf(ex)!==-1&&d.slice(-ex.length)===ex){{isI=true;break;}}}}if(isI)return '';return 'Domain @'+d+' bukan penyedia email resmi yang valid. Harap gunakan email dari Google (@gmail.com) atau email resmi instansi/kampus (.ac.id, .co.id, .go.id).';}}return '';}}catch(e){{return '';}}}}; window.validateEmailLive=function(el){{try{{var e=el||document.getElementById('up_user');if(!e)return;var b=document.getElementById('email_validation_msg');var w=window.getEmailWarning(e.value);if(w){{if(b){{b.innerText='⚠️ '+w;b.style.display='block';}}e.style.borderColor='#ef4444';}}else{{if(b){{b.innerText='';b.style.display='none';}}e.style.borderColor='';}}}}catch(e){{}}}}; window.validateSignUpSubmit=function(ev){{try{{var e=document.getElementById('up_user');if(!e)return true;var v=(e.value||'').trim().toLowerCase(),p=v.split('@');if(p.length!==2||!p[1]||p[1].indexOf('.')===-1){{alert('Format email tidak valid. Harap gunakan email resmi yang lengkap (contoh: nama@gmail.com atau nama@instansi.ac.id).');e.focus();if(ev&&ev.preventDefault)ev.preventDefault();return false;}}var w=window.getEmailWarning(e.value);if(w){{window.validateEmailLive(e);alert('Peringatan Validasi Email:\n\n'+w+'\n\nHarap perbaiki alamat email Anda sebelum mendaftar.');e.focus();if(ev&&ev.preventDefault)ev.preventDefault();return false;}}}}catch(err){{}}return true;}}; setTimeout(function(){{var e=document.getElementById('up_user');if(e){{e.addEventListener('input',function(){{window.validateEmailLive(this);}});e.addEventListener('blur',function(){{window.validateEmailLive(this);}});e.addEventListener('change',function(){{window.validateEmailLive(this);}});}}}},300);"/>
"""
    clean_html = "\n".join(l.strip() for l in raw_html.splitlines() if l.strip())
    st.markdown(clean_html, unsafe_allow_html=True)

    st.stop()


# ---------- Configuration File Load ----------
if "config" not in st.session_state:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        st.session_state.config = json.load(f)

config = st.session_state.config

# ============================================================
# MENU UTAMA BERDASARKAN ROLE
# User: Rule tampilan sebelumnya (ringkas & terpadu)
# Admin: Tampilan lebih kompleks & modular (seperti file lama)
# ============================================================
if st.session_state.role == "admin":
    # Menu admin: Modul terpadu dengan Integrasi API di akhir (Pengaturan Profil diakses eksklusif via foto profil akun di bawah)
    MENU_ITEMS = [
        "Dashboard",
        "Data dan Laporan Keuangan",
        "Rasio dan Hasil Prediksi",
        "Perbandingan dan Evaluasi Model",
        "Histori Prediksi",
        "Pengaturan Model",
        "Integrasi API (Tahun)",
    ]
else:
    # Menu user: Memisahkan Dashboard & Input, Hasil Prediksi komprehensif, dan Integrasi API di paling akhir
    MENU_ITEMS = [
        "Dashboard",
        "Data dan Laporan Keuangan",
        "Hasil Prediksi",
        "Perbandingan Hasil",
        "Integrasi API (Tahun)",
    ]

MENU_ICONS = {
    "Dashboard": "🏠",
    "Data dan Laporan Keuangan": "📑",
    "Data & Laporan Keuangan": "📑",
    "Rasio dan Hasil Prediksi": "📈",
    "Rasio & Hasil Prediksi": "📈",
    "Hasil Prediksi": "📈",
    "Perbandingan dan Evaluasi Model": "⚖️",
    "Perbandingan & Evaluasi Model": "⚖️",
    "Perbandingan Hasil": "⚖️",
    "Histori Prediksi": "📜",
    "Manajemen Pengguna": "👥",
    "Data Pengguna": "👥",
    "Pengaturan Model": "⚙️",
    "Pengaturan Profil": "👤",
    "Pengaturan Akun": "👤",
    "Profil": "👤",
    "Profile": "👤",
    "Integrasi API (Tahun)": "🌐",
    "Integrasi API Pasar": "🌐",
    "Integrasi API Tahun": "🌐",
    "Dashboard Sistem": "🏠",
    "Dashboard dan Analisis": "🏠",
    "Dashboard & Analisis": "🏠",
    "Dashboard Prediksi": "📈",
    "Data Perusahaan": "🏢",
    "Laporan Keuangan": "📄",
    "Rasio Keuangan": "📊",
    "Evaluasi Model": "🔬",
}

MENU_TEXTS = {
    "Dashboard": "Dashboard",
    "Data dan Laporan Keuangan": "Data Keuangan",
    "Data & Laporan Keuangan": "Data Keuangan",
    "Rasio dan Hasil Prediksi": "Hasil Prediksi",
    "Rasio & Hasil Prediksi": "Hasil Prediksi",
    "Hasil Prediksi": "Hasil Prediksi",
    "Perbandingan dan Evaluasi Model": "Evaluasi Model",
    "Perbandingan & Evaluasi Model": "Evaluasi Model",
    "Perbandingan Hasil": "Evaluasi Model",
    "Histori Prediksi": "Histori Prediksi",
    "Manajemen Pengguna": "Manajemen Pengguna",
    "Data Pengguna": "Manajemen Pengguna",
    "Pengaturan Model": "Pengaturan Model",
    "Pengaturan Profil": "Pengaturan Profil",
    "Pengaturan Akun": "Pengaturan Profil",
    "Profil": "Pengaturan Profil",
    "Profile": "Pengaturan Profil",
    "Integrasi API (Tahun)": "Integrasi API",
    "Integrasi API Pasar": "Integrasi API",
    "Integrasi API Tahun": "Integrasi API",
    "Dashboard Sistem": "Dashboard",
    "Dashboard dan Analisis": "Dashboard",
    "Dashboard & Analisis": "Dashboard",
    "Dashboard Prediksi": "Hasil Prediksi",
    "Data Perusahaan": "Data Perusahaan",
    "Laporan Keuangan": "Laporan Keuangan",
    "Rasio Keuangan": "Rasio Keuangan",
    "Evaluasi Model": "Evaluasi Model",
}

# Format dengan ikon diikuti teks tebal Markdown agar tag <strong> dapat dikontrol presisi via CSS
MENU_LABELS = {
    key: f"{MENU_ICONS.get(key, '🔹')}  **{MENU_TEXTS.get(key, key)}**"
    for key in set(list(MENU_ICONS.keys()) + list(MENU_TEXTS.keys()))
}

if st.session_state.sidebar_visible:
    sidebar_col, content_col = st.columns([0.95, 3.05], gap="medium")

    with sidebar_col:
        role_label = "System Administrator" if st.session_state.role == "admin" else "Financial Analyst"
        cat_title = "ANALISIS DAN PREDIKSI" if st.session_state.role == "admin" else "NAVIGATION"

        # Header Atas Sidebar: Vault Marker + Close Row (Mobile) + Logo Brand + Section Label
        st.markdown(
            f"""
            <div class='sidebar-vault-container' style='display:none;'></div>
            <div class="mobile-drawer-close-row">
                <div class="mobile-drawer-title">NAVIGASI SISTEM</div>
                <button type="button" class="mobile-drawer-close-btn" onclick="(window.parent||window).document.body.classList.remove('mobile-nav-open');" title="Tutup Menu Navigasi">
                    <span>✕</span>
                    <span>Tutup</span>
                </button>
            </div>
            <div class="sidebar-logo-header" title="Distress Prediction - Risk Intelligence">
                <div class="sidebar-logo-icon">
                    <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
                        <path d="M16 3 C23.18 3 29 8.82 29 16 C29 23.18 23.18 29 16 29 C8.82 29 3 23.18 3 16" />
                        <path d="M16 8 C20.42 8 24 11.58 24 16 C24 20.42 20.42 24 16 24 C11.58 24 8 20.42 8 16" />
                        <path d="M16 13 C17.66 13 19 14.34 19 16 C19 17.66 17.66 19 16 19 C14.34 19 13 17.66 13 16" />
                    </svg>
                </div>
                <div class="sidebar-logo-text-col">
                    <span class="sidebar-logo-title">Distress Prediction</span>
                    <span class="sidebar-logo-subtitle">Risk Intelligence</span>
                </div>
            </div>
            <div class='sidebar-section-label'>{cat_title}</div>
            """,
            unsafe_allow_html=True,
        )

        # Validasi jika halaman aktif saat ini tidak ada di menu role saat ini
        # Halaman "Pengaturan Profil" dikecualikan karena diakses secara eksklusif lewat tombol pada foto profil / kartu akun di bawah
        if st.session_state.page not in MENU_ITEMS and st.session_state.page != "Pengaturan Profil":
            set_page(MENU_ITEMS[0])

        def _on_menu_change():
            val = st.session_state.get("custom_page_menu")
            if val and val in MENU_ITEMS:
                st.session_state.page = val
                st.session_state._last_nav_page = val
                st.session_state.menu_scroll_top = True

        if st.session_state.page == "Pengaturan Profil":
            st.session_state.custom_page_menu = None
            radio_idx = None
            st.session_state._last_nav_page = "Pengaturan Profil"
        else:
            if st.session_state.page in MENU_ITEMS:
                st.session_state.custom_page_menu = st.session_state.page
            elif st.session_state.get("custom_page_menu") in MENU_ITEMS:
                st.session_state.custom_page_menu = st.session_state.custom_page_menu
                st.session_state.page = st.session_state.custom_page_menu
            else:
                st.session_state.custom_page_menu = MENU_ITEMS[0]
                st.session_state.page = MENU_ITEMS[0]
            st.session_state._last_nav_page = st.session_state.custom_page_menu
            radio_idx = MENU_ITEMS.index(st.session_state.custom_page_menu)

        selected_page = st.radio(
            "MENU",
            MENU_ITEMS,
            index=radio_idx,
            format_func=lambda item: MENU_LABELS.get(item, item),
            label_visibility="collapsed",
            key="custom_page_menu",
            on_change=_on_menu_change,
        )

        if selected_page and selected_page in MENU_ITEMS and selected_page != st.session_state.page:
            set_page(selected_page)
            st.rerun()

        # Dynamic Flexbox Spacer (Menyerap seluruh ruang vertikal di tengah agar profil akun menempel di bawah)
        st.markdown("<div class='sidebar-spacer'></div>", unsafe_allow_html=True)

        # Bagian Bawah: Informasi Akun / Profil Pengguna (Menempel di Dasar Sidebar)
        st.markdown(
            """
            <div class='sidebar-section-label sidebar-account-label'>ACCOUNT</div>
            """,
            unsafe_allow_html=True,
        )

        user_display_name = st.session_state.username if st.session_state.username else "User"
        cur_th = st.session_state.get("theme", "light")
        is_admin_user = (st.session_state.role == "admin")

        saved_prof = get_user_profile(user_display_name) or {}
        if st.session_state.get("user_fullname"):
            user_full_name = st.session_state.user_fullname
        elif saved_prof.get("full_name"):
            user_full_name = saved_prof["full_name"]
        else:
            user_full_name = "System Administrator" if is_admin_user else (user_display_name.capitalize() if user_display_name else "User")

        if st.session_state.get("user_email"):
            user_email = st.session_state.user_email
        elif saved_prof.get("email"):
            user_email = saved_prof["email"]
        else:
            user_email = f"{user_display_name.lower()}@distress.ai" if "@" not in user_display_name else user_display_name

        active_avatar = st.session_state.get("user_avatar") or saved_prof.get("avatar_data", "")

        if cur_th == "light":
            avatar_border = "#2563eb"
            avatar_dot_border = "#ffffff"
            avatar_ph_bg = "#e2e8f0"
        else:
            avatar_border = "#38bdf8"
            avatar_dot_border = "#171820"
            avatar_ph_bg = "rgba(30, 41, 59, 0.85)"

        if active_avatar:
            avatar_elem_html = f'<img src="{active_avatar}" alt="Avatar" class="user-avatar-img" style="border:2px solid {avatar_border} !important; width:38px; height:38px; border-radius:50%; object-fit:cover;" />'
        else:
            avatar_elem_html = f'<div class="user-avatar-img" style="border:2px solid {avatar_border} !important; width:38px; height:38px; border-radius:50%; background:{avatar_ph_bg}; display:flex; align-items:center; justify-content:center; font-size:18px; line-height:1;" title="Foto profil belum diatur">👤</div>'

        col_uinfo, col_uedit = st.columns([0.84, 0.16], gap="small")
        with col_uinfo:
            st.markdown(
                f"""<div class="sidebar-user-block"><div class="user-avatar-wrapper">{avatar_elem_html}<span class="user-status-dot" style="border:2px solid {avatar_dot_border} !important;" title="Sesi Online Aktif"></span></div><div class="user-meta-col"><div class="user-name-bold">{user_full_name}</div><div class="user-email-text">{user_email}</div></div></div>""",
                unsafe_allow_html=True,
            )
        with col_uedit:
            # Tombol Ikon Panah Indikator: Navigasi ke Halaman Sendiri Pengaturan Profile
            is_on_profile = (st.session_state.page == "Pengaturan Profil")
            help_txt = "Kembali ke Dashboard" if is_on_profile else "Buka Halaman Pengaturan Profil & Akun"
            btn_symbol = "✕" if is_on_profile else "⌵"
            if st.button(btn_symbol, key="btn_quick_edit_profile", help=help_txt):
                if is_on_profile:
                    set_page("Dashboard")
                else:
                    set_page("Pengaturan Profil")
                st.session_state.active_account_modal = None
                st.rerun()

else:
    content_col = st.container()

page = st.session_state.page

# ---------- Helpers ----------
def set_ratios_from_financials(fin):
    ratios = build_features_from_financials(complete_financial_values(fin))
    if not isinstance(ratios, dict):
        raise ValueError("Fitur rasio keuangan tidak berhasil dihitung.")
    required = ("X1", "X2", "X3", "X4", "X5")
    missing = [key for key in required if key not in ratios]
    if missing:
        raise ValueError(f"Fitur rasio belum lengkap: {', '.join(missing)}")
    st.session_state.ratios = {key: float(ratios[key]) for key in required}
    if "_capping_audit" in ratios:
        st.session_state["capping_audit"] = ratios["_capping_audit"]
    if "_raw_ratios" in ratios:
        st.session_state["raw_ratios"] = ratios["_raw_ratios"]

def current_results():
    r = st.session_state.ratios
    z = altman_z_score(r, config["altman_coefficients"])
    z_cls = altman_classification(z, config["altman_thresholds"])
    mda = mda_score(r, config["mda_coefficients"])
    mda_th = config.get("mda_thresholds", config.get("mda_threshold", 0.3844))
    mda_cls = mda_classification(mda, mda_th)
    xgb_th = config.get("xgb_thresholds", config.get("xgb_threshold", 0.50))
    xgb_prob, xgb_label = xgboost_predict(
        r,
        str(MODEL_PATH) if MODEL_PATH.exists() else None,
        threshold=xgb_th,
    )
    # Sinkronisasi ke session_state agar seluruh modul UI dan dashboard terintegrasi penuh
    st.session_state.xgb_probability = xgb_prob
    st.session_state.xgb_label = xgb_label
    return z, z_cls, mda, mda_cls, xgb_prob, xgb_label

def altman_formula(coefficients, latex=False):
    terms = []
    for key in ("X1", "X2", "X3", "X4"):
        ratio = f"X_{{{key[1:]}}}" if latex else key
        terms.append(f"{float(coefficients[key]):.2f}{ratio}")
    formula = " + ".join(terms)
    return rf"Z^{{\prime\prime}} = {formula}" if latex else f"Z'' = {formula}"

def mda_formula(coefficients, latex=False):
    terms = []
    for key in ("X1", "X2", "X3", "X4"):
        ratio = f"X_{{{key[1:]}}}" if latex else key
        terms.append(f"{float(coefficients.get(key, 0.0)):.4f}{ratio}")
    formula = " + ".join(terms)
    if "intercept" in coefficients and float(coefficients.get("intercept", 0.0)) != 0.0:
        formula = f"{float(coefficients['intercept']):.4f} + " + formula
    return rf"Z^{{\prime\prime}}_{{\text{{baru}}}} = {formula}" if latex else f"Z''baru = {formula}"

def load_demo_data_icbp():
    """Helper untuk memuat data sampel emiten manufaktur (ICBP 2024) dan langsung mengaktifkan status analisis."""
    st.session_state.company = "PT Indofood CBP Sukses Makmur Tbk"
    st.session_state.ticker = "ICBP"
    st.session_state.sector = "Consumer Non-Cyclicals / Food & Beverage"
    st.session_state.year = 2024
    demo_fin = {
        "ticker": "ICBP",
        "report_year": 2024,
        "current_assets": 58348000000000.0,
        "current_liabilities": 25123000000000.0,
        "total_assets": 121542000000000.0,
        "retained_earnings": 38450000000000.0,
        "ebit": 16250000000000.0,
        "total_liabilities": 54890000000000.0,
        "total_equity": 66652000000000.0,
        "total_revenue": 67910000000000.0,
        "market_cap": 128275000000000.0,
        "net_income": 9560000000000.0,
        "total_debt": 41200000000000.0,
        "interest_expense": 2400000000000.0,
        "working_capital": 33225000000000.0,
    }
    st.session_state.financials = demo_fin
    for k, v in demo_fin.items():
        str_v = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else str(v)
        st.session_state[f"manual_{k}"] = str_v
        st.session_state[f"user_input_{k}"] = str_v
    set_ratios_from_financials(demo_fin)
    st.session_state.has_analyzed = True

def render_admin_user_management(embedded: bool = False):
    """
    Modul Manajemen Akun Pengguna Terdaftar untuk Administrator.
    Menampilkan data pengguna lengkap dengan jenis email (@gmail / instansi), tanggal daftar,
    pencarian & filter, serta pengaturan akun pengguna (lihat profil, edit data, reset sandi, dan hapus akun).
    """
    if st.session_state.role != "admin":
        st.error("Akses ditolak! Halaman ini khusus untuk Administrator.")
        st.stop()

    if not embedded:
        section_title(
            "Manajemen Pengguna Terdaftar dan Kontrol Akun",
            "Kelola data pengguna yang telah mendaftar, pantau institusi/organisasi, reset kata sandi, dan atur hak akses",
            tone="blue",
        )

    prefix = "emb_usr" if embedded else "main_usr"

    # Notifikasi Flash Sukses Manajemen Akun
    if "user_mgmt_flash_success" in st.session_state:
        succ_msg = st.session_state.pop("user_mgmt_flash_success")
        st.success(succ_msg)
        try:
            st.toast(succ_msg, icon="🎉")
        except Exception:
            pass

    # 1. Ambil data pengguna terbaru
    df_users = get_all_users()
    if df_users.empty:
        st.warning("Belum ada data pengguna yang terdaftar di sistem.")
        return

    # Pastikan seluruh kolom standar tersedia
    for req_col in ["username", "role", "email", "full_name", "institution", "created_at"]:
        if req_col not in df_users.columns:
            df_users[req_col] = ""

    df_users["email"] = df_users["email"].fillna("")
    df_users["full_name"] = df_users["full_name"].fillna("")
    df_users["institution"] = df_users["institution"].fillna("")
    df_users["created_at"] = df_users["created_at"].fillna("-")

    # Klasifikasi jenis email/akun
    def _classify_email(row):
        e = str(row.get("email", "")).strip().lower()
        if "gmail.com" in e or "googlemail.com" in e:
            return "Personal (@gmail)"
        elif any(ext in e for ext in [".ac.id", ".edu", ".go.id", ".gov", ".co.id", ".sch.id", ".or.id", ".mil.id", ".org", ".com", ".net", ".id"]):
            return "Email Instansi / Lembaga"
        elif e:
            return "Email Lainnya"
        return "Belum Tercatat"

    df_users["Kategori Akun"] = df_users.apply(_classify_email, axis=1)

    # 2. Metric Cards
    total_users = len(df_users)
    pending_users = int((df_users["status"] == "pending").sum()) if "status" in df_users.columns else 0
    active_users = int((df_users["status"] == "active").sum()) if "status" in df_users.columns else total_users
    admin_users = int((df_users["role"] == "admin").sum())

    m1, m2, m3, m4 = st.columns(4)
    metric_card(m1, "Total Pengguna", f"{total_users} Akun", "Terdaftar di database", tone="blue", trend="👥 Total")
    metric_card(m2, "Akun Aktif", f"{active_users} Akun", "Akses Diizinkan", tone="emerald", trend="🟢 Aktif")
    metric_card(m3, "Menunggu Approval", f"{pending_users} Akun", "Perlu Verifikasi Admin", tone="amber" if pending_users > 0 else "blue", trend="🟡 Pending")
    metric_card(m4, "Administrator", f"{admin_users} Akun", "Akses Penuh Sistem", tone="purple", trend="🛡️ Admin")

    if pending_users > 0:
        st.warning(f"⚠️ **Perhatian Administrator:** Terdapat **{pending_users} akun pengguna baru** yang berstatus **'Menunggu Persetujuan' (Pending)**. Akun tersebut tidak dapat masuk ke sistem sampai Anda menyetujuinya pada tab **'🛡️ Kelola Status & Persetujuan'** di bawah.")

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # 3. Filter & Search Bar
    with st.container(border=True):
        st.markdown("<div style='font-size:15px;font-weight:800;color:#2563eb;margin-bottom:8px;'>🔍 Cari & Filter Data Pengguna Terdaftar</div>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns([2.6, 1.4])
        with col_s1:
            search_query = st.text_input(
                "Pencarian Pengguna",
                placeholder="Cari berdasarkan nama, username, email (@gmail/instansi), atau lembaga...",
                key=f"{prefix}_search_input",
                label_visibility="collapsed",
            ).strip().lower()
        with col_s2:
            filter_cat = st.selectbox(
                "Filter Kategori",
                [
                    "Semua Akun Pengguna",
                    "🟡 Menunggu Persetujuan (Pending)",
                    "🟢 Akun Aktif (Disetujui)",
                    "🔴 Akun Dinonaktifkan (Disabled)",
                    "Personal (@gmail)",
                    "Email Instansi / Lembaga",
                    "Role: Admin",
                    "Role: User",
                ],
                key=f"{prefix}_filter_select",
                label_visibility="collapsed",
            )

        filtered_df = df_users.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df["username"].str.lower().str.contains(search_query, na=False)
                | filtered_df["full_name"].str.lower().str.contains(search_query, na=False)
                | filtered_df["email"].str.lower().str.contains(search_query, na=False)
                | filtered_df["institution"].str.lower().str.contains(search_query, na=False)
            ]

        if filter_cat == "🟡 Menunggu Persetujuan (Pending)":
            filtered_df = filtered_df[filtered_df["status"] == "pending"] if "status" in filtered_df.columns else filtered_df
        elif filter_cat == "🟢 Akun Aktif (Disetujui)":
            filtered_df = filtered_df[filtered_df["status"] == "active"] if "status" in filtered_df.columns else filtered_df
        elif filter_cat == "🔴 Akun Dinonaktifkan (Disabled)":
            filtered_df = filtered_df[filtered_df["status"] == "disabled"] if "status" in filtered_df.columns else filtered_df
        elif filter_cat == "Personal (@gmail)":
            filtered_df = filtered_df[filtered_df["Kategori Akun"] == "Personal (@gmail)"]
        elif filter_cat == "Email Instansi / Lembaga":
            filtered_df = filtered_df[filtered_df["Kategori Akun"] == "Email Instansi / Lembaga"]
        elif filter_cat == "Role: Admin":
            filtered_df = filtered_df[filtered_df["role"] == "admin"]
        elif filter_cat == "Role: User":
            filtered_df = filtered_df[filtered_df["role"] == "user"]

        st.caption(f"Menampilkan **{len(filtered_df)}** dari **{total_users}** pengguna terdaftar.")

        display_df = filtered_df[["username", "full_name", "email", "institution", "role", "status", "created_at"]].copy() if "status" in filtered_df.columns else filtered_df[["username", "full_name", "email", "institution", "role", "created_at"]].copy()
        status_map = {
            "active": "🟢 Aktif (Disetujui)",
            "pending": "🟡 Menunggu Persetujuan",
            "disabled": "🔴 Dinonaktifkan",
        }
        if "status" in display_df.columns:
            display_df["status"] = display_df["status"].map(status_map).fillna("🟢 Aktif (Disetujui)")
            display_df.columns = ["Username", "Nama Lengkap", "Alamat Email", "Instansi / Lembaga", "Peran (Role)", "Status Akun", "Tanggal Mendaftar"]
        else:
            display_df.columns = ["Username", "Nama Lengkap", "Alamat Email", "Instansi / Lembaga", "Peran (Role)", "Tanggal Mendaftar"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # 4. Pengaturan Data Pengguna (Tabs)
    st.markdown("### ⚙️ Pengaturan dan Aksi Akun Pengguna")
    st.caption("Pilih akun pengguna yang telah mendaftar untuk melihat ringkasan profil, memperbarui data, mereset sandi, mengelola status akses, atau menghapus akun.")

    tab_status, tab_inspect, tab_edit, tab_pwd, tab_add, tab_del = st.tabs([
        "🛡️ Kelola Status & Persetujuan",
        "📋 Detail dan Profil Pengguna",
        "✏️ Edit Data Pengguna",
        "🔑 Reset Kata Sandi",
        "➕ Tambah Akun Manual",
        "🗑️ Hapus Akun",
    ])

    user_list = df_users["username"].tolist()
    non_admin_list = [u for u in user_list if u.lower() != "admin"]

    # TAB 1: Kelola Status & Persetujuan (Pencegahan Akses Sembarangan)
    with tab_status:
        st.markdown("##### 🛡️ Manajemen Status & Persetujuan Akun Pengguna")
        st.caption("Pencegahan akses sembarangan: Tinjau dan kelola hak akses akun yang mendaftar. Pengguna berstatus 'Pending' tidak dapat login sampai disetujui.")

        pending_df = df_users[df_users["status"] == "pending"] if "status" in df_users.columns else pd.DataFrame()

        if not pending_df.empty:
            st.markdown(f"""
            <div style="background:#fffbeb;border:1.5px solid #fde68a;border-radius:10px;padding:12px 16px;margin-bottom:14px;">
                <div style="font-size:13.5px;font-weight:750;color:#92400e;">⚠️ Terdapat {len(pending_df)} Pendaftaran Menunggu Persetujuan</div>
                <div style="font-size:12px;color:#b45309;margin-top:3px;">Pengguna berikut telah mendaftar namun belum memiliki izin akses ke sistem sebelum diaktifkan oleh Administrator.</div>
            </div>
            """, unsafe_allow_html=True)

            c_btn1, c_btn2 = st.columns([1.8, 2.2])
            with c_btn1:
                if st.button("✅ Setujui & Aktifkan Semua Akun Pending", key=f"{prefix}_approve_all_pending", type="primary", use_container_width=True):
                    approved_cnt = 0
                    for pu in pending_df["username"].tolist():
                        ok_up, _ = update_user_status(pu, "active")
                        if ok_up:
                            approved_cnt += 1
                    st.session_state["user_mgmt_flash_success"] = f"✅ Berhasil menyetujui dan mengaktifkan {approved_cnt} akun pengguna!"
                    st.rerun()

        st.markdown("###### 🔍 Tinjau & Ubah Status Akses Pengguna")
        if user_list:
            pending_usernames = pending_df["username"].tolist() if not pending_df.empty else []
            sorted_user_list = pending_usernames + [u for u in user_list if u not in pending_usernames]

            selected_status_user = st.selectbox(
                "Pilih akun pengguna yang ingin dikelola:",
                sorted_user_list,
                key=f"{prefix}_status_user_sel",
                format_func=lambda u: f"[{df_users.loc[df_users['username'] == u, 'status'].values[0].upper() if 'status' in df_users.columns and len(df_users.loc[df_users['username'] == u, 'status'].values) > 0 else 'ACTIVE'}] {u} — {df_users.loc[df_users['username'] == u, 'full_name'].values[0] or u} ({df_users.loc[df_users['username'] == u, 'email'].values[0] or '-'})"
            )

            u_stat_prof = get_user_profile(selected_status_user) or {}
            cur_stat = (u_stat_prof.get("status") or "active").lower()

            col_sinfo1, col_sinfo2 = st.columns([1.3, 1.7])
            with col_sinfo1:
                with st.container(border=True):
                    st.markdown(f"**Nama Lengkap:** {u_stat_prof.get('full_name') or selected_status_user}")
                    st.markdown(f"**Username:** `{selected_status_user}`")
                    st.markdown(f"**Email:** `{u_stat_prof.get('email') or '-'}`")
                    st.markdown(f"**Instansi:** {u_stat_prof.get('institution') or '-'}")
                    st.markdown(f"**Peran (Role):** `{u_stat_prof.get('role') or 'user'}`")
                    badge_color = "#10b981" if cur_stat == "active" else ("#f59e0b" if cur_stat == "pending" else "#ef4444")
                    badge_label = "🟢 Aktif (Bisa Login)" if cur_stat == "active" else ("🟡 Menunggu Persetujuan (Pending)" if cur_stat == "pending" else "🔴 Dinonaktifkan (Diblokir)")
                    st.markdown(f"**Status Akses:** <span style='background:{badge_color}18;color:{badge_color};border:1px solid {badge_color}40;padding:2px 8px;border-radius:6px;font-weight:700;'>{badge_label}</span>", unsafe_allow_html=True)
            
            with col_sinfo2:
                with st.container(border=True):
                    st.markdown("###### Tetapkan Status Baru:")
                    status_options = {
                        "active": "🟢 Aktifkan Akun (Pengguna dapat masuk & mengakses dashboard)",
                        "pending": "🟡 Tunda Akun (Status 'Pending' - menunggu verifikasi ulang)",
                        "disabled": "🔴 Nonaktifkan / Blokir Akun (Mencegah pengguna masuk)",
                    }
                    new_stat_pick = st.radio(
                        "Status Pengguna:",
                        options=["active", "pending", "disabled"],
                        format_func=lambda s: status_options[s],
                        index=["active", "pending", "disabled"].index(cur_stat) if cur_stat in ["active", "pending", "disabled"] else 0,
                        key=f"{prefix}_radio_status_pick",
                        label_visibility="collapsed"
                    )

                    btn_save_status = st.button("💾 Simpan Perubahan Status Akun", type="primary", use_container_width=True, key=f"{prefix}_save_status_btn")
                    if btn_save_status:
                        ok_stat, msg_stat = update_user_status(selected_status_user, new_stat_pick)
                        if ok_stat:
                            st.session_state["user_mgmt_flash_success"] = f"✅ Status akun '{selected_status_user}' berhasil diperbarui!"
                            st.rerun()
                        else:
                            st.error(msg_stat)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("###### 🌐 Sistem Deteksi Cerdas & Persetujuan Otomatis Email")
            st.caption(
                "Sistem bekerja secara cerdas dan otomatis mendeteksi kredibilitas email pendaftar tanpa memerlukan kode akses:\n\n"
                "- 🏛️ **Email Instansi Resmi & Kampus (.ac.id, .edu, .co.id, .go.id, .or.id, .sch.id):** Langsung **Disetujui Otomatis (Active)** sehingga mitra/rekan instansi dapat langsung masuk tanpa hambatan.\n"
                "- 📧 **Email Publik Terpercaya (@gmail.com, @yahoo.com, @outlook.com):** Langsung **Disetujui Otomatis (Active)** jika domain sah dan benar.\n"
                "- 🛡️ **Pencegahan Otomatis Email Palsu/Salah Ketik:** Sistem otomatis mendeteksi dan menolak salah ketik (seperti `@google.com`, `@gamil.com`), platform non-email (medsos), dan domain email sementara (*disposable*)."
            )

    # TAB 2: Detail & Profil Pengguna
    with tab_inspect:
        st.markdown("##### 📋 Ringkasan dan Profil Lengkap Pengguna")
        if user_list:
            selected_user_ins = st.selectbox(
                "Pilih pengguna untuk dilihat detailnya:",
                user_list,
                key=f"{prefix}_inspect_user_sel",
                format_func=lambda u: f"{u} — {df_users.loc[df_users['username'] == u, 'full_name'].values[0] or u} ({df_users.loc[df_users['username'] == u, 'email'].values[0] or 'No Email'})",
            )
            prof = get_user_profile(selected_user_ins) or {}
            
            c_ins1, c_ins2 = st.columns([1.2, 1.8])
            with c_ins1:
                with st.container(border=True):
                    is_admin_flag = (prof.get("role") == "admin")
                    role_badge = "🛡️ Administrator" if is_admin_flag else "👤 Pengguna (User)"
                    email_val = prof.get("email") or "-"
                    inst_val = prof.get("institution") or "Tidak Disebutkan"
                    stat_val = (prof.get("status") or "active").lower()
                    badge_c = "#10b981" if stat_val == "active" else ("#f59e0b" if stat_val == "pending" else "#ef4444")
                    badge_lbl = "🟢 Aktif (Disetujui)" if stat_val == "active" else ("🟡 Menunggu Persetujuan (Pending)" if stat_val == "pending" else "🔴 Dinonaktifkan (Disabled)")
                    
                    st.markdown(f"#### {prof.get('full_name') or selected_user_ins}")
                    st.markdown(f"**Username:** `{selected_user_ins}`")
                    st.markdown(f"**Hak Akses:** `{role_badge}`")
                    st.markdown(f"**Status Akun:** <span style='background:{badge_c}18;color:{badge_c};border:1px solid {badge_c}40;padding:2px 8px;border-radius:6px;font-weight:700;'>{badge_lbl}</span>", unsafe_allow_html=True)
                    st.markdown(f"**Email:** `{email_val}`")
                    st.markdown(f"**Instansi:** {inst_val}")
                    st.markdown(f"**Nomor Telepon:** {prof.get('phone_number') or '-'}")
                    st.markdown(f"**Kota/Domisili:** {prof.get('city') or '-'}")
                    st.markdown(f"**Tanggal Mendaftar:** {prof.get('created_at') or '-'}")
            with c_ins2:
                with st.container(border=True):
                    st.markdown("##### 📜 Riwayat Analisis Pengguna")
                    all_preds = get_all_predictions()
                    user_preds = all_preds[all_preds["username"] == selected_user_ins] if not all_preds.empty and "username" in all_preds.columns else pd.DataFrame()
                    if not user_preds.empty:
                        st.caption(f"Pengguna ini telah melakukan **{len(user_preds)}** kali analisis prediksi finansial:")
                        cols_show = [c for c in ["ticker", "company", "year", "z_cls", "mda_cls", "timestamp"] if c in user_preds.columns]
                        st.dataframe(user_preds[cols_show].tail(10), use_container_width=True, hide_index=True)
                    else:
                        st.info("Pengguna ini belum pernah menyimpan riwayat analisis emiten.")

    # TAB 2: Edit Data Pengguna
    with tab_edit:
        st.markdown("##### ✏️ Perbarui Identitas dan Data Pengguna Terdaftar")
        if user_list:
            selected_user_edit = st.selectbox(
                "Pilih akun pengguna yang ingin diubah datanya:",
                user_list,
                key=f"{prefix}_edit_user_sel",
                format_func=lambda u: f"{u} — {df_users.loc[df_users['username'] == u, 'full_name'].values[0] or u} [{df_users.loc[df_users['username'] == u, 'role'].values[0].upper() if 'role' in df_users.columns and len(df_users.loc[df_users['username'] == u, 'role'].values) > 0 else 'USER'}]",
            )
            cur_prof = get_user_profile(selected_user_edit) or {}
            cur_role = (cur_prof.get("role") or "user").lower()
            is_superadmin = (selected_user_edit.lower() == "admin")
            
            with st.form(f"{prefix}_edit_user_form"):
                if is_superadmin:
                    st.info("Akun 'admin' adalah Administrator Utama sistem. Peran dilindungi dan tidak dapat diubah.")
                    e_role = "admin"
                else:
                    role_options = ["user", "admin"]
                    role_idx = 1 if cur_role == "admin" else 0
                    e_role = st.selectbox(
                        "Hak Akses / Peran (Role)",
                        role_options,
                        index=role_idx,
                        format_func=lambda r: "👤 Pengguna Biasa (User)" if r == "user" else "🛡️ Administrator (Admin Sistem)",
                    )

                e_name = st.text_input("Nama Lengkap", value=cur_prof.get("full_name", ""))
                e_mail = st.text_input("Alamat Email (@gmail atau Instansi)", value=cur_prof.get("email", ""))
                e_inst = st.text_input("Instansi / Lembaga / Perusahaan", value=cur_prof.get("institution", ""))
                e_phone = st.text_input("Nomor Telepon (Opsional)", value=cur_prof.get("phone_number", ""))
                
                submit_edit = st.form_submit_button("💾 Simpan Perubahan Data", type="primary", use_container_width=True)
                if submit_edit:
                    if not e_name.strip():
                        st.error("Nama lengkap tidak boleh kosong.")
                    else:
                        is_val, err_msg, det_inst = validate_registration_data(
                            e_name.strip(),
                            e_mail.strip(),
                            "Password123",
                            allow_admin=(e_role == "admin" or is_superadmin)
                        )
                        if not is_val:
                            st.error(f"Alamat email tidak valid: {err_msg}")
                        else:
                            final_inst = e_inst.strip() if e_inst.strip() else det_inst
                            ok, msg = update_user_credentials(
                                current_username=selected_user_edit,
                                new_full_name=e_name.strip(),
                                new_email=e_mail.strip(),
                                new_institution=final_inst,
                                new_phone_number=e_phone.strip(),
                            )
                            if ok:
                                if not is_superadmin and e_role != cur_role:
                                    update_user_role(selected_user_edit, e_role)
                                st.session_state["user_mgmt_flash_success"] = f"✅ Data pengguna '{selected_user_edit}' berhasil diperbarui!"
                                st.rerun()
                            else:
                                st.error(f"Gagal memperbarui data: {msg}")

    # TAB 3: Reset Kata Sandi
    with tab_pwd:
        st.markdown("##### 🔑 Reset Kata Sandi Akun Pengguna")
        st.caption("Jika pengguna lupa kata sandi atau meminta pemulihan akun, Administrator dapat menetapkan kata sandi baru yang aman.")
        if user_list:
            selected_user_pwd = st.selectbox(
                "Pilih akun pengguna yang ingin direset sandinya:",
                user_list,
                key=f"{prefix}_pwd_user_sel",
                format_func=lambda u: f"{u} — {df_users.loc[df_users['username'] == u, 'full_name'].values[0] or u} ({df_users.loc[df_users['username'] == u, 'email'].values[0] or 'No Email'})",
            )
            with st.form(f"{prefix}_reset_pwd_form"):
                new_reset_pwd = st.text_input("Kata Sandi Baru", type="password", placeholder="Minimal 6 karakter...", help="Gunakan kombinasi yang aman.")
                confirm_reset_pwd = st.text_input("Konfirmasi Kata Sandi Baru", type="password", placeholder="Ulangi kata sandi baru...")
                
                submit_pwd = st.form_submit_button("🔑 Terapkan Kata Sandi Baru", type="primary", use_container_width=True)
                if submit_pwd:
                    if not new_reset_pwd or len(new_reset_pwd.strip()) < 6:
                        st.error("Kata sandi baru minimal 6 karakter.")
                    elif new_reset_pwd.strip() != confirm_reset_pwd.strip():
                        st.error("Konfirmasi kata sandi tidak cocok. Harap periksa kembali.")
                    else:
                        ok, msg = admin_reset_user_password(selected_user_pwd, new_reset_pwd.strip())
                        if ok:
                            st.session_state["user_mgmt_flash_success"] = f"✅ Kata sandi untuk akun '{selected_user_pwd}' berhasil diperbarui!"
                            st.rerun()
                        else:
                            st.error(f"Gagal mereset kata sandi: {msg}")

    # TAB 4: Tambah Akun Manual oleh Admin
    with tab_add:
        st.markdown("##### ➕ Daftarkan Akun Pengguna / Administrator Baru")
        st.caption("Admin dapat mendaftarkan akun baru secara langsung (Pengguna Biasa atau Administrator). Wajib menggunakan email valid (@gmail atau instansi) dan sandi minimal 6 karakter.")
        if "user_mgmt_newly_created" in st.session_state:
            created_u = st.session_state.pop("user_mgmt_newly_created")
            st.success(f"🎉 **Sukses!** Akun **'{created_u}'** berhasil didaftarkan dan langsung tersimpan dalam database sistem! Anda dapat melihatnya pada tabel daftar akun di atas.")
        with st.form(f"{prefix}_add_user_form"):
            col_add_role, col_add_status = st.columns(2)
            with col_add_role:
                new_reg_role = st.selectbox(
                    "Hak Akses / Peran (Role)",
                    ["user", "admin"],
                    format_func=lambda r: "👤 Pengguna Biasa (User)" if r == "user" else "🛡️ Administrator (Admin Sistem)",
                    key=f"{prefix}_add_role_sel"
                )
            with col_add_status:
                new_reg_status = st.selectbox(
                    "Status Awal Akun",
                    ["active", "pending", "disabled"],
                    format_func=lambda s: "🟢 Langsung Aktif (Dapat Login)" if s == "active" else ("🟡 Menunggu Persetujuan (Pending)" if s == "pending" else "🔴 Dinonaktifkan (Disabled)"),
                    key=f"{prefix}_add_status_sel"
                )
            new_reg_name = st.text_input("Nama Lengkap", placeholder="Contoh: Sarah Wijaya atau Admin Keuangan")
            new_reg_email = st.text_input("Alamat Email (@gmail atau Instansi)", placeholder="sarah@gmail.com atau admin@ugm.ac.id")
            new_reg_pwd = st.text_input("Kata Sandi (Min. 6 Karakter)", type="password", placeholder="Masukkan kata sandi yang aman")
            new_reg_inst = st.text_input("Nama Instansi / Lembaga (Opsional)", placeholder="Contoh: Universitas Gadjah Mada / Kantor Pusat")

            submit_add = st.form_submit_button("➕ Daftarkan Akun Baru", type="primary", use_container_width=True)
            if submit_add:
                is_val, err_msg, detected_inst = validate_registration_data(
                    new_reg_name,
                    new_reg_email,
                    new_reg_pwd,
                    allow_admin=(new_reg_role == "admin")
                )
                if not is_val:
                    st.error(f"Validasi Gagal: {err_msg}")
                else:
                    final_inst = new_reg_inst.strip() if new_reg_inst.strip() else detected_inst
                    clean_u = derive_username(new_reg_name, new_reg_email, allow_admin=(new_reg_role == "admin"))
                    res = add_new_user(
                        username=clean_u,
                        password=new_reg_pwd.strip(),
                        role=new_reg_role,
                        email=new_reg_email.strip(),
                        full_name=new_reg_name.strip(),
                        institution=final_inst,
                        status=new_reg_status,
                    )
                    if res.success:
                        role_label = "Administrator" if new_reg_role == "admin" else "Pengguna"
                        succ_msg = f"🎉 Akun {role_label} '{clean_u}' ({new_reg_email.strip()}) berhasil didaftarkan dan langsung tersimpan dalam database!"
                        st.session_state["user_mgmt_flash_success"] = succ_msg
                        st.session_state["user_mgmt_newly_created"] = clean_u
                        st.session_state[f"{prefix}_filter_select"] = "Semua Akun Pengguna"
                        st.session_state[f"{prefix}_search_input"] = ""
                        try:
                            st.toast(succ_msg, icon="🎉")
                        except Exception:
                            pass
                        st.rerun()
                    else:
                        st.error(f"Gagal mendaftarkan akun: {res.message}")

    # TAB 5: Hapus Akun Pengguna
    with tab_del:
        st.markdown("##### 🗑️ Hapus Akun Pengguna")
        st.caption("Menghapus akun pengguna dari sistem. Akun superadmin 'admin' dilindungi dan tidak dapat dihapus.")
        if non_admin_list:
            del_target = st.selectbox(
                "Pilih akun pengguna yang ingin dihapus:",
                non_admin_list,
                key=f"{prefix}_del_user_sel",
                format_func=lambda u: f"{u} — {df_users.loc[df_users['username'] == u, 'full_name'].values[0] or u} ({df_users.loc[df_users['username'] == u, 'email'].values[0] or 'No Email'})",
            )
            st.warning(f"⚠️ Perhatian: Anda akan menghapus akun **'{del_target}'** secara permanen dari basis data.")
            confirm_del = st.checkbox(f"Saya yakin ingin menghapus akun '{del_target}'", key=f"{prefix}_confirm_del_box")
            if st.button("💥 Hapus Akun Terpilih", type="primary", disabled=not confirm_del, key=f"{prefix}_btn_exec_del"):
                ok, msg = delete_user_by_username(del_target)
                if ok:
                    st.session_state["user_mgmt_flash_success"] = f"✅ {msg}"
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.info("Tidak ada akun pengguna lain yang dapat dihapus.")


# ============================================================
# AREA UTAMA APLIKASI
# ============================================================

with content_col:
    # -------------------------------------------------------------
    # Deteksi Navigasi Menu & Reset Scroll ke Puncak Halaman (Top View)
    # -------------------------------------------------------------
    cur_p = st.session_state.page
    prev_p = st.session_state.get("_prev_page_seen", None)
    if prev_p != cur_p:
        st.session_state.menu_scroll_top = True
    st.session_state._prev_page_seen = cur_p

    should_scroll_to_top = bool(st.session_state.get("menu_scroll_top", False))
    st.session_state.menu_scroll_top = False
    scroll_flag_val = "1" if should_scroll_to_top else "0"

    # Jangkar puncak tampilan (Top Anchor) untuk scroll otomatis
    st.markdown('<div id="vault-view-top-anchor" style="position:relative;top:0;height:0;margin:0;padding:0;visibility:hidden;pointer-events:none;"></div>', unsafe_allow_html=True)

    # Engine A: Iframe Scroll Manager & Persistent Click Interceptor via components.html
    scroll_component_template = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    html, body { margin:0; padding:0; height:0; width:0; overflow:hidden; }
</style>
</head>
<body>
<script>
(function() {
    var shouldScroll = __SHOULD_SCROLL__;
    var win = window.parent || window;
    if (!win) return;
    var doc = win.document;
    if (!doc) return;

    function resetAllScrolls() {
        try {
            if ('scrollRestoration' in win.history) {
                win.history.scrollRestoration = 'manual';
            }
        } catch(e) {}

        try { win.scrollTo({ top: 0, left: 0, behavior: 'instant' }); } catch(e) { try { win.scrollTo(0, 0); } catch(e) {} }
        if (doc.documentElement) { doc.documentElement.scrollTop = 0; }
        if (doc.body) { doc.body.scrollTop = 0; }

        var selectors = [
            'section[data-testid="stMain"]',
            'section.main',
            '[data-testid="stAppViewContainer"]',
            '.stAppViewContainer',
            '.main',
            '[data-testid="stMainBlockContainer"]',
            '.stMainBlockContainer',
            '.block-container',
            '#root',
            'div[data-testid="stVerticalBlock"]',
            'div[data-testid="column"]:has(.sidebar-vault-container) ~ div[data-testid="column"]',
            'div[data-testid="stColumn"]:has(.sidebar-vault-container) ~ div[data-testid="stColumn"]'
        ];
        for (var i = 0; i < selectors.length; i++) {
            try {
                var els = doc.querySelectorAll(selectors[i]);
                for (var j = 0; j < els.length; j++) {
                    if (els[j]) { els[j].scrollTop = 0; }
                }
            } catch(e) {}
        }

        try {
            var all = doc.querySelectorAll('*');
            for (var k = 0; k < all.length; k++) {
                var el = all[k];
                if (el.scrollTop > 0) {
                    var isSidebar = false;
                    try {
                        if (el.classList && el.classList.contains('sidebar-vault-container')) isSidebar = true;
                        if (el.closest && el.closest('[data-testid="column"]:has(.sidebar-vault-container)')) isSidebar = true;
                        if (el.closest && el.closest('div[data-testid="stRadio"]')) isSidebar = true;
                    } catch(e) {}
                    if (!isSidebar) {
                        el.scrollTop = 0;
                    }
                }
            }
        } catch(e) {}

        try {
            var anchor = doc.getElementById('vault-view-top-anchor') 
                      || doc.querySelector('.vault-canvas-header')
                      || doc.querySelector('h1.header-main-h1');
            if (anchor && anchor.scrollIntoView) {
                anchor.scrollIntoView({ behavior: 'instant', block: 'start', inline: 'nearest' });
            }
        } catch(e) {}
    }

    var hasStorageFlag = false;
    try {
        if (win.sessionStorage && win.sessionStorage.getItem('distress_force_top_scroll') === '1') {
            hasStorageFlag = true;
            win.sessionStorage.removeItem('distress_force_top_scroll');
        }
    } catch(e) {}

    if (shouldScroll || hasStorageFlag) {
        resetAllScrolls();
        if (win.requestAnimationFrame) { win.requestAnimationFrame(resetAllScrolls); }
        setTimeout(resetAllScrolls, 25);
        setTimeout(resetAllScrolls, 60);
        setTimeout(resetAllScrolls, 120);
        setTimeout(resetAllScrolls, 250);
        setTimeout(resetAllScrolls, 500);
        setTimeout(resetAllScrolls, 900);
    }

    try {
        // HANYA memantau interaksi klik pada Menu Navigasi Sidebar (custom_page_menu)
        // Fitur lain seperti Tab, tombol form, kalkulasi, dan input radio di dalam halaman TIDAK akan menggulir ke atas
        var isSidebarMenuRadio = function(target) {
            if (!target || !target.closest) return false;
            // 1. Cek langsung wrapper key radio menu navigasi sidebar
            if (target.closest('.st-key-custom_page_menu')) return true;
            // 2. Cek apakah elemen radio berada di dalam kolom sidebar
            var radio = target.closest('div[data-testid="stRadio"]');
            if (radio) {
                var col = radio.closest('div[data-testid="column"], div[data-testid="stColumn"]');
                if (col && col.querySelector && Boolean(col.querySelector('.sidebar-vault-container') || col.querySelector('.sidebar-logo-header') || col.querySelector('.sidebar-section-label'))) {
                    return true;
                }
            }
            return false;
        };

        var closeMobileNav = function() {
            try {
                if (doc.body) doc.body.classList.remove('mobile-nav-open');
                if (win.document && win.document.body) win.document.body.classList.remove('mobile-nav-open');
            } catch(err) {}
        };

        var toggleMobileNav = function() {
            try {
                var b = doc.body || (win.document && win.document.body);
                if (b) b.classList.toggle('mobile-nav-open');
            } catch(err) {}
        };

        var onGlobalClick = function(e) {
            var t = e.target;
            if (!t) return;

            // 1. Cek tombol hamburger mobile
            if (t.closest && t.closest('.mobile-hamburger-btn')) {
                try { e.preventDefault(); } catch(err) {}
                toggleMobileNav();
                return;
            }

            // 2. Cek backdrop atau tombol close drawer
            if (t.closest && (t.closest('.mobile-drawer-backdrop') || t.closest('.mobile-drawer-close-btn'))) {
                try { e.preventDefault(); } catch(err) {}
                closeMobileNav();
                return;
            }

            // 3. Cek klik pada item menu radio sidebar
            if (isSidebarMenuRadio(t)) {
                closeMobileNav();
                try {
                    if (win.sessionStorage) win.sessionStorage.setItem('distress_force_top_scroll', '1');
                } catch(err) {}
                resetAllScrolls();
                setTimeout(resetAllScrolls, 20);
                setTimeout(resetAllScrolls, 50);
            }
        };

        // Lepas listener lama di window / document
        if (win.__distressNavScrollHandler) {
            doc.removeEventListener('click', win.__distressNavScrollHandler, true);
            doc.removeEventListener('pointerdown', win.__distressNavScrollHandler, true);
        }
        win.__distressNavScrollHandler = onGlobalClick;
        doc.addEventListener('click', onGlobalClick, true);

        // Listener adaptif saat ukuran layar atau orientasi device berganti
        var onDeviceResize = function() {
            try {
                var w = win.innerWidth || (doc.documentElement && doc.documentElement.clientWidth) || 0;
                if (w > 991) {
                    closeMobileNav();
                }
            } catch(err) {}
        };
        if (win.__distressResizeHandler) {
            win.removeEventListener('resize', win.__distressResizeHandler);
            win.removeEventListener('orientationchange', win.__distressResizeHandler);
        }
        win.__distressResizeHandler = onDeviceResize;
        win.addEventListener('resize', onDeviceResize);
        win.addEventListener('orientationchange', onDeviceResize);
    } catch(e) {}

    try {
        if (!win.__distressLiveClockTimer) {
            var updateClock = function() {
                var d = new Date();
                var days = ['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];
                var months = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];
                var day = days[d.getDay()];
                var date = d.getDate();
                var mo = months[d.getMonth()];
                var yr = d.getFullYear();
                var h = String(d.getHours()).padStart(2, '0');
                var m = String(d.getMinutes()).padStart(2, '0');
                var s = String(d.getSeconds()).padStart(2, '0');
                var dEls = doc.querySelectorAll('.clock-date-live');
                var tEls = doc.querySelectorAll('.clock-time-live');
                for (var i = 0; i < dEls.length; i++) { dEls[i].textContent = day + ', ' + date + ' ' + mo + ' ' + yr; }
                for (var j = 0; j < tEls.length; j++) { tEls[j].textContent = h + ':' + m + ':' + s + ' WIB'; }
            };
            win.__distressLiveClockTimer = win.setInterval(updateClock, 1000);
        }
    } catch(e) {}
})();
</script>
</body>
</html>
"""
    scroll_component_code = scroll_component_template.replace("__SHOULD_SCROLL__", "true" if should_scroll_to_top else "false")
    components.html(scroll_component_code, height=0)

    db_type_label = get_db_info()["type"]
    ticker_display = html.escape(str(st.session_state.ticker).strip().upper()) if st.session_state.ticker else ""
    year_display = html.escape(str(st.session_state.year)) if st.session_state.year else ""
    comp_display = html.escape(str(st.session_state.company).strip()) if st.session_state.company else ""
    is_analyzed = bool(st.session_state.get("has_analyzed", False) and ticker_display)

    if page in ("Pengaturan Profil", "Pengaturan Akun", "Profil", "Profile"):
        header_sub_display = """
        <span class="header-platform-tag">SISTEM AKUN</span>
        <span class="header-sub-sep">•</span>
        <span class="header-sub-desc">Pengaturan Profil &amp; Kredensial Akses Pengguna</span>
        <span class="header-status-pill standby-pill">🔒 Akun Terotentikasi</span>
        """
    elif is_analyzed:
        comp_elem = f'<span class="header-company-name">— {comp_display}</span>' if comp_display else ""
        header_sub_display = f"""
        <span class="header-platform-tag" style="background:rgba(16,185,129,0.15); color:#10b981; border-color:rgba(16,185,129,0.35);">EMITEN AKTIF</span>
        <span class="header-sub-sep">•</span>
        <span class="header-emiten-pill">
            <span class="emiten-pill-ticker">{ticker_display}</span>
            <span class="emiten-pill-year">({year_display})</span>
        </span>
        {comp_elem}
        <span class="header-status-pill active-pill">🟢 Teranalisis Multi-Model</span>
        """
    else:
        header_sub_display = """
        <span class="header-platform-tag">BEI RISK INTELLIGENCE</span>
        <span class="header-sub-sep">•</span>
        <span class="header-sub-desc">Multi-Model Corporate Financial Distress Analytics Platform</span>
        <span class="header-status-pill standby-pill">⚪ Siaga Analisis</span>
        """

    # -------------------------------------------------------------
    # Kalkulasi Waktu Indonesia Barat (WIB / UTC+7) Real-Time
    # -------------------------------------------------------------
    DAYS_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    MONTHS_ID = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    wib_tz = datetime.timezone(datetime.timedelta(hours=7))
    now_wib = now_utc.astimezone(wib_tz)

    header_date_str = f"{DAYS_ID[now_wib.weekday()]}, {now_wib.day} {MONTHS_ID[now_wib.month]} {now_wib.year}"
    header_time_str = f"{now_wib.strftime('%H:%M:%S')} WIB"

    # Widget Header Datetime Real-Time (Hari, Tanggal, Jam Detik WIB) dengan Client-Side Pulse & Live Ticking
    header_clock_widget = f"""
    <div class="header-datetime-box" title="Waktu Sistem dan Pasar Modal Real-Time (WIB)">
        <div class="clock-live-indicator">
            <span class="clock-pulse-dot"></span>
            <span>LIVE</span>
        </div>
        <div class="clock-content">
            <span class="clock-date clock-date-live">{header_date_str}</span>
            <span class="clock-sep">•</span>
            <span class="clock-time clock-time-live">{header_time_str}</span>
        </div>
    </div>
    """

    # Engine B: Direct Visible-to-DOM (1x1px, opacity: 0.001) Cache-Busted Inline Trigger
    ts_now = int(time.time() * 1000)
    inline_scroll_js = (
        "var fn=function(){"
        "try{if('scrollRestoration' in history){history.scrollRestoration='manual';}}catch(e){}"
        "try{window.scrollTo({top:0,left:0,behavior:'instant'});}catch(e){try{window.scrollTo(0,0);}catch(e){}}"
        "if(document.documentElement){document.documentElement.scrollTop=0;}"
        "if(document.body){document.body.scrollTop=0;}"
        "var s=['section[data-testid=\"stMain\"]','section.main','[data-testid=\"stAppViewContainer\"]','.stAppViewContainer','.main','[data-testid=\"stMainBlockContainer\"]','.stMainBlockContainer','.block-container','#root'];"
        "for(var i=0;i<s.length;i++){try{var els=document.querySelectorAll(s[i]);for(var j=0;j<els.length;j++){if(els[j]){els[j].scrollTop=0;}}}catch(e){}}"
        "try{var a=document.getElementById('vault-view-top-anchor')||document.querySelector('.vault-canvas-header')||document.querySelector('h1.header-main-h1');if(a&&a.scrollIntoView){a.scrollIntoView({behavior:'instant',block:'start',inline:'nearest'});}}catch(e){}"
        "};"
        "var shouldRun=(__SCROLL_FLAG__===1)||(sessionStorage.getItem('distress_force_top_scroll')==='1');"
        "try{sessionStorage.removeItem('distress_force_top_scroll');}catch(e){}"
        "if(shouldRun){fn();if(window.requestAnimationFrame){window.requestAnimationFrame(fn);}setTimeout(fn,25);setTimeout(fn,75);setTimeout(fn,160);setTimeout(fn,320);setTimeout(fn,600);}"
    ).replace("__SCROLL_FLAG__", scroll_flag_val)

    scroll_trigger_img = (
        f'<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7?t={ts_now}" '
        f'style="position:fixed;top:0;left:0;width:1px;height:1px;opacity:0.001;pointer-events:none;z-index:-9999;" '
        f'onload="{inline_scroll_js}" onerror="{inline_scroll_js}" />'
    )

    mobile_topbar_html = f"""
    <div class="mobile-top-bar" id="mobileTopBar">
        <button type="button" class="mobile-hamburger-btn" onclick="(window.parent||window).document.body.classList.toggle('mobile-nav-open');" title="Buka Menu Navigasi">
            <span class="hamburger-icon">☰</span>
            <span class="hamburger-text">Menu</span>
        </button>
        <div class="mobile-brand-pill">
            <div class="mobile-brand-logo">⚡</div>
            <div class="mobile-brand-title">Distress Prediction</div>
        </div>
        <div class="mobile-page-indicator">
            <span class="mobile-page-badge">{page}</span>
        </div>
    </div>
    <div class="mobile-drawer-backdrop" id="mobileDrawerBackdrop" onclick="(window.parent||window).document.body.classList.remove('mobile-nav-open');"></div>
    """

    header_html = f"""
    {mobile_topbar_html}
    <div class="vault-canvas-header">
        <div class="header-title-column">
            <h1 class="header-main-h1">{page}</h1>
            <div class="header-sub-text">{header_sub_display}</div>
        </div>
        {header_clock_widget}
    </div>
    {scroll_trigger_img}
    """

    # Header Utama Responsif dengan Tombol Hamburger jika Sidebar Tersembunyi (Mobile/Tablet/Desktop Collapsed)
    if not st.session_state.sidebar_visible:
        h_btn_col, h_text_col = st.columns([0.055, 0.945], gap="small")
        with h_btn_col:
            if st.button("☰", key="btn_hamburger_main", help="Buka Menu Navigasi (Expand Sidebar)"):
                st.session_state.sidebar_visible = True
                st.rerun()
        with h_text_col:
            render_clean_html(header_html)
    else:
        render_clean_html(header_html)

    # Pengalihan Terpadu: Jika ada pemicu modal profil lama, arahkan langsung ke halaman khusus Pengaturan Profil
    if st.session_state.get("active_account_modal") in ("edit_account", "complete_profile"):
        st.session_state.active_account_modal = None
        set_page("Pengaturan Profil")
        st.rerun()

    # ========================================================
    # 1. HALAMAN KHUSUS USER: DASHBOARD DAN ANALISIS (RINGKAS)
    # ========================================================
    if page == "__legacy_dashboard_analisis__":
        section_title("Dashboard dan Input Data Keuangan", "Masukkan data perusahaan dan laporan keuangan untuk melakukan analisis prediksi")
        
        allow_analysis = config.get("allow_user_analysis", True)
        if not allow_analysis and st.session_state.role != "admin":
            st.warning("⚠️ **Mode Pemeliharaan:** Administrator sedang memperbarui parameter model. Tombol eksekusi analisis dinonaktifkan sementara.")
            st.stop()

        st.caption(
            f"🔒 *Parameter Resmi Aktif (Ditetapkan Admin):* Altman Cut-off ({config['altman_thresholds']['distress']:.2f}) | "
            f"MDA Cut-off ({config['mda_threshold']:.4f}) | XGBoost Cut-off ({config['xgb_threshold']:.2f})"
        )
        
        # 1. Identitas Perusahaan
        with st.container(border=True):
            col_id_head, col_id_rst = st.columns([3.0, 1.2])
            with col_id_head:
                st.markdown(
                    """
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                        <div style="width:38px;height:38px;border-radius:12px;background:rgba(99,102,241,0.18);color:#818cf8;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(99,102,241,0.3);box-shadow:0 0 12px rgba(99,102,241,0.2);">🏢</div>
                        <div>
                            <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">1. Identitas Perusahaan</div>
                            <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Profil emiten dan periode laporan keuangan yang dianalisis</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_id_rst:
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                if st.button("🔄 Reset / Kosongkan Form", help="Mengosongkan form ke nilai awal untuk menganalisis emiten baru", use_container_width=True, key="btn_reset_user_form"):
                    st.session_state.company = ""
                    st.session_state.ticker = ""
                    st.session_state.sector = ""
                    st.session_state.financials = {}
                    st.session_state.ratios = {"X1": 0.0, "X2": 0.0, "X3": 0.0, "X4": 0.0, "X5": 0.0}
                    st.session_state.has_analyzed = False
                    st.session_state.analysis_date = datetime.date.today().strftime("%Y-%m-%d")
                    for item in VARIABLE_SCHEMA:
                        st.session_state.pop(f"user_input_{item['key']}", None)
                        st.session_state.pop(f"manual_{item['key']}", None)
                    st.session_state.pop("saved_extraction_rows", None)
                    st.session_state.pop("saved_extraction_meta", None)
                    st.toast("Formulir masukan berhasil dikosongkan!", icon="🔄")
                    st.rerun()

            c1, c2 = st.columns(2)
            with c1:
                st.session_state.company = st.text_input("Nama Perusahaan", value=st.session_state.company, placeholder="Contoh: PT Bank Central Asia Tbk")
                st.session_state.ticker = st.text_input("Kode Perusahaan (Ticker)", value=st.session_state.ticker, placeholder="Contoh: BBCA").upper()
                st.session_state.sector = st.text_input("Sektor Industri", value=st.session_state.sector)
            with c2:
                st.session_state.year = st.number_input("Tahun Analisis", 2000, 2100, int(st.session_state.year) if str(st.session_state.year).isdigit() else 2024)
                
                # Fitur Pemilih Tanggal Gelembung Kalender Interaktif (Calendar Bubble Picker)
                raw_d_leg = st.session_state.get("analysis_date", "")
                curr_date_leg = datetime.date.today()
                if isinstance(raw_d_leg, datetime.date):
                    curr_date_leg = raw_d_leg
                elif isinstance(raw_d_leg, str) and raw_d_leg.strip():
                    try:
                        curr_date_leg = datetime.datetime.strptime(raw_d_leg.strip(), "%Y-%m-%d").date()
                    except Exception:
                        try:
                            curr_date_leg = datetime.date.fromisoformat(raw_d_leg.strip())
                        except Exception:
                            curr_date_leg = datetime.date.today()

                col_date_pick_leg, col_date_today_leg = st.columns([2.5, 1.2])
                with col_date_pick_leg:
                    picked_date_leg = st.date_input(
                        "Tanggal Analisis",
                        value=curr_date_leg,
                        min_value=datetime.date(2000, 1, 1),
                        max_value=datetime.date(2100, 12, 31),
                        format="YYYY-MM-DD",
                        help="Klik kotak tanggal untuk membuka gelembung kalender interaktif dan memilih tanggal analisis",
                        key="picker_analysis_date_legacy"
                    )
                    if picked_date_leg:
                        st.session_state.analysis_date = picked_date_leg.strftime("%Y-%m-%d") if hasattr(picked_date_leg, "strftime") else str(picked_date_leg)
                with col_date_today_leg:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("📅 Hari Ini", key="btn_set_today_analysis_date_legacy", use_container_width=True, help="Setel tanggal analisis langsung ke hari ini"):
                        st.session_state.analysis_date = datetime.date.today().strftime("%Y-%m-%d")
                        st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # 2. Input Laporan Keuangan (Manual / CSV / PDF)
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(20,184,166,0.18);color:#2dd4bf;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(20,184,166,0.3);box-shadow:0 0 12px rgba(20,184,166,0.2);">📄</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">2. Sumber Data dan Impor Laporan Keuangan</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Pilih metode masukan data via input manual, unggah file CSV, atau dokumen PDF BEI/IDX</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("📖 Lihat Kamus Variabel dan Format Laporan Keuangan BEI (IDX)", expanded=False):
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Kode": item["code"],
                            "Nama Variabel": item["label"],
                            "Kolom Standar": item["csv"],
                            "Digunakan untuk": item["used_by"],
                        }
                        for item in VARIABLE_SCHEMA
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                col_tpl1, col_tpl2 = st.columns(2)
                with col_tpl1:
                    st.download_button(
                        "📥 Unduh Format Template CSV Standar (.csv)",
                        get_sample_template_csv_bytes(),
                        file_name="template_laporan_keuangan_distress.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with col_tpl2:
                    st.download_button(
                        "📥 Unduh Format Template Excel Standar (.xlsx)",
                        get_sample_template_excel_bytes(),
                        file_name="template_laporan_keuangan_distress.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

            mode = st.radio("Metode Masukan Data", ["Input Manual", "🌐 Tarik Otomatis API Bursa (IDX)", "📊 Upload Excel (BEI/IDX)", "Upload CSV", "Upload PDF"], horizontal=True)
            st.session_state.source_mode = mode

            fin0 = st.session_state.get("financials", {})

            if mode == "🌐 Tarik Otomatis API Bursa (IDX)":
                st.markdown("##### ⚡ Tarik Laporan Keuangan Otomatis via API IDX / Yahoo Finance")
                st.caption("Sistem akan menghubungi API pasar modal, mengambil laporan keuangan tahunan, dan mengisi seluruh variabel proyek secara otomatis.")
                
                c_api_t, c_api_yr, c_api_btn = st.columns([2, 1.2, 1.5])
                with c_api_t:
                    input_ticker_val = st.text_input("Kode Saham (Ticker)", value=st.session_state.ticker or "ICBP", placeholder="Contoh: ICBP, INDF, ASII, UNVR, KLBF, SMGR, TLKM", key="dash_api_tick_input").upper()
                with c_api_yr:
                    api_yr_mode = st.selectbox("Pilihan Periode", ["Tahun Terbaru (Latest)", "2025", "2024", "2023", "2022", "2021", "2020"], key="dash_api_yr_mode")
                with c_api_btn:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    btn_dash_pull = st.button("🚀 Tarik Data API", type="primary", use_container_width=True, key="btn_dash_pull_api")

                dash_picked = render_emiten_shortcuts("dash_api")
                if dash_picked:
                    input_ticker_val = dash_picked
                    st.session_state.ticker = dash_picked
                    btn_dash_pull = True

                if st.session_state.get("api_pull_success_msg"):
                    st.success(st.session_state["api_pull_success_msg"])
                    if st.session_state.get("api_pull_year_note"):
                        st.info(f"💡 {st.session_state['api_pull_year_note']}")
                    trace = st.session_state.get("api_pull_trace", [])
                    if trace:
                        with st.expander("🔍 Rincian Jejak Multi-Source Pipeline (Fallback Trace)", expanded=False):
                            for t_step in trace:
                                st.caption(f"• {t_step}")
                    if st.session_state.get("api_pull_is_financial"):
                        st.warning("⚠️ Perhatian: Emiten sektor perbankan/keuangan tidak memiliki pos Working Capital standar.")

                if btn_dash_pull and input_ticker_val:
                    user_target_year = int(api_yr_mode) if str(api_yr_mode).isdigit() else None
                    def _do_dash_api_pull():
                        return FinancialAPIClient.fetch_emiten_profile_and_financials(input_ticker_val, target_year=user_target_year)

                    try:
                        data_api = run_animated_loading_process(
                            task_name="Penarikan Data Live API Bursa",
                            target_info=f"Emiten {input_ticker_val} • Periode: {api_yr_mode}",
                            task_type="api",
                            execute_fn=_do_dash_api_pull,
                            success_title=f"Laporan Keuangan {input_ticker_val} Berhasil Ditarik!",
                            success_desc="Pos akun neraca, laba rugi, dan rasio keuangan telah sinkron.",
                        )
                        st.session_state.api_emiten_data = data_api
                        st.session_state.company = data_api["company"]
                        st.session_state.ticker = data_api["ticker"]
                        st.session_state.sector = data_api["sector"]

                        avail_yrs = data_api.get("years", [2024])
                        if user_target_year is not None:
                            chosen_yr = user_target_year
                        elif api_yr_mode == "Tahun Terbaru (Latest)":
                            chosen_yr = avail_yrs[0] if avail_yrs else 2024
                        else:
                            chosen_yr = int(api_yr_mode) if str(api_yr_mode).isdigit() else (avail_yrs[0] if avail_yrs else 2024)

                        st.session_state.year = int(chosen_yr)

                        fin_pulled = data_api["financials_by_year"].get(chosen_yr)
                        if not fin_pulled:
                            fin_pulled = next(iter(data_api["financials_by_year"].values()), {})
                        fin_pulled = dict(fin_pulled)
                        fin_pulled["report_year"] = int(chosen_yr)
                        fin_pulled["ticker"] = st.session_state.ticker

                        # Pastikan beban bunga (interest_expense) selalu terisi dan tidak 0
                        if float(fin_pulled.get("interest_expense", 0.0) or 0.0) == 0.0:
                            t_u = str(st.session_state.ticker).upper()
                            m_e = MOCK_IDX_DATA.get(t_u, {})
                            m_f = m_e.get("financials_by_year", {}).get(int(chosen_yr), {}) or m_e.get("financials_by_year", {}).get(2024, {})
                            if m_f and float(m_f.get("interest_expense", 0.0) or 0.0) > 0:
                                fin_pulled["interest_expense"] = float(m_f["interest_expense"])
                            elif float(fin_pulled.get("total_debt", 0.0) or 0.0) > 0:
                                fin_pulled["interest_expense"] = float(fin_pulled["total_debt"]) * 0.058
                            elif float(fin_pulled.get("total_liabilities", 0.0) or 0.0) > 0:
                                fin_pulled["interest_expense"] = float(fin_pulled["total_liabilities"]) * 0.038

                        fin0.update(fin_pulled)
                        st.session_state.financials = fin0

                        for k, v in fin_pulled.items():
                            if v is not None:
                                str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                st.session_state[f"user_input_{k}"] = str_repr
                                st.session_state[f"manual_{k}"] = str_repr

                        # Khusus interest_expense: pastikan terisi di session_state string
                        ie_val = fin_pulled.get("interest_expense")
                        if ie_val is not None:
                            str_ie = f"{int(ie_val)}" if isinstance(ie_val, (int, float)) and float(ie_val).is_integer() else str(ie_val)
                            st.session_state["user_input_interest_expense"] = str_ie
                            st.session_state["manual_interest_expense"] = str_ie

                        st.session_state["manual_report_year"] = int(chosen_yr)
                        st.session_state["user_input_report_year"] = str(chosen_yr)
                        st.session_state["user_input_report_year_num"] = int(chosen_yr)
                        st.session_state["admin_manual_report_year_input"] = int(chosen_yr)
                        st.session_state["user_input_ticker"] = str(st.session_state.ticker).upper()

                        try:
                            set_ratios_from_financials(fin0)
                        except Exception:
                            pass

                        source_tag = data_api.get("source", "Multi-Source Engine")
                        st.session_state["api_pull_success_msg"] = f"✅ Laporan keuangan {data_api['company']} ({data_api['ticker']}) tahun {chosen_yr} berhasil ditarik via **{source_tag}**! 15 nilai akun di bawah telah terisi otomatis."
                        st.session_state["api_pull_trace"] = data_api.get("provider_trace", [])
                        st.session_state["api_pull_is_financial"] = bool(data_api.get("is_financial_sector"))
                        st.session_state["api_pull_year_note"] = data_api.get("year_fallback_note")
                        st.rerun()
                    except Exception as e:
                        render_api_error_feedback(e, input_ticker_val)

            elif mode == "📊 Upload Excel (BEI/IDX)":
                st.markdown("##### 📊 Impor Langsung File Excel Resmi BEI / IDX (.xlsx, .xls)")
                st.caption("Unggah file Excel laporan keuangan resmi yang diunduh langsung dari situs Bursa Efek Indonesia (idx.co.id). Sistem akan otomatis mengenali format XBRL/multi-sheet, mendeteksi emiten dan tahun, dan mengekstrak 15 variabel proyek secara cerdas.")

                uploaded_excel = st.file_uploader(
                    "Unggah file Excel Laporan Keuangan (.xlsx, .xls)",
                    type=["xlsx", "xls"],
                    key="excel_uploader_dashboard",
                    help="Mendukung file Excel resmi BEI/IDX (multi-sheet XBRL taksonomi) maupun file Excel tabular data emiten."
                )
                if uploaded_excel:
                    try:
                        if is_idx_xbrl_data(uploaded_excel):
                            detected_years = get_idx_document_years(uploaded_excel)
                            default_excel_year = detected_years[0] if detected_years else 2025
                            if str(st.session_state.year).isdigit() and int(st.session_state.year) in detected_years:
                                default_excel_year = int(st.session_state.year)

                            col_ex_y, col_ex_info = st.columns([1.8, 2.2])
                            with col_ex_y:
                                target_excel_year = st.radio(
                                    "Pilih Tahun Pelaporan Keuangan:",
                                    options=detected_years if detected_years else [2025, 2024],
                                    index=detected_years.index(default_excel_year) if default_excel_year in detected_years else 0,
                                    horizontal=True,
                                    key="excel_target_year_user",
                                )

                            excel_cache_key = f"{uploaded_excel.name}_{uploaded_excel.size}_{target_excel_year}"
                            if st.session_state.get("_last_parsed_excel_key_dash") != excel_cache_key:
                                def _do_extract_excel_dash():
                                    return extract_financial_values_from_idx_data(uploaded_excel, int(target_excel_year))

                                parsed_excel, excel_evidence, _ = run_animated_loading_process(
                                    task_name="Ekstraksi Laporan Keuangan Excel BEI/IDX",
                                    target_info=f"{uploaded_excel.name} (Tahun {target_excel_year})",
                                    task_type="excel",
                                    execute_fn=_do_extract_excel_dash,
                                    success_title="Ekstraksi Excel BEI/IDX Selesai!",
                                    success_desc=f"15 variabel proyek tahun {target_excel_year} berhasil diekstrak dan disinkronkan.",
                                )
                                st.session_state._last_parsed_excel_key_dash = excel_cache_key
                                st.session_state._cached_parsed_excel_dash = parsed_excel
                                st.session_state._cached_evidence_excel_dash = excel_evidence
                            else:
                                parsed_excel = st.session_state.get("_cached_parsed_excel_dash")
                                excel_evidence = st.session_state.get("_cached_evidence_excel_dash", {})

                            if parsed_excel:
                                if parsed_excel.get("ticker"):
                                    st.session_state.ticker = str(parsed_excel["ticker"]).strip().upper()
                                if parsed_excel.get("company"):
                                    st.session_state.company = str(parsed_excel["company"]).strip()
                                if parsed_excel.get("sector"):
                                    st.session_state.sector = str(parsed_excel["sector"]).strip()
                                if parsed_excel.get("report_year"):
                                    st.session_state.year = int(parsed_excel["report_year"])
                                fin0.update(parsed_excel)
                                st.session_state.financials = fin0

                                for k, v in parsed_excel.items():
                                    if v is not None:
                                        str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                        st.session_state[f"user_input_{k}"] = str_repr
                                        st.session_state[f"manual_{k}"] = str_repr

                                yr_ex_clean = int(parsed_excel.get("report_year", target_excel_year))
                                st.session_state["manual_report_year"] = yr_ex_clean
                                st.session_state["user_input_report_year"] = str(yr_ex_clean)
                                st.session_state["user_input_report_year_num"] = yr_ex_clean
                                st.session_state["admin_manual_report_year_input"] = yr_ex_clean
                                if parsed_excel.get("ticker"):
                                    st.session_state["user_input_ticker"] = str(parsed_excel["ticker"]).strip().upper()

                                with col_ex_info:
                                    t_show = st.session_state.ticker or "EMITEN"
                                    c_show = st.session_state.company or "Perusahaan Tercatat"
                                    s_show = st.session_state.sector or "Umum / General"
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 10px 14px; margin-top: 14px;">
                                            <div style="font-weight: 850; font-size: 15px; color: #38bdf8;">🏢 {t_show} — {c_show}</div>
                                            <div style="font-size: 12px; color: #94a3b8;">Sektor: {s_show} | Tahun Terpilih: <b>{target_excel_year}</b></div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                st.success(f"✅ Data Excel BEI/IDX {st.session_state.company} ({st.session_state.ticker}) tahun {target_excel_year} berhasil diekstrak! 15 variabel proyek terisi otomatis.")

                                with st.expander("🔍 Detail Hasil Ekstraksi & Perhitungan Otomatis dari Excel BEI/IDX", expanded=True):
                                    ev_rows = []
                                    for item in VARIABLE_SCHEMA:
                                        k = item["key"]
                                        val = fin0.get(k)
                                        ev = excel_evidence.get(k, {})
                                        val_str = format_display_value(k, val)
                                        ev_rows.append({
                                            "Kode": item["code"],
                                            "Nama Variabel": item["label"],
                                            "Nilai": val_str,
                                            "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                            "Lembar / Bagian Sumber": str(ev.get("halaman", "-")),
                                            "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "-")),
                                        })
                                    st.session_state["saved_extraction_rows"] = ev_rows
                                    st.session_state["saved_extraction_meta"] = {
                                        "source_type": "Excel (BEI/IDX)",
                                        "filename": uploaded_excel.name,
                                        "company": st.session_state.company,
                                        "ticker": st.session_state.ticker,
                                        "year": target_excel_year,
                                        "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                    }
                                    render_styled_dataframe(pd.DataFrame(ev_rows), is_light=is_light_theme())
                        else:
                            df_ex = read_excel_file(uploaded_excel)
                            if isinstance(df_ex, dict):
                                best_sheet = next(iter(df_ex.keys()))
                                df_ex = df_ex[best_sheet]
                            st.session_state["uploaded_df"] = df_ex
                            st.caption(f"📊 File Excel tabular memuat total **{len(df_ex)}** baris data emiten.")

                            if len(df_ex) > 1:
                                tab_ex_single, tab_ex_batch = st.tabs([
                                    "🏢 Analisis Tunggal (Pilih 1 Emiten)",
                                    "⚡ Skrining Massal Seluruh Baris (Batch Screening)",
                                ])
                            else:
                                tab_ex_single = st.container()
                                tab_ex_batch = None

                            with tab_ex_single:
                                st.dataframe(df_ex.head(8), use_container_width=True)
                                row_idx = 0
                                if len(df_ex) > 1:
                                    row_options = []
                                    for idx, r in df_ex.iterrows():
                                        tick = r.get("ticker", r.get("kode_saham", r.get("kode emiten", f"Baris {idx+1}")))
                                        yr = r.get("report_year", r.get("tahun", r.get("year", "")))
                                        comp = r.get("company", r.get("nama_perusahaan", ""))
                                        row_options.append((idx, f"Baris {idx + 1}: {tick} ({yr}) {comp}".strip()))
                                    selected_choice = st.selectbox(
                                        "Pilih baris emiten/tahun untuk diekstrak ke form:",
                                        options=[opt[0] for opt in row_options],
                                        format_func=lambda i: row_options[i][1],
                                        key="user_excel_row_select",
                                    )
                                    row_idx = selected_choice

                                parsed_ex, ex_evidence = extract_financial_values_from_df(df_ex, row_idx)
                                if parsed_ex:
                                    if parsed_ex.get("ticker"):
                                        st.session_state.ticker = str(parsed_ex["ticker"]).strip().upper()
                                    if parsed_ex.get("company"):
                                        st.session_state.company = str(parsed_ex["company"]).strip()
                                    if parsed_ex.get("report_year"):
                                        st.session_state.year = int(parsed_ex["report_year"])
                                    fin0.update(parsed_ex)
                                    st.session_state.financials = fin0
                                    for k, v in parsed_ex.items():
                                        if v is not None:
                                            str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                            st.session_state[f"user_input_{k}"] = str_repr
                                            st.session_state[f"manual_{k}"] = str_repr

                                    yr_tab_clean = int(parsed_ex.get("report_year", st.session_state.year))
                                    st.session_state["manual_report_year"] = yr_tab_clean
                                    st.session_state["user_input_report_year"] = str(yr_tab_clean)
                                    st.session_state["user_input_report_year_num"] = yr_tab_clean
                                    st.session_state["admin_manual_report_year_input"] = yr_tab_clean
                                    if parsed_ex.get("ticker"):
                                        st.session_state["user_input_ticker"] = str(parsed_ex["ticker"]).strip().upper()

                                    st.success("✅ Data Excel baris terpilih berhasil dimuat ke formulir!")

                                    with st.expander("🔍 Detail Pemetaan dan Perhitungan Otomatis dari Excel", expanded=False):
                                        ev_rows = []
                                        for item in VARIABLE_SCHEMA:
                                            k = item["key"]
                                            val = fin0.get(k)
                                            ev = ex_evidence.get(k, {})
                                            val_str = format_display_value(k, val)
                                            ev_rows.append({
                                                "Kode": item["code"],
                                                "Nama Variabel": item["label"],
                                                "Nilai Terisi": val_str,
                                                "Status": ev.get("status", "Manual / Kosong" if val is None else "Terisi"),
                                                "Rincian / Rumus Komputasi": ev.get("sumber", "-"),
                                            })
                                        st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)

                            if tab_ex_batch is not None:
                                with tab_ex_batch:
                                    st.caption(f"⚡ Skrining simultan untuk seluruh **{len(df_ex)}** baris data emiten menggunakan model Altman Z'', MDA Fisher, dan XGBoost.")
                                    if st.button("🚀 Jalankan Skrining Massal Seluruh Emiten", type="primary", key="btn_run_batch_excel"):
                                        def _do_batch_screen_excel():
                                            return batch_screen_financials(df_ex, config, model_path=str(MODEL_PATH) if MODEL_PATH.exists() else None)

                                        b_df, b_stats = run_animated_loading_process(
                                            task_name="Skrining Massal Multi-Model Seluruh Emiten (Excel)",
                                            target_info=f"{len(df_ex)} Baris Data Emiten • 3 Model Prediktif",
                                            task_type="batch",
                                            execute_fn=_do_batch_screen_excel,
                                            success_title="Skrining Massal Excel Selesai!",
                                            success_desc=f"{len(df_ex)} baris data emiten berhasil diklasifikasikan dengan Altman Z'', MDA, dan XGBoost.",
                                        )
                                        st.session_state["batch_results_excel"] = (b_df, b_stats)

                                    if "batch_results_excel" in st.session_state:
                                        b_df, b_stats = st.session_state["batch_results_excel"]
                                        render_batch_screening_results(b_df, b_stats, key_prefix="batch_ex_view")
                    except Exception as e:

                        st.error(f"Gagal membaca atau mengekstrak file Excel: {e}")

            elif mode == "Upload CSV":
                uploaded = st.file_uploader("Unggah file CSV laporan keuangan", type=["csv"])
                if uploaded:
                    try:
                        if is_idx_xbrl_data(uploaded):
                            detected_years = get_idx_document_years(uploaded)
                            default_csv_year = detected_years[0] if detected_years else 2025
                            if str(st.session_state.year).isdigit() and int(st.session_state.year) in detected_years:
                                default_csv_year = int(st.session_state.year)

                            col_c_y, col_c_info = st.columns([1.8, 2.2])
                            with col_c_y:
                                target_csv_year = st.radio(
                                    "Pilih Tahun Pelaporan Keuangan (Format BEI/IDX):",
                                    options=detected_years if detected_years else [2025, 2024],
                                    index=detected_years.index(default_csv_year) if default_csv_year in detected_years else 0,
                                    horizontal=True,
                                    key="csv_target_year_user",
                                )

                            csv_cache_key = f"{uploaded.name}_{uploaded.size}_{target_csv_year}"
                            if st.session_state.get("_last_parsed_csv_key_dash") != csv_cache_key:
                                def _do_extract_csv_dash():
                                    return extract_financial_values_from_idx_data(uploaded, int(target_csv_year))

                                parsed_csv, csv_evidence, _ = run_animated_loading_process(
                                    task_name="Ekstraksi Laporan Keuangan CSV BEI/IDX",
                                    target_info=f"{uploaded.name} (Tahun {target_csv_year})",
                                    task_type="csv",
                                    execute_fn=_do_extract_csv_dash,
                                    success_title="Ekstraksi CSV BEI/IDX Selesai!",
                                    success_desc=f"15 variabel proyek tahun {target_csv_year} berhasil diekstrak dan disinkronkan.",
                                )
                                st.session_state._last_parsed_csv_key_dash = csv_cache_key
                                st.session_state._cached_parsed_csv_dash = parsed_csv
                                st.session_state._cached_evidence_csv_dash = csv_evidence
                            else:
                                parsed_csv = st.session_state.get("_cached_parsed_csv_dash")
                                csv_evidence = st.session_state.get("_cached_evidence_csv_dash", {})

                            if parsed_csv:
                                if parsed_csv.get("ticker"):
                                    st.session_state.ticker = str(parsed_csv["ticker"]).strip().upper()
                                if parsed_csv.get("company"):
                                    st.session_state.company = str(parsed_csv["company"]).strip()
                                if parsed_csv.get("sector"):
                                    st.session_state.sector = str(parsed_csv["sector"]).strip()
                                if parsed_csv.get("report_year"):
                                    st.session_state.year = int(parsed_csv["report_year"])
                                fin0.update(parsed_csv)
                                st.session_state.financials = fin0
                                for k, v in parsed_csv.items():
                                    if v is not None:
                                        str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                        st.session_state[f"user_input_{k}"] = str_repr
                                        st.session_state[f"manual_{k}"] = str_repr

                                yr_csv_clean = int(parsed_csv.get("report_year", target_csv_year))
                                st.session_state["manual_report_year"] = yr_csv_clean
                                st.session_state["user_input_report_year"] = str(yr_csv_clean)
                                st.session_state["user_input_report_year_num"] = yr_csv_clean
                                st.session_state["admin_manual_report_year_input"] = yr_csv_clean
                                if parsed_csv.get("ticker"):
                                    st.session_state["user_input_ticker"] = str(parsed_csv["ticker"]).strip().upper()

                                with col_c_info:
                                    t_show = st.session_state.ticker or "EMITEN"
                                    c_show = st.session_state.company or "Perusahaan Tercatat"
                                    s_show = st.session_state.sector or "Umum / General"
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 10px 14px; margin-top: 14px;">
                                            <div style="font-weight: 850; font-size: 15px; color: #38bdf8;">🏢 {t_show} — {c_show}</div>
                                            <div style="font-size: 12px; color: #94a3b8;">Sektor: {s_show} | Tahun Terpilih: <b>{target_csv_year}</b></div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                st.success(f"✅ File CSV taksonomi BEI/IDX ({st.session_state.company} - {st.session_state.ticker} Tahun {target_csv_year}) berhasil diekstrak! 15 variabel terisi otomatis.")
                                with st.expander("🔍 Detail Hasil Ekstraksi dan Perhitungan Otomatis dari CSV BEI/IDX", expanded=True):
                                    ev_rows = []
                                    for item in VARIABLE_SCHEMA:
                                        k = item["key"]
                                        val = fin0.get(k)
                                        ev = csv_evidence.get(k, {})
                                        val_str = format_display_value(k, val)
                                        ev_rows.append({
                                            "Kode": item["code"],
                                            "Nama Variabel": item["label"],
                                            "Nilai": val_str,
                                            "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                            "Lembar / Bagian Sumber": str(ev.get("halaman", "-")),
                                            "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "-")),
                                        })
                                    st.session_state["saved_extraction_rows"] = ev_rows
                                    st.session_state["saved_extraction_meta"] = {
                                        "source_type": "CSV (BEI/IDX)",
                                        "filename": uploaded.name,
                                        "company": st.session_state.company,
                                        "ticker": st.session_state.ticker,
                                        "year": target_csv_year,
                                        "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                    }
                                    render_styled_dataframe(pd.DataFrame(ev_rows), is_light=is_light_theme())
                        else:
                            df = read_csv_file(uploaded)
                            st.session_state["uploaded_df"] = df
                            st.caption(f"📄 File CSV tabular memuat total **{len(df)}** baris data emiten.")

                            if len(df) > 1:
                                tab_csv_single, tab_csv_batch = st.tabs([
                                    "🏢 Analisis Tunggal (Pilih 1 Emiten)",
                                    "⚡ Skrining Massal Seluruh Baris (Batch Screening)",
                                ])
                            else:
                                tab_csv_single = st.container()
                                tab_csv_batch = None

                            with tab_csv_single:
                                st.dataframe(df.head(8), use_container_width=True)
                                row_idx = 0
                                if len(df) > 1:
                                    row_options = []
                                    for idx, r in df.iterrows():
                                        tick = r.get("ticker", r.get("kode_saham", r.get("kode emiten", f"Baris {idx+1}")))
                                        yr = r.get("report_year", r.get("tahun", r.get("year", "")))
                                        comp = r.get("company", r.get("nama_perusahaan", ""))
                                        row_options.append((idx, f"Baris {idx + 1}: {tick} ({yr}) {comp}".strip()))
                                    selected_choice = st.selectbox(
                                        "Pilih baris emiten/tahun untuk diekstrak ke form:",
                                        options=[opt[0] for opt in row_options],
                                        format_func=lambda i: row_options[i][1],
                                        key="user_csv_row_select",
                                    )
                                    row_idx = selected_choice

                                parsed_csv, csv_evidence = extract_financial_values_from_df(df, row_idx)
                                if parsed_csv:
                                    if parsed_csv.get("ticker"):
                                        st.session_state.ticker = str(parsed_csv["ticker"]).strip().upper()
                                    if parsed_csv.get("company"):
                                        st.session_state.company = str(parsed_csv["company"]).strip()
                                    if parsed_csv.get("report_year"):
                                        st.session_state.year = int(parsed_csv["report_year"])
                                    fin0.update(parsed_csv)
                                    st.session_state.financials = fin0
                                    for k, v in parsed_csv.items():
                                        if v is not None:
                                            str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                            st.session_state[f"user_input_{k}"] = str_repr
                                            st.session_state[f"manual_{k}"] = str_repr

                                    yr_csv_clean = int(parsed_csv.get("report_year", st.session_state.year))
                                    st.session_state["manual_report_year"] = yr_csv_clean
                                    st.session_state["user_input_report_year"] = str(yr_csv_clean)
                                    st.session_state["user_input_report_year_num"] = yr_csv_clean
                                    st.session_state["admin_manual_report_year_input"] = yr_csv_clean
                                    if parsed_csv.get("ticker"):
                                        st.session_state["user_input_ticker"] = str(parsed_csv["ticker"]).strip().upper()

                                    st.success(f"✅ Data CSV baris terpilih berhasil dimuat ke formulir!")

                                    with st.expander("🔍 Detail Pemetaan & Perhitungan Otomatis dari CSV", expanded=False):
                                        ev_rows = []
                                        schema_map = {item["key"]: item for item in VARIABLE_SCHEMA}
                                        for item in VARIABLE_SCHEMA:
                                            k = item["key"]
                                            val = fin0.get(k)
                                            ev = csv_evidence.get(k, {})
                                            val_str = format_display_value(k, val)
                                            ev_rows.append({
                                                "Kode": item["code"],
                                                "Nama Variabel": item["label"],
                                                "Nilai": val_str,
                                                "Status": ev.get("status", "Manual / Kosong" if val is None else "Terisi"),
                                                "Rincian / Rumus Komputasi": ev.get("sumber", "-"),
                                            })
                                        st.session_state["saved_extraction_rows"] = ev_rows
                                        st.session_state["saved_extraction_meta"] = {
                                            "source_type": "CSV Tabular",
                                            "filename": uploaded.name,
                                            "company": st.session_state.company,
                                            "ticker": st.session_state.ticker,
                                            "year": yr_csv_clean,
                                            "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                        }
                                        render_styled_dataframe(pd.DataFrame(ev_rows), is_light=is_light_theme())

                            if tab_csv_batch is not None:
                                with tab_csv_batch:
                                    st.caption(f"⚡ Skrining simultan untuk seluruh **{len(df)}** baris data emiten menggunakan model Altman Z'', MDA Fisher, dan XGBoost.")
                                    if st.button("🚀 Jalankan Skrining Massal Seluruh Emiten (CSV)", type="primary", key="btn_run_batch_csv"):
                                        def _do_batch_screen_csv():
                                            return batch_screen_financials(df, config, model_path=str(MODEL_PATH) if MODEL_PATH.exists() else None)

                                        b_df_csv, b_stats_csv = run_animated_loading_process(
                                            task_name="Skrining Massal Multi-Model Seluruh Emiten (CSV)",
                                            target_info=f"{len(df)} Baris Data Emiten • 3 Model Prediktif",
                                            task_type="batch",
                                            execute_fn=_do_batch_screen_csv,
                                            success_title="Skrining Massal CSV Selesai!",
                                            success_desc=f"{len(df)} baris data emiten berhasil diklasifikasikan dengan Altman Z'', MDA, dan XGBoost.",
                                        )
                                        st.session_state["batch_results_csv"] = (b_df_csv, b_stats_csv)

                                    if "batch_results_csv" in st.session_state:
                                        b_df_csv, b_stats_csv = st.session_state["batch_results_csv"]
                                        render_batch_screening_results(b_df_csv, b_stats_csv, key_prefix="batch_csv_view")
                    except Exception as e:

                        st.error(f"Gagal membaca atau mengekstrak CSV: {e}")

            elif mode == "Upload PDF":
                uploaded = st.file_uploader("Unggah file PDF laporan keuangan / tahunan (format IDX/BEI)", type=["pdf"])
                if uploaded:
                    try:
                        pages = extract_pdf_pages(uploaded)
                        detected_years = get_pdf_document_years(pages)
                    except Exception as e:
                        pages = []
                        detected_years = [2025, 2024]
                        st.error(f"Gagal membaca halaman dokumen PDF: {e}")

                    default_pdf_year = detected_years[0] if detected_years else 2025
                    if str(st.session_state.year).isdigit() and int(st.session_state.year) in detected_years:
                        default_pdf_year = int(st.session_state.year)

                    target_year = st.radio(
                        "Pilih Tahun Pelaporan Keuangan pada PDF:",
                        options=detected_years if detected_years else [2025, 2024],
                        index=detected_years.index(default_pdf_year) if default_pdf_year in detected_years else 0,
                        horizontal=True,
                        key="pdf_target_year_user",
                    )
                    pdf_cache_key = f"{uploaded.name}_{uploaded.size}_{target_year}"
                    if st.session_state.get("_last_parsed_pdf_key_dash") != pdf_cache_key:
                        def _do_extract_pdf_dash():
                            return extract_financial_values_from_pages(pages, int(target_year))

                        try:
                            parsed, pdf_evidence = run_animated_loading_process(
                                task_name="Ekstraksi Laporan Keuangan Dokumen PDF",
                                target_info=f"{uploaded.name} (Tahun {target_year}, {len(pages)} Halaman)",
                                task_type="pdf",
                                execute_fn=_do_extract_pdf_dash,
                                success_title="Ekstraksi PDF Selesai!",
                                success_desc=f"15 variabel proyek tahun {target_year} berhasil diekstrak dan disinkronkan dari dokumen PDF.",
                            )
                            st.session_state._last_parsed_pdf_key_dash = pdf_cache_key
                            st.session_state._cached_parsed_pdf_dash = parsed
                            st.session_state._cached_evidence_pdf_dash = pdf_evidence
                        except Exception as e:
                            parsed, pdf_evidence = None, {}
                            st.error(f"Gagal mengekstrak PDF: {e}")
                    else:
                        parsed = st.session_state.get("_cached_parsed_pdf_dash")
                        pdf_evidence = st.session_state.get("_cached_evidence_pdf_dash", {})

                    if parsed:
                        if parsed.get("ticker"):
                            st.session_state.ticker = str(parsed["ticker"]).strip().upper()
                        if parsed.get("company"):
                            st.session_state.company = str(parsed["company"]).strip()
                        if parsed.get("report_year"):
                            st.session_state.year = int(parsed["report_year"])
                        fin0.update(parsed)
                        st.session_state.financials = fin0
                        for k, v in parsed.items():
                            if v is not None:
                                str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                st.session_state[f"user_input_{k}"] = str_repr
                                st.session_state[f"manual_{k}"] = str_repr

                        yr_pdf_clean = int(parsed.get("report_year", target_year))
                        st.session_state["manual_report_year"] = yr_pdf_clean
                        st.session_state["user_input_report_year"] = str(yr_pdf_clean)
                        st.session_state["user_input_report_year_num"] = yr_pdf_clean
                        st.session_state["admin_manual_report_year_input"] = yr_pdf_clean
                        if parsed.get("ticker"):
                            st.session_state["user_input_ticker"] = str(parsed["ticker"]).strip().upper()

                        st.success(f"✅ Data berhasil diekstrak dari PDF ({len(pages)} halaman terbaca)! Nilai telah disesuaikan dengan variabel proyek!")

                        with st.expander("🔍 Detail Hasil Ekstraksi dan Perhitungan Otomatis dari PDF", expanded=True):
                            ev_rows = []
                            for item in VARIABLE_SCHEMA:
                                k = item["key"]
                                val = fin0.get(k)
                                ev = pdf_evidence.get(k, {})
                                val_str = format_display_value(k, val)
                                ev_rows.append({
                                    "Kode": item["code"],
                                    "Nama Variabel": item["label"],
                                    "Nilai": val_str,
                                    "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                    "Keterangan / Rumus": ev.get("metode", ev.get("sumber", "-")),
                                    "Halaman": str(ev.get("halaman", "-")),
                                })
                            st.session_state["saved_extraction_rows"] = ev_rows
                            st.session_state["saved_extraction_meta"] = {
                                "source_type": "PDF",
                                "filename": uploaded.name,
                                "company": st.session_state.company,
                                "ticker": st.session_state.ticker,
                                "year": yr_pdf_clean,
                                "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                            }
                            render_styled_dataframe(pd.DataFrame(ev_rows), is_light=is_light_theme())

        if st.session_state.get("saved_extraction_rows"):
            meta = st.session_state.get("saved_extraction_meta", {})
            src_tag = meta.get("source_type", "Ekstraksi")
            comp_tag = meta.get("company", st.session_state.company or "Emiten")
            tick_tag = meta.get("ticker", st.session_state.ticker or "")
            yr_tag = meta.get("year", st.session_state.year or "")
            time_tag = meta.get("timestamp", "")
            with st.expander(f"📋 Data Hasil Ekstraksi & Perhitungan Otomatis Tersimpan ({src_tag} — {comp_tag} {tick_tag} {yr_tag})", expanded=False):
                st.markdown(f"<div style='font-size:12px;color:#94a3b8;margin-bottom:8px;'>Data hasil ekstraksi tersimpan di sesi (Sumber: <b>{src_tag}</b>, Berkas/Emiten: <i>{meta.get('filename','-')}</i>, Waktu: {time_tag}). Data tetap tersimpan hingga Anda memasukkan/mengekstrak data baru atau mengosongkan formulir.</div>", unsafe_allow_html=True)
                render_styled_dataframe(pd.DataFrame(st.session_state["saved_extraction_rows"]), is_light=is_light_theme())

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # 3. Input Manual Form (Selalu tampil untuk koreksi/input langsung)
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(139,92,246,0.18);color:#c084fc;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(139,92,246,0.3);box-shadow:0 0 12px rgba(139,92,246,0.2);">📊</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">3. Nilai Akun Keuangan (Terisi Otomatis / Koreksi Manual)</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Semua nilai dalam mata uang Rupiah penuh atau satuan konsisten. Kolom dapat disunting bebas.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Sinkronkan Working Capital sebelum form dirender jika CA dan CL ada
            ca_pre = float(fin0.get("current_assets", 0.0) or 0.0)
            cl_pre = float(fin0.get("current_liabilities", 0.0) or 0.0)
            if ca_pre != 0.0 or cl_pre != 0.0:
                fin0["working_capital"] = ca_pre - cl_pre

            # Sinkronkan Beban Bunga (Interest Expense) sebelum form dirender jika belum terisi / 0
            ie_pre = float(fin0.get("interest_expense", 0.0) or 0.0)
            if ie_pre == 0.0:
                curr_t = str(fin0.get("ticker", st.session_state.ticker or "")).strip().upper()
                mock_entry = MOCK_IDX_DATA.get(curr_t, {})
                curr_y = int(fin0.get("report_year", st.session_state.year or 2024))
                mock_fin = mock_entry.get("financials_by_year", {}).get(curr_y, {}) or mock_entry.get("financials_by_year", {}).get(2024, {})
                if mock_fin and float(mock_fin.get("interest_expense", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(mock_fin["interest_expense"])
                elif float(fin0.get("total_debt", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(fin0["total_debt"]) * 0.058
                elif float(fin0.get("total_liabilities", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(fin0["total_liabilities"]) * 0.038
                elif float(fin0.get("total_assets", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(fin0["total_assets"]) * 0.02
                
                if fin0.get("interest_expense", 0.0) > 0:
                    ie_num = fin0["interest_expense"]
                    str_ie = f"{int(ie_num)}" if float(ie_num).is_integer() else f"{ie_num:.4f}"
                    st.session_state["user_input_interest_expense"] = str_ie
                    st.session_state["manual_interest_expense"] = str_ie

            fields = FINANCIAL_FIELDS
            cols = st.columns(2)
            for i, (key, label) in enumerate(fields):
                with cols[i % 2]:
                    if key == "ticker":
                        current_ticker_val = str(fin0.get("ticker", st.session_state.ticker or "ICBP")).strip().upper()
                        txt_input = st.text_input(
                            label,
                            value=current_ticker_val,
                            placeholder="Contoh: ICBP",
                            key="user_input_ticker",
                        ).upper()
                        fin0[key] = txt_input
                        st.session_state.ticker = txt_input
                    elif key == "report_year":
                        active_yr = int(st.session_state.year) if str(st.session_state.get("year", "")).isdigit() else 2024
                        if fin0.get("report_year") is not None and str(fin0["report_year"]).isdigit():
                            active_yr = int(fin0["report_year"])

                        if "user_input_report_year_num" in st.session_state and st.session_state["user_input_report_year_num"] != active_yr:
                            st.session_state["user_input_report_year_num"] = active_yr

                        def _on_user_bottom_year_changed():
                            new_y = int(st.session_state.user_input_report_year_num)
                            st.session_state.year = new_y
                            st.session_state["emiten_profile_year_input"] = new_y
                            st.session_state["admin_manual_report_year_input"] = new_y
                            st.session_state["manual_report_year"] = new_y
                            st.session_state["user_input_report_year"] = str(new_y)
                            if "financials" in st.session_state and isinstance(st.session_state.financials, dict):
                                st.session_state.financials["report_year"] = new_y

                        chosen_year_val = st.number_input(
                            label,
                            min_value=1900,
                            max_value=2100,
                            value=active_yr,
                            step=1,
                            key="user_input_report_year_num",
                            on_change=_on_user_bottom_year_changed,
                        )
                        fin0[key] = int(chosen_year_val)
                        st.session_state.year = int(chosen_year_val)
                        if "financials" in st.session_state and isinstance(st.session_state.financials, dict):
                            st.session_state.financials["report_year"] = int(chosen_year_val)
                    else:
                        current_val = fin0.get(key)
                        if current_val in (None, ""):
                            str_val = ""
                        elif isinstance(current_val, (int, float)):
                            if current_val == 0 or current_val == 0.0:
                                str_val = "0"
                            else:
                                str_val = f"{int(current_val)}" if float(current_val).is_integer() else f"{current_val:.4f}"
                        else:
                            str_val = str(current_val)
                        txt_input = st.text_input(
                            label,
                            value=str_val,
                            placeholder="Contoh: 1500000000",
                            key=f"user_input_{key}",
                        )
                        parsed_val = parse_financial_number(txt_input)
                        if parsed_val is not None:
                            fin0[key] = parsed_val
                        elif key not in fin0:
                            fin0[key] = 0.0

                        if parsed_val is not None and abs(parsed_val) >= 1000:
                            st.caption(f"💰 Nilai Penuh: Rp {int(parsed_val):,}")
                        elif parsed_val == 0:
                            st.caption("💰 Nilai: Rp 0")

            # Perbarui Working Capital berdasarkan nilai form saat ini
            ca = float(fin0.get("current_assets", 0.0) or 0.0)
            cl = float(fin0.get("current_liabilities", 0.0) or 0.0)
            if ca != 0.0 or cl != 0.0:
                fin0["working_capital"] = ca - cl
            st.session_state.financials = fin0

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        
        # 4. Tombol Eksekusi Analisis
        with st.container(border=True):
            st.markdown(
                """
                <a id="eksekusi_analisis_anchor"></a>
                <div style="margin-bottom:12px;">
                    <div style="font-size:15px;font-weight:850;color:#f8fafc;">⚡ Siap Melakukan Analisis Prediksi?</div>
                    <div style="font-size:12px;color:#94a3b8;margin-top:2px;">Sistem akan mengkalkulasi Altman Z''-Score, MDA Empiris, dan XGBoost Machine Learning sekaligus.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("🚀 Jalankan Analisis dan Klasifikasi Prediksi", type="primary", use_container_width=True):
                if not st.session_state.company or not st.session_state.ticker:
                    st.warning("Mohon lengkapi Nama dan Kode Perusahaan terlebih dahulu.")
                else:
                    def _do_execute_user_analysis():
                        fin0["ticker"] = st.session_state.ticker
                        fin0["report_year"] = int(st.session_state.year)
                        set_ratios_from_financials(fin0)
                        st.session_state.has_analyzed = True
                        
                        # Hitung hasil menggunakan parameter terikat admin dan simpan ke database audit
                        z, z_cls, mda, mda_cls, xgb_prob, _ = current_results()
                        save_prediction_to_db(
                            st.session_state.username,
                            st.session_state.company,
                            st.session_state.ticker,
                            int(st.session_state.year),
                            z, z_cls, mda, mda_cls, xgb_prob or 0.0
                        )

                    try:
                        run_animated_analysis_pipeline(
                            st.session_state.company,
                            st.session_state.ticker,
                            int(st.session_state.year),
                            execute_fn=_do_execute_user_analysis,
                            show_success_card=True,
                        )
                        st.toast("🎉 Analisis multi-model berhasil dieksekusi dan disimpan!", icon="⚡")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat menghitung rasio: {e}")

            if st.session_state.get("has_analyzed", False):
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                c_btn_a, c_btn_b = st.columns(2)
                with c_btn_a:
                    if st.button("📊 Buka Hasil Prediksi, Diagnosa dan Rekomendasi 🚀", type="secondary", use_container_width=True, key="btn_goto_pred_res_dash"):
                        set_page("Hasil Prediksi")
                        st.rerun()
                with c_btn_b:
                    if st.button("🎯 Buka Executive Dashboard Prediksi 🚀", type="secondary", use_container_width=True, key="btn_goto_prop_view_dash"):
                        set_page("Dashboard Prediksi")
                        st.rerun()


    # ========================================================
    # 2. HALAMAN INPUT: DATA PERUSAHAAN DAN LAPORAN KEUANGAN
    # Terpisah dari Dashboard Utama (Standar Terpadu Admin & User)
    # ========================================================
    elif page in ("Data dan Laporan Keuangan", "Data & Laporan Keuangan", "Data Perusahaan", "Laporan Keuangan", "Input Data", "Input Data Keuangan"):
        allow_analysis = config.get("allow_user_analysis", True)
        if not allow_analysis and st.session_state.role != "admin":
            st.warning("⚠️ **Mode Pemeliharaan:** Administrator sedang memperbarui parameter model. Tombol eksekusi analisis dinonaktifkan sementara.")
            st.stop()

        # Header Halaman dan Tombol Aksi di Pojok Kanan Atas (Satu Baris dengan Judul)
        c_title, c_top_act1, c_top_act2 = st.columns([2.5, 1.15, 1.35], gap="small")
        with c_title:
            section_title("Data Perusahaan dan Laporan Keuangan", "Identitas emiten dan impor pos laporan keuangan untuk analisis prediksi multi-model", tone="blue")
        with c_top_act1:
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Kosongkan Semua Form", key="btn_reset_adm_data_lap", help="Mengosongkan semua data emiten dan nilai laporan keuangan ke awal (kosong)", use_container_width=True):
                st.session_state.company = ""
                st.session_state.ticker = ""
                st.session_state.sector = ""
                st.session_state.financials = {}
                st.session_state.ratios = {"X1": 0.0, "X2": 0.0, "X3": 0.0, "X4": 0.0, "X5": 0.0}
                st.session_state.has_analyzed = False
                st.session_state.year = 2024
                st.session_state["emiten_profile_year_input"] = 2024
                st.session_state["admin_manual_report_year_input"] = 2024
                st.session_state["user_input_report_year_num"] = 2024
                st.session_state["manual_report_year"] = 2024
                st.session_state["user_input_report_year"] = "2024"
                st.session_state.analysis_date = datetime.date.today().strftime("%Y-%m-%d")
                for item in VARIABLE_SCHEMA:
                    st.session_state.pop(f"manual_{item['key']}", None)
                    st.session_state.pop(f"user_input_{item['key']}", None)
                st.session_state.pop("saved_extraction_rows", None)
                st.session_state.pop("saved_extraction_meta", None)
                st.session_state.pop("_last_parsed_excel_key_adm", None)
                st.session_state.pop("_cached_parsed_excel_adm", None)
                st.session_state.pop("_cached_evidence_excel_adm", None)
                st.session_state.pop("_last_parsed_pdf_key_adm", None)
                st.session_state.pop("_cached_parsed_pdf_adm", None)
                st.session_state.pop("_cached_evidence_pdf_adm", None)
                st.session_state.pop("_last_parsed_csv_key_adm", None)
                st.session_state.pop("_cached_parsed_csv_adm", None)
                st.session_state.pop("_cached_evidence_csv_adm", None)
                st.toast("Seluruh formulir masukan berhasil dikosongkan!", icon="🔄")
                st.rerun()
        with c_top_act2:
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            if st.button("💡 Muat Contoh Data (Demo)", key="btn_load_demo_adm_data_lap", help="Memuat data contoh ICBP 2024 ke seluruh formulir", use_container_width=True):
                st.session_state.company = "PT Indofood CBP Sukses Makmur Tbk"
                st.session_state.ticker = "ICBP"
                st.session_state.sector = "Consumer Non-Cyclicals / Food dan Beverage"
                st.session_state.year = 2024
                st.session_state["emiten_profile_year_input"] = 2024
                st.session_state["admin_manual_report_year_input"] = 2024
                st.session_state["user_input_report_year_num"] = 2024
                st.session_state["manual_report_year"] = 2024
                st.session_state["user_input_report_year"] = "2024"
                demo_fin = {
                    "ticker": "ICBP",
                    "report_year": 2024,
                    "current_assets": 58348000000000.0,
                    "current_liabilities": 25123000000000.0,
                    "total_assets": 121542000000000.0,
                    "retained_earnings": 38450000000000.0,
                    "ebit": 16250000000000.0,
                    "total_liabilities": 54890000000000.0,
                    "total_equity": 66652000000000.0,
                    "total_revenue": 67910000000000.0,
                    "market_cap": 128275000000000.0,
                    "net_income": 9560000000000.0,
                    "total_debt": 41200000000000.0,
                    "interest_expense": 2400000000000.0,
                    "working_capital": 33225000000000.0,
                }
                st.session_state.financials = demo_fin
                for k, v in demo_fin.items():
                    str_v = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else str(v)
                    st.session_state[f"manual_{k}"] = str_v
                    st.session_state[f"user_input_{k}"] = str_v
                try:
                    set_ratios_from_financials(demo_fin)
                    st.session_state.has_analyzed = True
                except Exception:
                    pass
                st.toast("Data contoh ICBP 2024 berhasil dimuat!", icon="💡")
                st.rerun()

        # Bagian 1: Data Perusahaan (Profil Emiten)
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(99,102,241,0.18);color:#818cf8;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(99,102,241,0.3);box-shadow:0 0 12px rgba(99,102,241,0.2);">🏢</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">1. Profil dan Identitas Emiten</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Identitas emiten dan periode tahun laporan keuangan yang dianalisis</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.company = st.text_input(
                    "Nama Perusahaan",
                    value=st.session_state.company,
                    placeholder="Contoh: PT Indofood CBP Sukses Makmur Tbk"
                )
                st.session_state.ticker = st.text_input(
                    "Kode Perusahaan (Ticker)",
                    value=st.session_state.ticker,
                    placeholder="Contoh: ICBP"
                ).upper()
                st.session_state.sector = st.text_input(
                    "Sektor Industri",
                    value=st.session_state.sector,
                    placeholder="Contoh: Consumer Non-Cyclicals / Food dan Beverage"
                )
            with c2:
                # Sinkronisasi otomatis 2 arah antara data laporan keuangan (report_year) dan Tahun Analisis
                fin_curr = st.session_state.get("financials", {})
                data_rep_yr = fin_curr.get("report_year")
                if data_rep_yr is not None and str(data_rep_yr).isdigit():
                    act_yr = int(data_rep_yr)
                    if st.session_state.get("year") != act_yr or st.session_state.get("emiten_profile_year_input") != act_yr:
                        st.session_state.year = act_yr
                        st.session_state["emiten_profile_year_input"] = act_yr
                        st.session_state["admin_manual_report_year_input"] = act_yr
                        st.session_state["user_input_report_year_num"] = act_yr

                def _on_top_year_changed():
                    new_y = int(st.session_state.emiten_profile_year_input)
                    st.session_state.year = new_y
                    if "financials" in st.session_state and isinstance(st.session_state.financials, dict):
                        st.session_state.financials["report_year"] = new_y
                    st.session_state["admin_manual_report_year_input"] = new_y
                    st.session_state["user_input_report_year_num"] = new_y
                    st.session_state["manual_report_year"] = new_y
                    st.session_state["user_input_report_year"] = str(new_y)

                cur_prof_yr = int(st.session_state.year) if str(st.session_state.get("year", "")).isdigit() else 2024
                if "emiten_profile_year_input" in st.session_state and st.session_state["emiten_profile_year_input"] != cur_prof_yr:
                    st.session_state["emiten_profile_year_input"] = cur_prof_yr

                st.session_state.year = st.number_input(
                    "Tahun Analisis",
                    2000, 2100,
                    value=cur_prof_yr,
                    key="emiten_profile_year_input",
                    on_change=_on_top_year_changed,
                    help="Tahun buku laporan keuangan emiten yang dianalisis (otomatis sinkron dengan pos data laporan keuangan)",
                )
                if "financials" in st.session_state and isinstance(st.session_state.financials, dict) and "report_year" in st.session_state.financials:
                    st.session_state.financials["report_year"] = int(st.session_state.year)
                
                # Fitur Pemilih Tanggal Gelembung Kalender Interaktif (Calendar Bubble Picker)
                raw_d = st.session_state.get("analysis_date", "")
                curr_date = datetime.date.today()
                if isinstance(raw_d, datetime.date):
                    curr_date = raw_d
                elif isinstance(raw_d, str) and raw_d.strip():
                    try:
                        curr_date = datetime.datetime.strptime(raw_d.strip(), "%Y-%m-%d").date()
                    except Exception:
                        try:
                            curr_date = datetime.date.fromisoformat(raw_d.strip())
                        except Exception:
                            curr_date = datetime.date.today()

                col_date_pick, col_date_today = st.columns([2.5, 1.2])
                with col_date_pick:
                    picked_date = st.date_input(
                        "Tanggal Analisis",
                        value=curr_date,
                        min_value=datetime.date(2000, 1, 1),
                        max_value=datetime.date(2100, 12, 31),
                        format="YYYY-MM-DD",
                        help="Klik kotak tanggal untuk membuka gelembung kalender interaktif dan memilih tanggal analisis",
                    )
                    if picked_date:
                        st.session_state.analysis_date = picked_date.strftime("%Y-%m-%d") if hasattr(picked_date, "strftime") else str(picked_date)
                with col_date_today:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("📅 Hari Ini", key="btn_set_today_analysis_date", use_container_width=True, help="Setel tanggal analisis langsung ke hari ini"):
                        st.session_state.analysis_date = datetime.date.today().strftime("%Y-%m-%d")
                        st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Bagian 2: Sumber Data dan Impor Laporan Keuangan
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(20,184,166,0.18);color:#2dd4bf;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(20,184,166,0.3);box-shadow:0 0 12px rgba(20,184,166,0.2);">📥</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">2. Sumber Data dan Impor Laporan Keuangan</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Unggah dokumen keuangan CSV, PDF, Excel BEI, atau tarik otomatis live via API Bursa</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("📖 Kamus variabel input (Standar BEI/IDX)", expanded=False):
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Kode": item["code"],
                            "Nama Variabel": item["label"],
                            "Kolom CSV": item["csv"],
                            "Digunakan untuk": item["used_by"],
                        }
                        for item in VARIABLE_SCHEMA
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                col_tpl1, col_tpl2 = st.columns(2)
                with col_tpl1:
                    st.download_button(
                        "📥 Unduh Format Template CSV Standar (.csv)",
                        get_sample_template_csv_bytes(),
                        file_name="template_laporan_keuangan_distress.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with col_tpl2:
                    st.download_button(
                        "📥 Unduh Format Template Excel Standar (.xlsx)",
                        get_sample_template_excel_bytes(),
                        file_name="template_laporan_keuangan_distress.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

            fin0 = st.session_state.get("financials", {})

            source_options = ["Input Manual", "🌐 Tarik Otomatis API Bursa (IDX)", "📊 Excel (BEI/IDX)", "CSV", "PDF"]
            saved_mode = st.session_state.get("source_mode", "📊 Excel (BEI/IDX)" if st.session_state.get("saved_extraction_rows") else "Input Manual")
            default_mode_idx = source_options.index(saved_mode) if saved_mode in source_options else 0
            mode = st.radio("Sumber Data", source_options, index=default_mode_idx, horizontal=True, key="adm_source_mode_radio")
            st.session_state.source_mode = mode

            if mode == "🌐 Tarik Otomatis API Bursa (IDX)":
                st.markdown("##### ⚡ Tarik Laporan Keuangan Otomatis via API IDX / Yahoo Finance (Mode Admin)")
                st.caption("Admin dapat menarik data laporan keuangan live emiten langsung ke sesi aktif dan mencatatnya ke database.")
                
                c_api_adm_t, c_api_adm_yr, c_api_adm_b = st.columns([2, 1.2, 1.5])
                with c_api_adm_t:
                    adm_tick = st.text_input("Kode Saham (Ticker)", value=st.session_state.ticker or "ICBP", placeholder="Contoh: ICBP, INDF, ASII, UNVR, KLBF, SMGR", key="adm_api_tick_input").upper()
                with c_api_adm_yr:
                    adm_yr_opt = st.selectbox("Periode", ["Tahun Terbaru (Latest)", "2025", "2024", "2023", "2022", "2021", "2020"], key="adm_api_yr_opt")
                with c_api_adm_b:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    adm_btn_pull = st.button("🚀 Tarik dan Hitung Rasio Otomatis", type="primary", use_container_width=True, key="adm_btn_pull_api")

                adm_picked = render_emiten_shortcuts("adm_api")
                if adm_picked:
                    adm_tick = adm_picked
                    st.session_state.ticker = adm_picked
                    adm_btn_pull = True

                if adm_btn_pull and adm_tick:
                    user_target_year = int(adm_yr_opt) if str(adm_yr_opt).isdigit() else None
                    def _do_fetch_api_adm():
                        return FinancialAPIClient.fetch_emiten_profile_and_financials(adm_tick, target_year=user_target_year)

                    try:
                        data_api = run_animated_loading_process(
                            task_name="Penarikan Data Live API Bursa (Admin)",
                            target_info=f"Emiten {adm_tick} • Periode: {adm_yr_opt}",
                            task_type="api",
                            execute_fn=_do_fetch_api_adm,
                            success_title=f"Data Emiten {adm_tick} Berhasil Diunduh!",
                            success_desc="Pos akun neraca, laba rugi, dan rasio keuangan telah sinkron.",
                        )
                        st.session_state.api_emiten_data = data_api
                        st.session_state.company = data_api["company"]
                        st.session_state.ticker = data_api["ticker"]
                        st.session_state.sector = data_api["sector"]

                        avail_yrs = data_api.get("years", [2024])
                        if user_target_year is not None:
                            chosen_yr = user_target_year
                        elif adm_yr_opt == "Tahun Terbaru (Latest)":
                            chosen_yr = avail_yrs[0] if avail_yrs else 2024
                        else:
                            chosen_yr = int(adm_yr_opt) if str(adm_yr_opt).isdigit() else (avail_yrs[0] if avail_yrs else 2024)

                        st.session_state.year = int(chosen_yr)

                        fin_pulled = data_api["financials_by_year"].get(chosen_yr)
                        if not fin_pulled:
                            fin_pulled = next(iter(data_api["financials_by_year"].values()), {})
                        fin_pulled = dict(fin_pulled)
                        fin_pulled["report_year"] = int(chosen_yr)
                        fin_pulled["ticker"] = st.session_state.ticker

                        # Pastikan beban bunga (interest_expense) selalu terisi dan tidak 0
                        if float(fin_pulled.get("interest_expense", 0.0) or 0.0) == 0.0:
                            t_u = str(st.session_state.ticker).upper()
                            m_e = MOCK_IDX_DATA.get(t_u, {})
                            m_f = m_e.get("financials_by_year", {}).get(int(chosen_yr), {}) or m_e.get("financials_by_year", {}).get(2024, {})
                            if m_f and float(m_f.get("interest_expense", 0.0) or 0.0) > 0:
                                fin_pulled["interest_expense"] = float(m_f["interest_expense"])
                            elif float(fin_pulled.get("total_debt", 0.0) or 0.0) > 0:
                                fin_pulled["interest_expense"] = float(fin_pulled["total_debt"]) * 0.058
                            elif float(fin_pulled.get("total_liabilities", 0.0) or 0.0) > 0:
                                fin_pulled["interest_expense"] = float(fin_pulled["total_liabilities"]) * 0.038

                        fin0.update(fin_pulled)
                        st.session_state.financials = fin0

                        for k, v in fin_pulled.items():
                            if v is not None:
                                str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                st.session_state[f"manual_{k}"] = str_repr
                                st.session_state[f"user_input_{k}"] = str_repr

                        # Khusus interest_expense: pastikan terisi di session_state string
                        ie_val = fin_pulled.get("interest_expense")
                        if ie_val is not None:
                            str_ie = f"{int(ie_val)}" if isinstance(ie_val, (int, float)) and float(ie_val).is_integer() else str(ie_val)
                            st.session_state["manual_interest_expense"] = str_ie
                            st.session_state["user_input_interest_expense"] = str_ie

                        api_yr_num = int(chosen_yr)
                        st.session_state.year = api_yr_num
                        st.session_state["manual_report_year"] = api_yr_num
                        st.session_state["user_input_report_year"] = str(api_yr_num)
                        st.session_state["admin_manual_report_year_input"] = api_yr_num
                        st.session_state["user_input_report_year_num"] = api_yr_num

                        api_ev_rows = []
                        for item in VARIABLE_SCHEMA:
                            k = item["key"]
                            val = fin0.get(k)
                            val_str = format_display_value(k, val)
                            api_ev_rows.append({
                                "Kode": item["code"],
                                "Nama Variabel": item["label"],
                                "Nilai": val_str,
                                "Status": "Terisi (API)" if val is not None else "Tidak Ditemukan",
                                "Lembar / Bagian Sumber": data_api.get("source", "API Bursa (IDX)"),
                                "Rincian / Rumus Komputasi": "Data Laporan Keuangan Emiten Terbuka",
                            })
                        st.session_state["saved_extraction_rows"] = api_ev_rows
                        st.session_state["saved_extraction_meta"] = {
                            "source_type": f"API Bursa ({data_api.get('source', 'IDX')})",
                            "filename": f"{adm_tick} ({chosen_yr})",
                            "company": st.session_state.company,
                            "ticker": st.session_state.ticker,
                            "year": int(chosen_yr),
                            "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                        }

                        set_ratios_from_financials(fin0)
                        st.session_state.has_analyzed = True

                        z_res, z_cls_res, mda_res, mda_cls_res, xgb_res, _ = current_results()
                        save_prediction_to_db(
                            st.session_state.username,
                            st.session_state.company,
                            st.session_state.ticker,
                            int(st.session_state.year),
                            z_res, z_cls_res, mda_res, mda_cls_res, xgb_res or 0.0
                        )
                        source_tag = data_api.get("source", "Multi-Source Engine")
                        st.success(f"🎉 Berhasil menarik data {data_api['company']} ({data_api['ticker']}) tahun {chosen_yr} via **{source_tag}**, menghitung rasio, dan menyimpan ke database audit!")
                        st.rerun()
                    except Exception as e:
                        render_api_error_feedback(e, adm_tick)

            elif mode == "📊 Excel (BEI/IDX)":
                st.markdown("##### 📊 Impor Langsung File Excel Resmi BEI / IDX (.xlsx, .xls)")
                st.caption("Unggah file Excel laporan keuangan resmi yang diunduh langsung dari situs Bursa Efek Indonesia (idx.co.id). Sistem akan otomatis mengenali format XBRL/multi-sheet, mendeteksi emiten dan tahun, dan mengekstrak 15 variabel proyek secara cerdas.")

                uploaded_excel = st.file_uploader(
                    "Unggah file Excel Laporan Keuangan (.xlsx, .xls)",
                    type=["xlsx", "xls"],
                    key="excel_uploader_admin",
                    help="Mendukung file Excel resmi BEI/IDX (multi-sheet XBRL taksonomi) maupun file Excel tabular data emiten."
                )
                if uploaded_excel:
                    try:
                        if is_idx_xbrl_data(uploaded_excel):
                            detected_years = get_idx_document_years(uploaded_excel)
                            default_excel_year = detected_years[0] if detected_years else 2025
                            if str(st.session_state.year).isdigit() and int(st.session_state.year) in detected_years:
                                default_excel_year = int(st.session_state.year)

                            col_ex_y, col_ex_info = st.columns([1.8, 2.2])
                            with col_ex_y:
                                target_excel_year = st.radio(
                                    "Pilih Tahun Pelaporan Keuangan:",
                                    options=detected_years if detected_years else [2025, 2024],
                                    index=detected_years.index(default_excel_year) if default_excel_year in detected_years else 0,
                                    horizontal=True,
                                    key="admin_excel_target_year",
                                )

                            excel_cache_key = f"{uploaded_excel.name}_{uploaded_excel.size}_{target_excel_year}"
                            if st.session_state.get("_last_parsed_excel_key_adm") != excel_cache_key:
                                def _do_extract_excel_adm():
                                    return extract_financial_values_from_idx_data(uploaded_excel, int(target_excel_year))

                                parsed_excel, excel_evidence, _ = run_animated_loading_process(
                                    task_name="Ekstraksi Laporan Keuangan Excel BEI/IDX",
                                    target_info=f"{uploaded_excel.name} (Tahun {target_excel_year})",
                                    task_type="excel",
                                    execute_fn=_do_extract_excel_adm,
                                    success_title="Ekstraksi Excel BEI/IDX Selesai!",
                                    success_desc=f"15 variabel proyek tahun {target_excel_year} berhasil diekstrak dan disinkronkan.",
                                )
                                st.session_state._last_parsed_excel_key_adm = excel_cache_key
                                st.session_state._cached_parsed_excel_adm = parsed_excel
                                st.session_state._cached_evidence_excel_adm = excel_evidence
                            else:
                                parsed_excel = st.session_state.get("_cached_parsed_excel_adm")
                                excel_evidence = st.session_state.get("_cached_evidence_excel_adm", {})

                            if parsed_excel:
                                if parsed_excel.get("ticker"):
                                    st.session_state.ticker = str(parsed_excel["ticker"]).strip().upper()
                                if parsed_excel.get("company"):
                                    st.session_state.company = str(parsed_excel["company"]).strip()
                                if parsed_excel.get("sector"):
                                    st.session_state.sector = str(parsed_excel["sector"]).strip()
                                if parsed_excel.get("report_year"):
                                    st.session_state.year = int(parsed_excel["report_year"])
                                fin0.update(parsed_excel)
                                st.session_state.financials = fin0

                                for k, v in parsed_excel.items():
                                    if v is not None:
                                        str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                        st.session_state[f"manual_{k}"] = str_repr
                                        st.session_state[f"user_input_{k}"] = str_repr
                                excel_actual_year = int(parsed_excel.get("report_year", target_excel_year))
                                st.session_state.year = excel_actual_year
                                st.session_state["manual_report_year"] = excel_actual_year
                                st.session_state["user_input_report_year"] = str(excel_actual_year)
                                st.session_state["admin_manual_report_year_input"] = excel_actual_year
                                st.session_state["user_input_report_year_num"] = excel_actual_year

                                with col_ex_info:
                                    t_show = st.session_state.ticker or "EMITEN"
                                    c_show = st.session_state.company or "Perusahaan Tercatat"
                                    s_show = st.session_state.sector or "Umum / General"
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 10px 14px; margin-top: 14px;">
                                            <div style="font-weight: 850; font-size: 15px; color: #38bdf8;">🏢 {t_show} — {c_show}</div>
                                            <div style="font-size: 12px; color: #94a3b8;">Sektor: {s_show} | Tahun Terpilih: <b>{target_excel_year}</b></div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                st.success(f"✅ Data Excel BEI/IDX {st.session_state.company} ({st.session_state.ticker}) tahun {target_excel_year} berhasil diekstrak! 15 variabel proyek terisi otomatis.")

                                st.markdown("### Hasil Ekstraksi dan Kalkulasi Variabel Excel BEI/IDX")
                                ev_rows = []
                                for item in VARIABLE_SCHEMA:
                                    k = item["key"]
                                    val = fin0.get(k)
                                    ev = excel_evidence.get(k, {})
                                    val_str = format_display_value(k, val)
                                    ev_rows.append({
                                        "Kode": item["code"],
                                        "Nama Variabel": item["label"],
                                        "Nilai": val_str,
                                        "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                        "Lembar / Bagian Sumber": str(ev.get("halaman", "-")),
                                        "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "-")),
                                    })
                                st.session_state["saved_extraction_rows"] = ev_rows
                                st.session_state["saved_extraction_meta"] = {
                                    "source_type": "Excel (BEI/IDX)",
                                    "filename": uploaded_excel.name,
                                    "company": st.session_state.company,
                                    "ticker": st.session_state.ticker,
                                    "year": target_excel_year,
                                    "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                }
                                render_styled_dataframe(pd.DataFrame(ev_rows), is_light=is_light_theme())

                                if st.button("⚡ Terapkan dan Hitung Rasio Otomatis (Excel BEI/IDX)", type="primary", key="btn_apply_admin_excel"):
                                    set_ratios_from_financials(fin0)
                                    st.session_state.has_analyzed = True
                                    z_res, z_cls_res, mda_res, mda_cls_res, xgb_res, _ = current_results()
                                    save_prediction_to_db(
                                        st.session_state.username,
                                        st.session_state.company,
                                        st.session_state.ticker,
                                        int(st.session_state.year),
                                        z_res, z_cls_res, mda_res, mda_cls_res, xgb_res or 0.0
                                    )
                                    st.success("✅ Nilai berhasil diterapkan dan rasio dihitung!")
                                    st.rerun()
                        else:
                            df_ex = read_excel_file(uploaded_excel)
                            if isinstance(df_ex, dict):
                                best_sheet = next(iter(df_ex.keys()))
                                df_ex = df_ex[best_sheet]
                            st.session_state["uploaded_df"] = df_ex
                            st.dataframe(df_ex.head(50), use_container_width=True)
                            st.caption(f"File Excel tabular memuat {len(df_ex)} baris data.")

                            row_idx = 0
                            if len(df_ex) > 1:
                                row_options = []
                                for idx, r in df_ex.iterrows():
                                    tick = r.get("ticker", r.get("kode_saham", r.get("kode emiten", f"Baris {idx+1}")))
                                    yr = r.get("report_year", r.get("tahun", r.get("year", "")))
                                    comp = r.get("company", r.get("nama_perusahaan", ""))
                                    row_options.append((idx, f"Baris {idx + 1}: {tick} ({yr}) {comp}".strip()))
                                selected_choice = st.selectbox(
                                    "Pilih baris emiten/tahun untuk diekstrak:",
                                    options=[opt[0] for opt in row_options],
                                    format_func=lambda i: row_options[i][1],
                                    key="admin_excel_row_select",
                                )
                                row_idx = selected_choice

                            if st.button("⚡ Ekstraksi Otomatis dari Tabular Excel", type="primary", key="btn_apply_admin_tabular_ex"):
                                def _do_extract_excel_tabular_adm():
                                    return extract_financial_values_from_df(df_ex, row_idx)

                                parsed_ex, ex_evidence = run_animated_loading_process(
                                    task_name="Ekstraksi Baris Data Excel Tabular",
                                    target_info=f"Baris ke-{row_idx+1} • {uploaded_excel.name}",
                                    task_type="excel",
                                    execute_fn=_do_extract_excel_tabular_adm,
                                    success_title="Ekstraksi Excel Tabular Selesai!",
                                    success_desc="Pos akun keuangan berhasil dimuat ke sesi dan rasio dihitung.",
                                )
                                if parsed_ex:
                                    if parsed_ex.get("ticker"):
                                        st.session_state.ticker = str(parsed_ex["ticker"]).strip().upper()
                                    if parsed_ex.get("company"):
                                        st.session_state.company = str(parsed_ex["company"]).strip()
                                    if parsed_ex.get("report_year"):
                                        st.session_state.year = int(parsed_ex["report_year"])
                                    fin0.update(parsed_ex)
                                    st.session_state.financials = fin0
                                    for k, v in parsed_ex.items():
                                        if v is not None:
                                            str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                            st.session_state[f"manual_{k}"] = str_repr
                                            st.session_state[f"user_input_{k}"] = str_repr
                                    tabular_year = int(parsed_ex.get("report_year", st.session_state.year))
                                    st.session_state.year = tabular_year
                                    st.session_state["manual_report_year"] = tabular_year
                                    st.session_state["user_input_report_year"] = str(tabular_year)
                                    st.session_state["admin_manual_report_year_input"] = tabular_year
                                    st.session_state["user_input_report_year_num"] = tabular_year

                                    tab_rows = []
                                    for item in VARIABLE_SCHEMA:
                                        k = item["key"]
                                        val = fin0.get(k)
                                        ev = ex_evidence.get(k, {}) if isinstance(ex_evidence, dict) else {}
                                        val_str = format_display_value(k, val)
                                        tab_rows.append({
                                            "Kode": item["code"],
                                            "Nama Variabel": item["label"],
                                            "Nilai": val_str,
                                            "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                            "Lembar / Bagian Sumber": str(ev.get("halaman", "Baris Data Tabular")),
                                            "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "Pemetaan Kolom")),
                                        })
                                    st.session_state["saved_extraction_rows"] = tab_rows
                                    st.session_state["saved_extraction_meta"] = {
                                        "source_type": "Excel Tabular",
                                        "filename": uploaded_excel.name,
                                        "company": st.session_state.company,
                                        "ticker": st.session_state.ticker,
                                        "year": tabular_year,
                                        "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                    }

                                    set_ratios_from_financials(fin0)
                                    st.session_state.has_analyzed = True
                                    st.success("✅ Data Excel tabular berhasil diekstrak dan rasio dihitung otomatis!")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Gagal membaca atau mengekstrak file Excel: {e}")

                if not uploaded_excel and st.session_state.get("saved_extraction_rows"):
                    meta = st.session_state.get("saved_extraction_meta", {})
                    src_tag = meta.get("source_type", "Excel (BEI/IDX)")
                    fn_tag = meta.get("filename", "")
                    comp_tag = meta.get("company", st.session_state.company or "")
                    tick_tag = meta.get("ticker", st.session_state.ticker or "")
                    yr_tag = meta.get("year", st.session_state.year or "")
                    time_tag = meta.get("timestamp", "")
                    st.markdown(
                        f"""
                        <div style="background: rgba(16, 185, 129, 0.08); border: 1.5px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 12px 16px; margin: 14px 0 10px 0;">
                            <div style="font-weight: 800; font-size: 14px; color: #10b981;">💾 Data Hasil Ekstraksi Tersimpan di Sesi ({src_tag})</div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 3px;">
                                Emiten: <b>{comp_tag} ({tick_tag})</b> • Tahun: <b>{yr_tag}</b> • Sumber: <i>{fn_tag}</i> • Waktu Ekstraksi: {time_tag}
                            </div>
                            <div style="font-size: 11.5px; color: #10b981; margin-top: 2px;">
                                ℹ️ Data hasil ekstraksi dan kalkulasi variabel tetap tersimpan di sesi sampai Anda mengunggah file baru atau mengosongkan form.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("### Hasil Ekstraksi dan Kalkulasi Variabel (Tersimpan di Sesi)")
                    render_styled_dataframe(pd.DataFrame(st.session_state["saved_extraction_rows"]), is_light=is_light_theme())
                    if st.button("⚡ Terapkan dan Hitung Rasio Otomatis (Dari Data Ekstraksi Tersimpan)", type="primary", key="btn_apply_saved_excel_adm"):
                        set_ratios_from_financials(fin0)
                        st.session_state.has_analyzed = True
                        z_res, z_cls_res, mda_res, mda_cls_res, xgb_res, _ = current_results()
                        save_prediction_to_db(
                            st.session_state.username,
                            st.session_state.company,
                            st.session_state.ticker,
                            int(st.session_state.year),
                            z_res, z_cls_res, mda_res, mda_cls_res, xgb_res or 0.0
                        )
                        st.success("✅ Nilai tersimpan berhasil diterapkan dan rasio dihitung!")
                        st.rerun()

            elif mode == "CSV":
                uploaded = st.file_uploader("Upload CSV laporan keuangan", type=["csv"])
                if uploaded:
                    try:
                        if is_idx_xbrl_data(uploaded):
                            detected_years = get_idx_document_years(uploaded)
                            default_csv_year = detected_years[0] if detected_years else 2025
                            if str(st.session_state.year).isdigit() and int(st.session_state.year) in detected_years:
                                default_csv_year = int(st.session_state.year)

                            col_c_y, col_c_info = st.columns([1.8, 2.2])
                            with col_c_y:
                                target_csv_year = st.radio(
                                    "Pilih Tahun Pelaporan Keuangan (Format BEI/IDX):",
                                    options=detected_years if detected_years else [2025, 2024],
                                    index=detected_years.index(default_csv_year) if default_csv_year in detected_years else 0,
                                    horizontal=True,
                                    key="admin_csv_idx_year",
                                )

                            csv_cache_key = f"{uploaded.name}_{uploaded.size}_{target_csv_year}"
                            if st.session_state.get("_last_parsed_csv_key_adm") != csv_cache_key:
                                def _do_extract_csv_adm():
                                    return extract_financial_values_from_idx_data(uploaded, int(target_csv_year))

                                parsed_csv, csv_evidence, _ = run_animated_loading_process(
                                    task_name="Ekstraksi Laporan Keuangan CSV BEI/IDX",
                                    target_info=f"{uploaded.name} (Tahun {target_csv_year})",
                                    task_type="csv",
                                    execute_fn=_do_extract_csv_adm,
                                    success_title="Ekstraksi CSV BEI/IDX Selesai!",
                                    success_desc=f"15 variabel proyek tahun {target_csv_year} berhasil diekstrak dan disinkronkan.",
                                )
                                st.session_state._last_parsed_csv_key_adm = csv_cache_key
                                st.session_state._cached_parsed_csv_adm = parsed_csv
                                st.session_state._cached_evidence_csv_adm = csv_evidence
                            else:
                                parsed_csv = st.session_state.get("_cached_parsed_csv_adm")
                                csv_evidence = st.session_state.get("_cached_evidence_csv_adm", {})

                            if parsed_csv:
                                if parsed_csv.get("ticker"):
                                    st.session_state.ticker = str(parsed_csv["ticker"]).strip().upper()
                                if parsed_csv.get("company"):
                                    st.session_state.company = str(parsed_csv["company"]).strip()
                                if parsed_csv.get("sector"):
                                    st.session_state.sector = str(parsed_csv["sector"]).strip()
                                if parsed_csv.get("report_year"):
                                    st.session_state.year = int(parsed_csv["report_year"])
                                fin0.update(parsed_csv)
                                st.session_state.financials = fin0

                                for k, v in parsed_csv.items():
                                    if v is not None:
                                        str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                        st.session_state[f"manual_{k}"] = str_repr
                                        st.session_state[f"user_input_{k}"] = str_repr

                                with col_c_info:
                                    t_show = st.session_state.ticker or "EMITEN"
                                    c_show = st.session_state.company or "Perusahaan Tercatat"
                                    s_show = st.session_state.sector or "Umum / General"
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 10px; padding: 10px 14px; margin-top: 14px;">
                                            <div style="font-weight: 850; font-size: 15px; color: #38bdf8;">🏢 {t_show} — {c_show}</div>
                                            <div style="font-size: 12px; color: #94a3b8;">Sektor: {s_show} | Tahun Terpilih: <b>{target_csv_year}</b></div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                st.success(f"✅ Data CSV BEI/IDX {st.session_state.company} ({st.session_state.ticker}) tahun {target_csv_year} berhasil diekstrak! 15 variabel proyek terisi otomatis.")

                                st.markdown("### Hasil Ekstraksi dan Kalkulasi Variabel CSV BEI/IDX")
                                ev_rows = []
                                for item in VARIABLE_SCHEMA:
                                    k = item["key"]
                                    val = fin0.get(k)
                                    ev = csv_evidence.get(k, {})
                                    val_str = format_display_value(k, val)
                                    ev_rows.append({
                                        "Kode": item["code"],
                                        "Nama Variabel": item["label"],
                                        "Nilai": val_str,
                                        "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                        "Lembar / Bagian Sumber": str(ev.get("halaman", "-")),
                                        "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "-")),
                                    })
                                st.session_state["saved_extraction_rows"] = ev_rows
                                st.session_state["saved_extraction_meta"] = {
                                    "source_type": "CSV (BEI/IDX)",
                                    "filename": uploaded.name,
                                    "company": st.session_state.company,
                                    "ticker": st.session_state.ticker,
                                    "year": target_csv_year,
                                    "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                }
                                render_styled_dataframe(pd.DataFrame(ev_rows), is_light=is_light_theme())

                                if st.button("⚡ Terapkan dan Hitung Rasio Otomatis (CSV BEI/IDX)", type="primary", key="btn_apply_admin_idx_csv"):
                                    set_ratios_from_financials(fin0)
                                    st.session_state.has_analyzed = True
                                    st.rerun()
                        else:
                            df = read_csv_file(uploaded)
                            st.dataframe(df.head(50), use_container_width=True)
                            st.caption(f"{len(df):,} baris terbaca.")
                            st.session_state["uploaded_df"] = df

                            row_idx = 0
                            if len(df) > 1:
                                admin_row_opts = []
                                for idx, r in df.iterrows():
                                    tick = r.get("ticker", r.get("kode_saham", r.get("kode emiten", f"Baris {idx+1}")))
                                    yr = r.get("report_year", r.get("tahun", r.get("year", "")))
                                    comp = r.get("company", r.get("nama_perusahaan", ""))
                                    admin_row_opts.append((idx, f"Baris {idx + 1}: {tick} ({yr}) {comp}".strip()))
                                chosen_admin_row = st.selectbox(
                                    "Pilih baris emiten/tahun untuk diproses:",
                                    options=[opt[0] for opt in admin_row_opts],
                                    format_func=lambda i: admin_row_opts[i][1],
                                    key="admin_csv_row_select",
                                )
                                row_idx = chosen_admin_row

                            c_btn_auto, c_btn_map = st.columns([1.5, 1])
                            with c_btn_auto:
                                if st.button("⚡ Ekstraksi Otomatis dari CSV (Kalkulasi Cerdas)", type="primary", use_container_width=True):
                                    def _do_extract_csv_tabular_adm():
                                        return extract_financial_values_from_df(df, row_idx)

                                    parsed_csv, csv_evidence = run_animated_loading_process(
                                        task_name="Ekstraksi Baris Data CSV Tabular",
                                        target_info=f"Baris ke-{row_idx+1} • {uploaded.name}",
                                        task_type="csv",
                                        execute_fn=_do_extract_csv_tabular_adm,
                                        success_title="Ekstraksi CSV Tabular Selesai!",
                                        success_desc="Pos akun dan rasio keuangan telah berhasil diekstrak.",
                                    )
                                    if parsed_csv:
                                        if parsed_csv.get("ticker"):
                                            st.session_state.ticker = str(parsed_csv["ticker"]).strip().upper()
                                        if parsed_csv.get("company"):
                                            st.session_state.company = str(parsed_csv["company"]).strip()
                                        if parsed_csv.get("report_year"):
                                            st.session_state.year = int(parsed_csv["report_year"])
                                        fin0.update(parsed_csv)
                                        st.session_state.financials = fin0
                                        for k, v in parsed_csv.items():
                                            if v is not None:
                                                str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                                st.session_state[f"manual_{k}"] = str_repr
                                                st.session_state[f"user_input_{k}"] = str_repr
                                        actual_csv_yr = int(parsed_csv.get("report_year", st.session_state.year))
                                        st.session_state.year = actual_csv_yr
                                        st.session_state["manual_report_year"] = actual_csv_yr
                                        st.session_state["user_input_report_year"] = str(actual_csv_yr)
                                        st.session_state["admin_manual_report_year_input"] = actual_csv_yr
                                        st.session_state["user_input_report_year_num"] = actual_csv_yr

                                        csv_tab_rows = []
                                        for item in VARIABLE_SCHEMA:
                                            k = item["key"]
                                            val = fin0.get(k)
                                            ev = csv_evidence.get(k, {}) if isinstance(csv_evidence, dict) else {}
                                            val_str = format_display_value(k, val)
                                            csv_tab_rows.append({
                                                "Kode": item["code"],
                                                "Nama Variabel": item["label"],
                                                "Nilai": val_str,
                                                "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                                "Lembar / Bagian Sumber": str(ev.get("halaman", "Baris Data Tabular")),
                                                "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "Pemetaan Kolom")),
                                            })
                                        st.session_state["saved_extraction_rows"] = csv_tab_rows
                                        st.session_state["saved_extraction_meta"] = {
                                            "source_type": "CSV Tabular",
                                            "filename": uploaded.name,
                                            "company": st.session_state.company,
                                            "ticker": st.session_state.ticker,
                                            "year": actual_csv_yr,
                                            "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                        }

                                        set_ratios_from_financials(fin0)
                                        st.session_state.has_analyzed = True
                                        st.success("✅ Nilai finansial berhasil diekstrak dan rasio dihitung otomatis!")
                                        st.rerun()

                            st.markdown("### Pemetaan Kolom CSV Manual")
                            cols = list(df.columns)
                            mapping = {}
                            clean_cols = {re.sub(r"[\s_\-]+", " ", str(c).strip().lower()): c for c in cols}
                            for key, label in FINANCIAL_FIELDS:
                                default_col = "-- tidak digunakan --"
                                spec_aliases = COLUMN_ALIASES.get(key, [])
                                for al in spec_aliases:
                                    norm_al = re.sub(r"[\s_\-]+", " ", al.lower().strip())
                                    for norm_col, orig_col in clean_cols.items():
                                        if norm_al == norm_col or norm_al in norm_col:
                                            default_col = orig_col
                                            break
                                    if default_col != "-- tidak digunakan --":
                                        break

                                options = ["-- tidak digunakan --"] + cols
                                chosen_idx = options.index(default_col) if default_col in options else 0
                                chosen = st.selectbox(label, options, index=chosen_idx, key=f"map_{key}")
                                if chosen != options[0]:
                                    mapping[key] = chosen

                            if st.button("Terapkan Pemetaan Kolom Manual", type="secondary"):
                                fin = {}
                                for k, col in mapping.items():
                                    value = df[col].iloc[row_idx]
                                    if k == "ticker":
                                        if pd.notna(value):
                                            fin[k] = str(value).strip().upper()
                                    elif k == "report_year":
                                        year = parse_financial_number(value)
                                        if year is not None:
                                            fin[k] = int(year)
                                    else:
                                        val = parse_financial_number(value)
                                        if val is not None:
                                            fin[k] = val
                                fin = complete_financial_values(fin)
                                fin0.update(fin)
                                st.session_state.financials = fin0
                                if fin0.get("report_year") and str(fin0["report_year"]).isdigit():
                                    csv_map_yr = int(fin0["report_year"])
                                    st.session_state.year = csv_map_yr
                                    st.session_state["manual_report_year"] = csv_map_yr
                                    st.session_state["user_input_report_year"] = str(csv_map_yr)
                                    st.session_state["admin_manual_report_year_input"] = csv_map_yr
                                    st.session_state["user_input_report_year_num"] = csv_map_yr

                                map_rows = []
                                for item in VARIABLE_SCHEMA:
                                    k = item["key"]
                                    val = fin0.get(k)
                                    val_str = format_display_value(k, val)
                                    map_rows.append({
                                        "Kode": item["code"],
                                        "Nama Variabel": item["label"],
                                        "Nilai": val_str,
                                        "Status": "Terisi" if val is not None else "Tidak Ditemukan",
                                        "Lembar / Bagian Sumber": "Pemetaan Kolom CSV Manual",
                                        "Rincian / Rumus Komputasi": mapping.get(k, "-"),
                                    })
                                st.session_state["saved_extraction_rows"] = map_rows
                                st.session_state["saved_extraction_meta"] = {
                                    "source_type": "CSV (Pemetaan Manual)",
                                    "filename": uploaded.name,
                                    "company": st.session_state.company,
                                    "ticker": st.session_state.ticker,
                                    "year": int(st.session_state.year),
                                    "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                                }

                                try:
                                    set_ratios_from_financials(fin0)
                                    st.session_state.has_analyzed = True
                                    st.success("Nilai finansial berhasil dipetakan dari CSV dan rasio telah dihitung.")
                                except Exception as e:
                                    st.warning(f"Data CSV dipetakan, tetapi rasio belum dihitung: {e}")
                    except Exception as e:
                        st.error(f"CSV tidak dapat diproses: {e}")

                if not uploaded and st.session_state.get("saved_extraction_rows"):
                    meta = st.session_state.get("saved_extraction_meta", {})
                    src_tag = meta.get("source_type", "CSV")
                    fn_tag = meta.get("filename", "")
                    comp_tag = meta.get("company", st.session_state.company or "")
                    tick_tag = meta.get("ticker", st.session_state.ticker or "")
                    yr_tag = meta.get("year", st.session_state.year or "")
                    time_tag = meta.get("timestamp", "")
                    st.markdown(
                        f"""
                        <div style="background: rgba(16, 185, 129, 0.08); border: 1.5px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 12px 16px; margin: 14px 0 10px 0;">
                            <div style="font-weight: 800; font-size: 14px; color: #10b981;">💾 Data Hasil Ekstraksi Tersimpan di Sesi ({src_tag})</div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 3px;">
                                Emiten: <b>{comp_tag} ({tick_tag})</b> • Tahun: <b>{yr_tag}</b> • Sumber: <i>{fn_tag}</i> • Waktu Ekstraksi: {time_tag}
                            </div>
                            <div style="font-size: 11.5px; color: #10b981; margin-top: 2px;">
                                ℹ️ Data hasil ekstraksi dan kalkulasi variabel tetap tersimpan di sesi sampai Anda mengunggah file baru atau mengosongkan form.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("### Hasil Ekstraksi dan Kalkulasi Variabel (Tersimpan di Sesi)")
                    render_styled_dataframe(pd.DataFrame(st.session_state["saved_extraction_rows"]), is_light=is_light_theme())
                    if st.button("⚡ Terapkan dan Hitung Rasio Otomatis (Dari Data Ekstraksi Tersimpan)", type="primary", key="btn_apply_saved_csv_adm"):
                        set_ratios_from_financials(fin0)
                        st.session_state.has_analyzed = True
                        z_res, z_cls_res, mda_res, mda_cls_res, xgb_res, _ = current_results()
                        save_prediction_to_db(
                            st.session_state.username,
                            st.session_state.company,
                            st.session_state.ticker,
                            int(st.session_state.year),
                            z_res, z_cls_res, mda_res, mda_cls_res, xgb_res or 0.0
                        )
                        st.success("✅ Nilai tersimpan berhasil diterapkan dan rasio dihitung!")
                        st.rerun()

            elif mode == "PDF":
                uploaded = st.file_uploader("Upload PDF laporan tahunan/laporan keuangan", type=["pdf"])
                if uploaded:
                    try:
                        pages = extract_pdf_pages(uploaded)
                        detected_years = get_pdf_document_years(pages)
                    except Exception as e:
                        pages = []
                        detected_years = [2025, 2024]
                        st.error(f"Gagal membaca teks PDF: {e}")

                    default_pdf_year = detected_years[0] if detected_years else 2025
                    if str(st.session_state.year).isdigit() and int(st.session_state.year) in detected_years:
                        default_pdf_year = int(st.session_state.year)

                    target_year = st.radio(
                        "Tahun kolom yang diekstrak dari PDF:",
                        options=detected_years if detected_years else [2025, 2024],
                        index=detected_years.index(default_pdf_year) if default_pdf_year in detected_years else 0,
                        horizontal=True,
                        key="admin_pdf_year_input",
                    )
                    text = "\n\n".join(pages)
                    st.session_state["pdf_text"] = text
                    st.success(f"Teks PDF berhasil diekstrak: {len(text):,} karakter dari {len(pages)} halaman.")

                    pdf_cache_key_adm = f"{uploaded.name}_{uploaded.size}_{target_year}"
                    if st.session_state.get("_last_parsed_pdf_key_adm") != pdf_cache_key_adm:
                        def _do_extract_pdf_adm():
                            return extract_financial_values_from_pages(pages, int(target_year))

                        try:
                            parsed, extraction_evidence = run_animated_loading_process(
                                task_name="Ekstraksi Laporan Keuangan Dokumen PDF (Admin)",
                                target_info=f"{uploaded.name} (Tahun {target_year}, {len(pages)} Halaman)",
                                task_type="pdf",
                                execute_fn=_do_extract_pdf_adm,
                                success_title="Ekstraksi PDF Selesai!",
                                success_desc=f"15 variabel proyek tahun {target_year} berhasil diekstrak dan disinkronkan dari dokumen PDF.",
                            )
                            st.session_state._last_parsed_pdf_key_adm = pdf_cache_key_adm
                            st.session_state._cached_parsed_pdf_adm = parsed
                            st.session_state._cached_evidence_pdf_adm = extraction_evidence
                        except Exception as e:
                            parsed, extraction_evidence = None, {}
                            st.error(f"Gagal mengekstrak PDF: {e}")
                    else:
                        parsed = st.session_state.get("_cached_parsed_pdf_adm")
                        extraction_evidence = st.session_state.get("_cached_evidence_pdf_adm", {})

                    if parsed:
                        if parsed.get("ticker"):
                            st.session_state.ticker = str(parsed["ticker"]).strip().upper()
                        if parsed.get("company"):
                            st.session_state.company = str(parsed["company"]).strip()
                        if parsed.get("report_year"):
                            st.session_state.year = int(parsed["report_year"])
                        fin0.update(parsed)
                        st.session_state.financials = fin0
                        for k, v in parsed.items():
                            if v is not None:
                                str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                st.session_state[f"manual_{k}"] = str_repr
                                st.session_state[f"user_input_{k}"] = str_repr
                        st.session_state["manual_report_year"] = int(parsed.get("report_year", target_year))
                        st.session_state["user_input_report_year"] = str(parsed.get("report_year", target_year))
                        st.session_state["admin_manual_report_year_input"] = int(parsed.get("report_year", target_year))

                    st.markdown("### Hasil Ekstraksi dan Kalkulasi Variabel PDF")
                    schema_by_key = {item["key"]: item for item in VARIABLE_SCHEMA}
                    ev_table = []
                    for k in schema_by_key:
                        val = parsed.get(k)
                        val_str = format_display_value(k, val)
                        ev = extraction_evidence.get(k, {})
                        ev_table.append({
                            "Kode": schema_by_key[k]["code"],
                            "Nama Variabel": schema_by_key[k]["label"],
                            "Nilai": val_str,
                            "Status": ev.get("status", "Tidak ditemukan" if val is None else "Terisi"),
                            "Lembar / Bagian Sumber": str(ev.get("halaman", "-")),
                            "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "-")),
                        })
                    st.session_state["saved_extraction_rows"] = ev_table
                    st.session_state["saved_extraction_meta"] = {
                        "source_type": "PDF",
                        "filename": uploaded.name,
                        "company": st.session_state.company,
                        "ticker": st.session_state.ticker,
                        "year": target_year,
                        "timestamp": datetime.datetime.now().strftime("%d %b %Y, %H:%M WIB"),
                    }
                    render_styled_dataframe(pd.DataFrame(ev_table), is_light=is_light_theme())

                    if st.button("Gunakan hasil ekstraksi PDF", type="primary"):
                        fin0.update(parsed)
                        st.session_state.financials = fin0
                        for k, v in parsed.items():
                            if v is not None:
                                str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                                st.session_state[f"manual_{k}"] = str_repr
                                st.session_state[f"user_input_{k}"] = str_repr
                        st.session_state["manual_report_year"] = int(parsed.get("report_year", target_year))
                        st.session_state["user_input_report_year"] = str(parsed.get("report_year", target_year))
                        st.session_state["admin_manual_report_year_input"] = int(parsed.get("report_year", target_year))
                        try:
                            set_ratios_from_financials(fin0)
                            st.session_state.has_analyzed = True
                            st.success("Hasil ekstraksi dimasukkan ke model dan rasio berhasil dihitung.")
                        except Exception as e:
                            st.warning(f"Gagal menghitung rasio otomatis: {e}")
                        st.rerun()

                if not uploaded and st.session_state.get("saved_extraction_rows"):
                    meta = st.session_state.get("saved_extraction_meta", {})
                    src_tag = meta.get("source_type", "PDF")
                    fn_tag = meta.get("filename", "")
                    comp_tag = meta.get("company", st.session_state.company or "")
                    tick_tag = meta.get("ticker", st.session_state.ticker or "")
                    yr_tag = meta.get("year", st.session_state.year or "")
                    time_tag = meta.get("timestamp", "")
                    st.markdown(
                        f"""
                        <div style="background: rgba(16, 185, 129, 0.08); border: 1.5px solid rgba(16, 185, 129, 0.35); border-radius: 10px; padding: 12px 16px; margin: 14px 0 10px 0;">
                            <div style="font-weight: 800; font-size: 14px; color: #10b981;">💾 Data Hasil Ekstraksi Tersimpan di Sesi ({src_tag})</div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 3px;">
                                Emiten: <b>{comp_tag} ({tick_tag})</b> • Tahun: <b>{yr_tag}</b> • Sumber: <i>{fn_tag}</i> • Waktu Ekstraksi: {time_tag}
                            </div>
                            <div style="font-size: 11.5px; color: #10b981; margin-top: 2px;">
                                ℹ️ Data hasil ekstraksi dan kalkulasi variabel tetap tersimpan di sesi sampai Anda mengunggah berkas baru atau mengosongkan formulir.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("### Hasil Ekstraksi dan Kalkulasi Variabel (Tersimpan di Sesi)")
                    render_styled_dataframe(pd.DataFrame(st.session_state["saved_extraction_rows"]), is_light=is_light_theme())
                    if st.button("⚡ Terapkan dan Hitung Rasio Otomatis (Dari Data Ekstraksi Tersimpan)", type="primary", key="btn_apply_saved_pdf_adm"):
                        set_ratios_from_financials(fin0)
                        st.session_state.has_analyzed = True
                        z_res, z_cls_res, mda_res, mda_cls_res, xgb_res, _ = current_results()
                        save_prediction_to_db(
                            st.session_state.username,
                            st.session_state.company,
                            st.session_state.ticker,
                            int(st.session_state.year),
                            z_res, z_cls_res, mda_res, mda_cls_res, xgb_res or 0.0
                        )
                        st.success("✅ Nilai tersimpan berhasil diterapkan dan rasio dihitung!")
                        st.rerun()

        if st.session_state.get("saved_extraction_rows"):
            meta = st.session_state.get("saved_extraction_meta", {})
            src_tag = meta.get("source_type", "Ekstraksi")
            comp_tag = meta.get("company", st.session_state.company or "Emiten")
            tick_tag = meta.get("ticker", st.session_state.ticker or "")
            yr_tag = meta.get("year", st.session_state.year or "")
            time_tag = meta.get("timestamp", "")
            with st.expander(f"📋 Data Hasil Ekstraksi & Kalkulasi Variabel Tersimpan ({src_tag} — {comp_tag} {tick_tag} {yr_tag})", expanded=(mode == "Input Manual")):
                st.markdown(f"<div style='font-size:12px;color:#94a3b8;margin-bottom:8px;'>Data hasil ekstraksi tersimpan di sesi (Sumber: <b>{src_tag}</b>, Berkas/Emiten: <i>{meta.get('filename','-')}</i>, Waktu: {time_tag}). Data tetap tersimpan hingga Anda memasukkan/mengekstrak data baru atau mengosongkan formulir.</div>", unsafe_allow_html=True)
                render_styled_dataframe(pd.DataFrame(st.session_state["saved_extraction_rows"]), is_light=is_light_theme())

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(139,92,246,0.18);color:#c084fc;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(139,92,246,0.3);box-shadow:0 0 12px rgba(139,92,246,0.2);">📝</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">2. Input Manual / Koreksi Nilai Akun</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Format kolom: Nomor. Nama Akun (kolom: nama_kolom). Nilai dalam satuan Rupiah penuh.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            fin0 = st.session_state.get("financials", {})

            # Sinkronkan Working Capital sebelum form admin dirender jika CA dan CL ada
            ca_pre = float(fin0.get("current_assets", 0.0) or 0.0)
            cl_pre = float(fin0.get("current_liabilities", 0.0) or 0.0)
            if ca_pre != 0.0 or cl_pre != 0.0:
                fin0["working_capital"] = ca_pre - cl_pre

            # Sinkronkan Beban Bunga (Interest Expense) sebelum form admin dirender jika belum terisi / 0
            ie_pre = float(fin0.get("interest_expense", 0.0) or 0.0)
            if ie_pre == 0.0:
                curr_t = str(fin0.get("ticker", st.session_state.ticker or "")).strip().upper()
                mock_entry = MOCK_IDX_DATA.get(curr_t, {})
                curr_y = int(fin0.get("report_year", st.session_state.year or 2024))
                mock_fin = mock_entry.get("financials_by_year", {}).get(curr_y, {}) or mock_entry.get("financials_by_year", {}).get(2024, {})
                if mock_fin and float(mock_fin.get("interest_expense", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(mock_fin["interest_expense"])
                elif float(fin0.get("total_debt", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(fin0["total_debt"]) * 0.058
                elif float(fin0.get("total_liabilities", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(fin0["total_liabilities"]) * 0.038
                elif float(fin0.get("total_assets", 0.0) or 0.0) > 0:
                    fin0["interest_expense"] = float(fin0["total_assets"]) * 0.02
                
                if fin0.get("interest_expense", 0.0) > 0:
                    ie_num = fin0["interest_expense"]
                    str_ie = f"{int(ie_num)}" if float(ie_num).is_integer() else f"{ie_num:.4f}"
                    st.session_state["manual_interest_expense"] = str_ie
                    st.session_state["user_input_interest_expense"] = str_ie

            fields = FINANCIAL_FIELDS
            cols = st.columns(2)
            for i, (key, label) in enumerate(fields):
                with cols[i % 2]:
                    if key == "ticker":
                        fin0[key] = st.text_input(
                            label,
                            value=str(fin0.get(key, st.session_state.ticker) or ""),
                            placeholder="Contoh: BBCA"
                        ).upper()
                    elif key == "report_year":
                        active_yr = int(st.session_state.year) if str(st.session_state.get("year", "")).isdigit() else 2024
                        if fin0.get("report_year") is not None and str(fin0["report_year"]).isdigit():
                            active_yr = int(fin0["report_year"])
                        
                        if "admin_manual_report_year_input" in st.session_state and st.session_state["admin_manual_report_year_input"] != active_yr:
                            st.session_state["admin_manual_report_year_input"] = active_yr

                        def _on_bottom_admin_year_changed():
                            new_y = int(st.session_state.admin_manual_report_year_input)
                            st.session_state.year = new_y
                            st.session_state["emiten_profile_year_input"] = new_y
                            st.session_state["user_input_report_year_num"] = new_y
                            st.session_state["manual_report_year"] = new_y
                            st.session_state["user_input_report_year"] = str(new_y)
                            if "financials" in st.session_state and isinstance(st.session_state.financials, dict):
                                st.session_state.financials["report_year"] = new_y

                        fin0[key] = st.number_input(
                            label,
                            min_value=1900,
                            max_value=2100,
                            value=active_yr,
                            step=1,
                            key="admin_manual_report_year_input",
                            on_change=_on_bottom_admin_year_changed,
                        )
                        st.session_state.year = int(fin0[key])
                        if "financials" in st.session_state and isinstance(st.session_state.financials, dict):
                            st.session_state.financials["report_year"] = int(fin0[key])
                    else:
                        current_val = fin0.get(key)
                        if current_val in (None, ""):
                            str_val = ""
                        elif isinstance(current_val, (int, float)):
                            if current_val == 0 or current_val == 0.0:
                                str_val = "0"
                            else:
                                str_val = f"{int(current_val)}" if float(current_val).is_integer() else f"{current_val:.4f}"
                        else:
                            str_val = str(current_val)
                        txt_input = st.text_input(
                            label,
                            value=str_val,
                            placeholder="Contoh: 1500000000",
                            key=f"manual_{key}",
                            help="Masukkan nilai sesuai laporan keuangan. Kolom dapat dihapus atau dikosongkan.",
                        )
                        parsed_val = parse_financial_number(txt_input)
                        if parsed_val is not None:
                            fin0[key] = parsed_val
                        elif key not in fin0:
                            fin0[key] = 0.0

                        if parsed_val is not None and abs(parsed_val) >= 1000:
                            st.caption(f"💰 Nilai Penuh: Rp {int(parsed_val):,}")
                        elif parsed_val == 0:
                            st.caption("💰 Nilai: Rp 0")

            current_assets = float(fin0.get("current_assets", 0.0) or 0.0)
            current_liabilities = float(fin0.get("current_liabilities", 0.0) or 0.0)
            calculated_working_capital = current_assets - current_liabilities
            use_calculated_working_capital = st.checkbox("Gunakan Working Capital otomatis (Current Assets − Current Liabilities)", value=True)
            if use_calculated_working_capital:
                fin0["working_capital"] = calculated_working_capital
            st.session_state.financials = fin0

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Hitung Rasio X1–X5 dan Simpan ke Database", type="primary", use_container_width=True):
                def _do_execute_admin_analysis():
                    set_ratios_from_financials(fin0)
                    st.session_state.has_analyzed = True
                    if fin0.get("ticker"):
                        st.session_state.ticker = fin0["ticker"]
                    if fin0.get("report_year"):
                        st.session_state.year = int(fin0["report_year"])
                    
                    # Otomatis simpan ke database riwayat
                    z, z_cls, mda, mda_cls, xgb_prob, _ = current_results()
                    save_prediction_to_db(
                        st.session_state.username,
                        st.session_state.company,
                        st.session_state.ticker,
                        int(st.session_state.year),
                        z, z_cls, mda, mda_cls, xgb_prob or 0.0
                    )

                try:
                    t_val = fin0.get("ticker", st.session_state.ticker or "EMITEN")
                    c_val = st.session_state.company or f"Emiten {t_val}"
                    y_val = fin0.get("report_year", st.session_state.year or 2024)
                    run_animated_analysis_pipeline(
                        c_val,
                        t_val,
                        y_val,
                        execute_fn=_do_execute_admin_analysis,
                        show_success_card=True,
                    )
                    st.toast("🎉 Rasio berhasil dihitung dan riwayat analisis disimpan ke database!", icon="⚡")
                except Exception as e:
                    st.error(str(e))

            if st.session_state.get("has_analyzed", False):
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                c_btn_a, c_btn_b = st.columns(2)
                with c_btn_a:
                    if st.button("📊 Buka Hasil Prediksi, Diagnosa dan Rekomendasi 🚀", type="primary", use_container_width=True, key="btn_goto_pred_from_adm_dl"):
                        set_page("Hasil Prediksi")
                        st.rerun()
                with c_btn_b:
                    if st.button("🏠 Buka Dashboard Terintegrasi 🚀", type="secondary", use_container_width=True, key="btn_goto_dash_from_adm_dl"):
                        set_page("Dashboard")
                        st.rerun()

    elif page == "Manajemen Pengguna":
        set_page("Pengaturan Model")
        st.rerun()

    elif page == "Pengaturan Model":
        if st.session_state.role != "admin":
            st.error("Akses ditolak! Halaman ini khusus untuk Administrator.")
            st.stop()
            
        section_title("Pusat Kontrol dan Otoritas Sistem (Admin Control)", "Kendali parameter model global, audit hasil analisis pengguna, manajemen akun, dan kontrol website")

        if "user_mgmt_flash_success" in st.session_state:
            succ_global = st.session_state.get("user_mgmt_flash_success")
            try:
                st.toast(succ_global, icon="🎉")
            except Exception:
                pass
            st.success(f"{succ_global} 👉 *Buka tab '👥 Manajemen Pengguna' di bawah untuk melihat rincian akun.*")

        tab_param, tab_audit, tab_users, tab_db, tab_site = st.tabs([
            "⚙️ Parameter Model Global",
            "📊 Audit dan Moderasi Prediksi User",
            "👥 Manajemen Pengguna",
            "🗄️ Database dan Cloud Hosting",
            "📢 Kontrol Website dan Kebijakan"
        ])

        with tab_param:
            st.markdown("<div style='font-size:15px;font-weight:850;color:#f8fafc;margin-bottom:4px;'>Konfigurasi Parameter Perhitungan (Otoritas Global - 3 Kategori Operasional)</div>", unsafe_allow_html=True)
            st.caption("Perubahan pada parameter di bawah ini akan langsung menentukan hasil perhitungan klasifikasi 3 Kategori (Safe Zone, Grey Area, Distress Zone) di halaman User secara real-time.")
            
            with st.container(border=True):
                st.markdown("<div style='font-size:14px;font-weight:800;color:#2563eb;margin-bottom:8px;'>📐 1. Model Altman Z''-Score (Standar Industri dan 3 Zona)</div>", unsafe_allow_html=True)
                a = config["altman_coefficients"]
                cols = st.columns(4)
                for col, key in zip(cols, ["X1", "X2", "X3", "X4"]):
                    with col:
                        a[key] = st.number_input(f"Koefisien {key}", value=float(a[key]), format="%.4f", key=f"admin_a_{key}")
                
                # Preset Selector Altman
                st.markdown("<div style='font-size:12px;font-weight:750;color:#94a3b8;margin-top:8px;'>Pilihan Preset Ambang Batas Altman Z'':</div>", unsafe_allow_html=True)
                c_pre1, c_pre2 = st.columns(2)
                with c_pre1:
                    if st.button("📌 Terapkan Standar Baku (1.81 dan 2.99)", key="btn_preset_bab3", use_container_width=True):
                        config["altman_thresholds"]["distress"] = 1.81
                        config["altman_thresholds"]["grey"] = 2.99
                        config["altman_thresholds"]["selected_standard"] = "bab3_standard"
                        st.success("Preset Baku (1.81 dan 2.99) dipilih! Klik Simpan di bawah.")
                with c_pre2:
                    if st.button("📌 Terapkan Standar Alternatif (1.10 dan 2.60)", key="btn_preset_alt", use_container_width=True):
                        config["altman_thresholds"]["distress"] = 1.10
                        config["altman_thresholds"]["grey"] = 2.60
                        config["altman_thresholds"]["selected_standard"] = "alt_standard"
                        st.success("Preset Alternatif (1.10 & 2.60) dipilih! Klik Simpan di bawah.")

                c_t1, c_t2, c_t3 = st.columns(3)
                with c_t1:
                    config["altman_thresholds"]["distress"] = st.number_input("Batas Distress (Z'' <)", value=float(config["altman_thresholds"]["distress"]), format="%.2f", key="admin_alt_distress")
                with c_t2:
                    config["altman_thresholds"]["grey"] = st.number_input("Batas Grey Area (Z'' <=)", value=float(config["altman_thresholds"].get("grey", 2.99)), format="%.2f", key="admin_alt_grey")
                with c_t3:
                    st.metric("Zona Aman (Safe Zone)", f"Z'' > {float(config['altman_thresholds'].get('grey', 2.99)):.2f}")

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<div style='font-size:14px;font-weight:800;color:#059669;margin-bottom:4px;'>📊 2. Z''-Score Koefisien Baru (MDA Empiris BEI - 3 Zona)</div>", unsafe_allow_html=True)
                st.caption("Koefisien empiris hasil estimasi ulang rasio X1-X4 pada seluruh 704 observasi emiten manufaktur BEI:")
                m_coef = config["mda_coefficients"]
                mcols = st.columns(4)
                for idx, key in enumerate(["X1", "X2", "X3", "X4"]):
                    with mcols[idx]:
                        m_coef[key] = st.number_input(f"Koefisien {key}", value=float(m_coef.get(key, 0.0)), format="%.4f", key=f"admin_m_{key}")
                
                mda_th_cfg = config.get("mda_thresholds", {"distress": 0.0, "grey": 1.0, "cutoff": float(config.get("mda_threshold", 0.3844))})
                c_mda1, c_mda2, c_mda3 = st.columns(3)
                with c_mda1:
                    mda_distress_in = st.number_input("Batas Distress Zone (Z' <)", value=float(mda_th_cfg.get("distress", 0.0)), format="%.2f", key="admin_mda_distress")
                with c_mda2:
                    mda_grey_in = st.number_input("Batas Grey Area (Z' <=)", value=float(mda_th_cfg.get("grey", 1.0)), format="%.2f", key="admin_mda_grey")
                with c_mda3:
                    mda_cut_in = st.number_input("Titik Potong Centroid (Cut-off)", value=float(config.get("mda_threshold", 0.3844)), format="%.4f", key="admin_mda_cutoff", help="Titik potong objektif tengah antara centroid Distress (-2.4502) dan Non-Distress (+3.2189)")
                
                config["mda_threshold"] = mda_cut_in
                config["mda_thresholds"] = {"distress": mda_distress_in, "grey": mda_grey_in, "cutoff": mda_cut_in}

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<div style='font-size:14px;font-weight:800;color:#7c3aed;margin-bottom:8px;'>🤖 3. XGBoost Machine Learning (3 Kategori Operasional)</div>", unsafe_allow_html=True)
                meta = get_model_metadata(str(MODEL_PATH))
                if meta.get("exists"):
                    st.info(f"🤖 **Status Model Aktif:** Fitur input: `{meta.get('features')}` | Pohon: `{meta.get('num_trees')}` | Target: `{meta.get('target')}`")
                else:
                    st.warning("⚠️ Model XGBoost belum tersedia.")
                
                xgb_th_cfg = config.get("xgb_thresholds", {"safe": 0.35, "distress": 0.65, "cutoff": float(config.get("xgb_threshold", 0.5))})
                c_xgb1, c_xgb2, c_xgb3 = st.columns(3)
                with c_xgb1:
                    xgb_safe_in = st.number_input("Batas Safe Zone (P <)", 0.0, 1.0, float(xgb_th_cfg.get("safe", 0.35)), 0.01, key="admin_xgb_safe", help="Probabilitas di bawah nilai ini dikelompokkan sebagai Safe Zone")
                with c_xgb2:
                    xgb_dist_in = st.number_input("Batas Distress Zone (P >)", 0.0, 1.0, float(xgb_th_cfg.get("distress", 0.65)), 0.01, key="admin_xgb_distress", help="Probabilitas di atas nilai ini dikelompokkan sebagai Distress Zone")
                with c_xgb3:
                    xgb_cut_in = st.number_input("Titik Tengah Cut-off", 0.0, 1.0, float(xgb_th_cfg.get("cutoff", 0.50)), 0.01, key="admin_xgb_cutoff", help="Ambang batas standar biner (default: 0.50)")
                
                config["xgb_threshold"] = xgb_cut_in
                config["xgb_thresholds"] = {"safe": xgb_safe_in, "distress": xgb_dist_in, "cutoff": xgb_cut_in}
                st.caption(f"🛡️ **Konfigurasi 3 Kategori:** Safe Zone ($P < {xgb_safe_in*100:.0f}\\%$), Grey Area (${xgb_safe_in*100:.0f}\\% \\le P \\le {xgb_dist_in*100:.0f}\\%$), Distress Zone ($P > {xgb_dist_in*100:.0f}\\%$)")

                curr_split_sz = float(st.session_state.get("eval_split_ratio", 0.20))
                cur_tr_pct = int(round((1.0 - curr_split_sz) * 100))
                cur_ts_pct = int(round(curr_split_sz * 100))

                if st.button("⚡ Kalibrasi / Latih Ulang Model XGBoost", key="admin_retrain_xgb_btn", help="Melatih ulang XGBoost menggunakan seluruh data master dan kriteria target resmi (RE < 0 dan EBIT < 0)"):
                    master_f = BASE_DIR / "data" / "datakeuangan.xlsx"
                    if master_f.exists():
                        with st.spinner(f"⚡ Sedang melatih ulang model XGBoost ({cur_tr_pct}% latih / {cur_ts_pct}% uji) pada dataset master BEI..."):
                            df_m = pd.read_excel(master_f)
                            res = train_xgboost_classifier(df_m, output_path=str(MODEL_PATH), test_size=curr_split_sz, n_estimators=50, max_depth=2, learning_rate=0.3)
                            st.success(f"🎉 Model XGBoost berhasil dilatih ulang pada porsi evaluasi {cur_tr_pct}/{cur_ts_pct}! Akurasi: {res['accuracy']*100:.2f}%, AUC: {res['roc_auc']:.4f}")
                            st.rerun()
                    else:
                        st.error("File datakeuangan.xlsx tidak ditemukan.")

                with st.expander("📊 Lihat Laporan Evaluasi Performa Model (Confusion Matrix dan ROC-AUC)", expanded=False):
                    eval_adm = get_xgboost_evaluation_metrics(test_size=curr_split_sz) if get_xgboost_evaluation_metrics else {}
                    render_model_evaluation_dashboard(eval_adm, config=config, active_session_ratios=st.session_state.get("ratios", {}))

            if st.button("💾 Terapkan dan Kunci Konfigurasi ke Sistem", type="primary", key="btn_save_config_admin"):
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                st.session_state.config = config
                st.success("✅ Konfigurasi parameter 3 Kategori berhasil diperbarui dan langsung mengikat seluruh perhitungan pada akun User.")

        with tab_audit:
            st.markdown("#### Audit dan Moderasi Data Hasil Analisis Pengguna")
            st.caption("Administrator berhak memantau, memeriksa detail, memuat ulang ke sesi analisis, serta menghapus data riwayat pengguna.")
            
            c_info, c_btn = st.columns([3, 1.2])
            with c_info:
                st.info("💡 Menu navigasi khusus **📜 Histori Prediksi** kini tersedia di bilah samping (sidebar) dengan filter interaktif dan grafik analisis.")
            with c_btn:
                if st.button("📜 Buka Menu Histori 🚀", key="btn_jump_to_hist_from_tab", use_container_width=True):
                    set_page("Histori Prediksi")
                    st.rerun()

            df_hist = get_all_predictions()

            if not df_hist.empty:
                tot_pred = len(df_hist)
                tot_distress = len(df_hist[df_hist["z_cls"] == "distress"])
                tot_user_pred = len(df_hist[df_hist["username"] != "admin"])
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Prediksi Masuk", tot_pred)
                m2.metric("Analisis dari User", tot_user_pred)
                m3.metric("Kasus Distress", tot_distress)
                m4.metric("Tingkat Risiko", f"{(tot_distress/tot_pred)*100:.1f}%")

                st.markdown("---")
                col_filt, col_dl = st.columns([2, 1.2])
                with col_filt:
                    chosen_user = st.selectbox(
                        "Saring Berdasarkan Pengguna:",
                        ["Semua Akun"] + sorted(list(df_hist["username"].dropna().unique())),
                        key="admin_hist_filter"
                    )
                with col_dl:
                    csv_data = df_hist.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Unduh Seluruh Log (CSV)",
                        csv_data,
                        "rekap_riwayat_prediksi.csv",
                        "text/csv",
                        use_container_width=True
                    )

                df_filtered = df_hist if chosen_user == "Semua Akun" else df_hist[df_hist["username"] == chosen_user]
                st.dataframe(df_filtered, use_container_width=True, hide_index=True)

                st.markdown("##### 🛠️ Tindakan Moderasi dan Audit")
                act_col1, act_col2 = st.columns(2)
                with act_col1:
                    st.markdown("**🔍 Audit: Muat Analisis User ke Sesi Admin**")
                    inspect_opts = {
                        f"ID {r['id']} | {r['ticker']} ({r['company']}, {r['year']}) by @{r['username']}": r
                        for _, r in df_filtered.iterrows()
                    }
                    selected_inspect = st.selectbox("Pilih data untuk diperiksa:", list(inspect_opts.keys()), key="inspect_pred_select")
                    if st.button("Tinjau di Dashboard Admin", key="btn_inspect_pred"):
                        r_data = inspect_opts[selected_inspect]
                        st.session_state.company = str(r_data["company"])
                        st.session_state.ticker = str(r_data["ticker"])
                        st.session_state.year = int(r_data["year"])
                        st.session_state.has_analyzed = True
                        st.success(f"Analisis emiten {r_data['ticker']} oleh @{r_data['username']} berhasil dimuat ke sesi Admin! Buka menu Dashboard atau Hasil Prediksi untuk meninjau.")

                with act_col2:
                    st.markdown("**🗑️ Hapus Riwayat Analisis**")
                    del_audit_mode = st.radio(
                        "Pilihan Penghapusan:",
                        ["Hapus per ID", "💥 Hapus Semua Histori"],
                        horizontal=True,
                        key="audit_del_mode_choice"
                    )
                    if del_audit_mode == "Hapus per ID":
                        del_id = st.number_input("Masukkan ID data yang ingin dihapus:", min_value=1, step=1, key="input_del_pred_id")
                        if st.button("Hapus Entri dari Database", type="secondary", key="btn_del_pred", use_container_width=True):
                            delete_prediction_by_id(int(del_id))
                            st.warning(f"Entri prediksi ID {del_id} berhasil dihapus dari database.")
                            st.rerun()
                    else:
                        st.warning("⚠️ Perhatian: Seluruh data riwayat analisis dari semua pengguna akan dihapus secara permanen.")
                        confirm_all_audit = st.checkbox("Saya yakin ingin menghapus seluruh riwayat prediksi", key="audit_confirm_clear_all")
                        if st.button("💥 Hapus Semua Histori", type="primary", disabled=not confirm_all_audit, key="btn_del_all_pred_audit", use_container_width=True):
                            clear_all_predictions()
                            st.success("✅ Seluruh data riwayat prediksi berhasil dikosongkan.")
                            st.rerun()
            else:
                st.info("Belum ada data prediksi yang tersimpan di sistem.")

        with tab_users:
            render_admin_user_management(embedded=True)

        with tab_db:
            st.markdown("#### Status dan Konfigurasi Basis Data (Database Engine)")
            st.caption("Kelola penyimpanan data prediksi dan pengguna untuk mode pengembangan lokal maupun hosting produksi.")

            db_info = get_db_info()
            
            c_db1, c_db2 = st.columns([1.5, 1])
            with c_db1:
                with st.container(border=True):
                    is_active = "Aktif" in db_info['status']
                    status_badge_html = (
                        f"<span style='background:rgba(20,184,166,0.18);color:#2dd4bf;border:1px solid rgba(20,184,166,0.4);box-shadow:0 0 10px rgba(20,184,166,0.25);padding:4px 12px;border-radius:12px;font-weight:750;font-size:12px;'>🟢 {html.escape(db_info['status'])}</span>"
                        if is_active
                        else f"<span style='background:rgba(245,158,11,0.18);color:#fbbf24;border:1px solid rgba(245,158,11,0.4);box-shadow:0 0 10px rgba(245,158,11,0.25);padding:4px 12px;border-radius:12px;font-weight:750;font-size:12px;'>🟡 {html.escape(db_info['status'])}</span>"
                    )
                    st.markdown(f"### 🗄️ {db_info['type']}")
                    st.markdown(f"**Penyedia:** 🏢 `{db_info['provider']}`")
                    st.markdown(f"**Status:** {status_badge_html}", unsafe_allow_html=True)
                    st.markdown(f"**Koneksi/Target:** 🔗 `{db_info['url']}`")
                    st.info(f"💡 **Catatan Penyimpanan:**\n\n{db_info['notes']}")
            with c_db2:
                with st.container(border=True):
                    st.markdown("##### 📊 Statistik Data Tersimpan")
                    cnt_users = len(get_all_users())
                    cnt_preds = len(get_all_predictions())
                    st.metric("Total Pengguna Terdaftar", cnt_users)
                    st.metric("Total Riwayat Prediksi", cnt_preds)
                    if st.button("🔄 Uji dan Segarkan Koneksi DB", key="btn_refresh_db_info"):
                        st.toast("Koneksi database aktif dan responsif!", icon="✅")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### 🚀 Panduan Hosting Website dan Menghubungkan Database Cloud")
            st.markdown(
                "Aplikasi ini dirancang dengan arsitektur **Dual-Mode (Hybrid)** yang sangat fleksibel:\n\n"
                "* 💻 **Mode Lokal (Sekarang):** Otomatis menggunakan SQLite lokal (`financial_distress.db`) tanpa perlu instalasi tambahan.\n"
                "* ☁️ **Mode Hosting (Streamlit Cloud / Railway / Render):** Hubungkan ke **Supabase** atau **Neon (Serverless PostgreSQL)** agar data riwayat tidak hilang saat website di-restart."
            )

            with st.expander("📖 Panduan Langkah-demi-Langkah Koneksi Cloud Database (Gratis & Aman)", expanded=True):
                st.markdown(
                    "**1️⃣ Mengapa Perlu Cloud Database saat Hosting?**\n"
                    "* ⚠️ Di layanan hosting seperti Streamlit Community Cloud atau Render Free, server bersifat *ephemeral* (sementara). File lokal seperti SQLite akan terhapus saat server restart atau ada pembaruan kode.\n"
                    "* 🛡️ Dengan menghubungkan database Cloud seperti Neon atau Supabase, semua akun pengguna dan riwayat prediksi tersimpan permanen dan aman.\n\n"
                    "**2️⃣ Langkah Pendaftaran (100% Gratis):**\n"
                    "* 🌐 Buat akun di [Neon.tech](https://neon.tech) atau [Supabase.com](https://supabase.com).\n"
                    "* 🔑 Buat database baru, lalu salin **Connection String (URI PostgreSQL)**. Contoh:\n"
                    "`postgresql://neondb_owner:npg_xyz123@ep-cool-lake-1234.us-east-2.aws.neon.tech/neondb?sslmode=require`\n\n"
                    "**3️⃣ Cara Konfigurasi Secrets:**\n"
                    "* 💻 **Di Lokal (opsional):** Buat file `.streamlit/secrets.toml`:\n"
                    "```toml\n"
                    "DATABASE_URL = \"postgresql://neondb_owner:password@host/neondb?sslmode=require\"\n"
                    "```\n"
                    "* ☁️ **Di Streamlit Community Cloud (Hosting):** Masuk ke menu *Settings* 👉 *Secrets* pada aplikasi Anda di Streamlit Cloud, lalu masukkan baris `DATABASE_URL` yang sama. Sistem akan otomatis beralih ke PostgreSQL Cloud!"
                )

        with tab_site:
            st.markdown("#### Kontrol Kebijakan dan Komunikasi Website")
            st.caption("Administrator dapat mempublikasikan instruksi operasional langsung ke antarmuka pengguna serta mengontrol izin analisis.")
            
            announcement_text = st.text_area(
                "Pesan Instruksi / Pengumuman untuk Akun User:",
                value=config.get("system_announcement", ""),
                help="Pesan ini akan langsung muncul di bagian atas halaman input Dashboard & Analisis user."
            )
            allow_flag = st.checkbox(
                "Izinkan Pengguna Menjalankan Analisis Baru (Sistem Beroperasi)",
                value=bool(config.get("allow_user_analysis", True)),
                help="Jika dimatikan, pengguna tidak dapat menekan tombol jalankan analisis sementara Admin mengkalibrasi model."
            )

            if st.button("💾 Publikasikan Kebijakan Website", type="primary", key="btn_publish_policy"):
                config["system_announcement"] = announcement_text
                config["allow_user_analysis"] = allow_flag
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                st.session_state.config = config
                st.success("Kebijakan website dan pengumuman berhasil dipublikasikan ke halaman pengguna!")

    # ========================================================
    # HALAMAN HASIL PREDIKSI DAN ANALISIS KOMPREHENSIF
    # Menggantikan dashboard prediksi dengan hasil prediksi yang sesuai & komprehensif
    # ========================================================
    elif page in ("Hasil Prediksi", "Rasio dan Hasil Prediksi", "Rasio & Hasil Prediksi", "Rasio Keuangan", "Dashboard Prediksi"):
        section_title(
            "Hasil Prediksi dan Analisis Komprehensif",
            "Evaluasi variabel rasio X1–X5, status konsensus 3 kategori operasional, diagnosa mendalam, dan intelijen strategis finansial",
            tone="purple",
        )

        is_analyzed = bool(st.session_state.get("has_analyzed", False) and st.session_state.get("ticker"))
        is_light = is_light_theme()

        # Sinkronisasi dua arah rasio: jika berganti emiten, widget di-reset; jika widget diedit manual, r disinkronkan
        cur_emiten_key = f"{st.session_state.get('ticker')}_{st.session_state.get('year')}"
        prev_emiten_key = st.session_state.get("_prev_emiten_key_hp")
        if cur_emiten_key != prev_emiten_key:
            st.session_state._prev_emiten_key_hp = cur_emiten_key
            r_cur = st.session_state.get("ratios", {})
            for _k in ("X1", "X2", "X3", "X4", "X5"):
                st.session_state[f"input_ratio_{_k}"] = float(r_cur.get(_k, 0.0))
        else:
            if "ratios" not in st.session_state or not isinstance(st.session_state.ratios, dict):
                st.session_state.ratios = {"X1": 0.0, "X2": 0.0, "X3": 0.0, "X4": 0.0, "X5": 0.0}
            for _k in ("X1", "X2", "X3", "X4", "X5"):
                if f"input_ratio_{_k}" in st.session_state:
                    st.session_state.ratios[_k] = float(st.session_state[f"input_ratio_{_k}"])

        # Top Bar Emiten Aktif dan Navigasi Cepat (Single-Level Columns, Anti-Tertumpuk & Sisi Rapi)
        c_top_rh1, c_r_b1, c_r_b2 = st.columns([2.1, 1.15, 0.75], gap="small")
        with c_top_rh1:
            bar_em_bg = "#ffffff" if is_light else "rgba(15, 23, 42, 0.75)"
            bar_em_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
            bar_em_txt = "#334155" if is_light else "#cbd5e1"
            bar_em_name = "#0f172a" if is_light else "#ffffff"
            st.markdown(
                f"""
                <div style="background:{bar_em_bg};border:1.5px solid {bar_em_border};border-radius:10px;min-height:40px;height:auto;padding:8px 14px;margin-bottom:12px;display:flex;align-items:center;gap:10px;box-shadow:0 2px 6px rgba(15,23,42,0.04);box-sizing:border-box;">
                    <span style="font-size:16px;line-height:1;flex-shrink:0;">🏢</span>
                    <div style="font-size:12px;color:{bar_em_txt};line-height:1.35;word-break:break-word;">
                        Emiten Teranalisis: <b style="color:{bar_em_name};">{st.session_state.company or 'Belum Dipilih'} ({st.session_state.ticker or '-'})</b> • Tahun Laporan: <b style="color:#2563eb;">{st.session_state.year if is_analyzed else '-'}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_r_b1:
            if st.button("📑 Edit Data/Laporan", key="btn_goto_dl_from_rh", use_container_width=True, help="Kembali ke formulir data dan laporan keuangan"):
                set_page("Data dan Laporan Keuangan")
                st.rerun()
        with c_r_b2:
            if st.button("🏠 Buka Dashboard", key="btn_goto_dash_from_rh", use_container_width=True, help="Buka dashboard utama"):
                set_page("Dashboard")
                st.rerun()

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # Hasil Prediksi Multi-Model dan Status 3 Kategori
        xgb_thresh = float(config.get("xgb_threshold", 0.5))
        xgb_th_cfg = config.get("xgb_thresholds", {"safe": 0.35, "distress": 0.65, "cutoff": xgb_thresh})
        alt_d = float(config["altman_thresholds"]["distress"])
        alt_g = float(config["altman_thresholds"].get("grey", 2.99))
        mda_th_dict = config.get("mda_thresholds", {"distress": 0.0, "grey": 1.0, "cutoff": float(config.get("mda_threshold", 0.3844))})
        mda_d = float(mda_th_dict.get("distress", 0.0))
        mda_g = float(mda_th_dict.get("grey", mda_th_dict.get("safe", 1.0)))
        mda_cut = float(mda_th_dict.get("cutoff", config.get("mda_threshold", 0.3844)))

        if is_analyzed:
            z, z_cls, mda, mda_cls, xgb_prob, xgb_label = current_results()
            if xgb_prob is None:
                xgb_tone = "purple"
                xgb_trend = "Standby"
                xgb_note = "Model Belum Ada"
                xgb_status = "MODEL BELUM TERSEDIA"
                xgb_badge_icon = "⚪"
            else:
                if xgb_label == 1:
                    xgb_tone = "red"
                    xgb_status = "DISTRESS ZONE"
                    xgb_badge_icon = "🔴"
                    xgb_trend = f"🔴 Distress {xgb_prob*100:.1f}%"
                elif xgb_label == 2:
                    xgb_tone = "amber"
                    xgb_status = "GREY AREA"
                    xgb_badge_icon = "🟡"
                    xgb_trend = f"🟡 Waspada {xgb_prob*100:.1f}%"
                else:
                    xgb_tone = "teal"
                    xgb_status = "SAFE ZONE"
                    xgb_badge_icon = "🟢"
                    xgb_trend = f"🟢 Aman {(1-xgb_prob)*100:.1f}%"
                xgb_note = f"Safe < {xgb_th_cfg.get('safe', 0.35):.2f} | Dist > {xgb_th_cfg.get('distress', 0.65):.2f}"

            cat3 = determine_3category_status(z, z_cls, mda, mda_cls, xgb_prob, xgb_thresh=xgb_th_cfg)
            overall = cat3["status"]
            overall_tone = cat3["tone"]
            overall_trend = f"{cat3['badge_icon']} {cat3['status']}"
            overall_note = cat3["summary_note"]

            if z_cls == "distress":
                z_tone = "red"
                z_trend = "🔴 Distress Zone"
            elif z_cls in ("grey area", "grey", "waspada"):
                z_tone = "amber"
                z_trend = "🟡 Grey Area"
            else:
                z_tone = "teal"
                z_trend = "🟢 Safe Zone"
            z_note = f"Dist < {alt_d:.2f} | Safe > {alt_g:.2f}"

            if mda_cls == "distress":
                mda_tone = "red"
                mda_trend = "🔴 Distress Zone"
            elif mda_cls in ("grey area", "grey"):
                mda_tone = "amber"
                mda_trend = "🟡 Grey Area"
            else:
                mda_tone = "cyan"
                mda_trend = "🟢 Safe Zone"
            mda_note = f"Dist < {mda_d:.1f} | Safe > {mda_g:.1f}"

            c = st.columns(4)
            metric_card(c[0], "ALTMAN Z''-SCORE", f"{z:.2f}", z_note, z_tone, trend=z_trend)
            metric_card(c[1], "Z''-SCORE KOEF. BARU", f"{mda:.2f}", mda_note, mda_tone, trend=mda_trend)
            if xgb_prob is None:
                metric_card(c[2], "PREDIKSI XGBOOST", "N/A", xgb_note, xgb_tone, trend=xgb_trend)
            else:
                z_eq_val = calculate_xgb_equivalent_z_score(xgb_prob)
                xgb_card_val = f"{xgb_prob*100:.1f}% ({xgb_prob:.4f})"
                xgb_card_note = f"{xgb_note} • Eq. Z: {z_eq_val:.2f}"
                metric_card(c[2], "PREDIKSI XGBOOST", xgb_card_val, xgb_card_note, xgb_tone, trend=xgb_trend)
            metric_card(c[3], "KONSENSUS (3 KATEGORI)", overall, overall_note, overall_tone, trend=overall_trend)

            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
            if evaluate_model_concordance:
                concordance = evaluate_model_concordance(z_cls, mda_cls, xgb_label)
                render_concordance_badge(concordance)

            if evaluate_warning_factors:
                warning_factors = evaluate_warning_factors(st.session_state.financials)
                render_warning_factors_checklist(warning_factors)

            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            left, mid, right = st.columns([1.1, 1.5, 1.1])

            with left:
                with st.container(border=True):
                    section_title("Data Perusahaan", tone="blue")
                    info_table([
                        ("Nama Perusahaan", st.session_state.company or "-"),
                        ("Kode Perusahaan", st.session_state.ticker or "-"),
                        ("Sektor", st.session_state.sector or "-"),
                        ("Tahun Analisis", str(st.session_state.year)),
                        ("Tanggal Analisis", st.session_state.analysis_date),
                    ])

            with mid:
                with st.container(border=True):
                    section_title("Rasio Keuangan (Input Model)", tone="purple")
                    ratio_labels = {
                        "X1": "X1 • Modal Kerja / Total Aset",
                        "X2": "X2 • Laba Ditahan / Total Aset",
                        "X3": "X3 • EBIT / Total Aset",
                        "X4": "X4 • Ekuitas / Total Liabilitas",
                    }
                    ratio_rows = [
                        (ratio_labels.get(k, k), f"{st.session_state.ratios.get(k, 0.0):.4f}")
                        for k in ["X1", "X2", "X3", "X4"]
                    ]
                    info_table(ratio_rows)
                    cap_audit = st.session_state.get("capping_audit", {})
                    if "X4" in cap_audit:
                        st.caption(f"🛡️ *Capping X4 Aktif:* `{cap_audit['X4']['raw']:.4f}` ➔ **{cap_audit['X4']['capped']:.4f}** (Maks 3.0)")

            with right:
                with st.container(border=True):
                    status_tone = "red" if z_cls == "distress" else ("amber" if z_cls in ("grey", "waspada") else "emerald")
                    section_title("Status Financial Distress", tone=status_tone)
                    render_gauge(z, config["altman_thresholds"])
                    status_color = "#f43f5e" if z_cls == "distress" else ("#f59e0b" if z_cls in ("grey", "waspada") else "#10b981")
                    status_bg = "rgba(244, 63, 94, 0.12)" if z_cls == "distress" else ("rgba(245, 158, 11, 0.12)" if z_cls in ("grey", "waspada") else "rgba(16, 185, 129, 0.12)")
                    status_border = "rgba(244, 63, 94, 0.35)" if z_cls == "distress" else ("rgba(245, 158, 11, 0.35)" if z_cls in ("grey", "waspada") else "rgba(16, 185, 129, 0.35)")
                    st.markdown(
                        f"""
                        <div style='display:flex;justify-content:center;margin-top:6px;'>
                            <span style='background:{status_bg};border:1px solid {status_border};color:{status_color};font-weight:800;font-size:13.5px;padding:6px 20px;border-radius:999px;letter-spacing:1px;text-transform:uppercase;display:inline-flex;align-items:center;gap:7px;box-shadow:0 0 14px {status_color}25;'>
                                <span style='width:7px;height:7px;border-radius:50%;background:{status_color};box-shadow:0 0 8px {status_color};display:inline-block;'></span>
                                {z_cls.upper()}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            z, z_cls, mda, mda_cls, xgb_prob, xgb_label = 0.0, "standby", 0.0, "standby", None, 0
            overall = "STANDBY"
            c = st.columns(4)
            metric_card(c[0], "ALTMAN Z''-SCORE", "-", "Menunggu Analisis", "blue", trend="⚪ Standby")
            metric_card(c[1], "Z''-SCORE KOEF. BARU", "-", "Menunggu Analisis", "blue", trend="⚪ Standby")
            metric_card(c[2], "PREDIKSI XGBOOST", "-", "Menunggu Analisis", "blue", trend="⚪ Standby")
            metric_card(c[3], "KONSENSUS (3 KATEGORI)", "STANDBY", "Belum Dilakukan Prediksi", "blue", trend="⚪ Belum Ada Data")

            st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
            st.info("ℹ️ **Status Siaga:** Sistem Peringatan Dini, Keselarasan Model, dan Speedometer Risiko akan otomatis aktif dan terkalkulasi setelah data laporan keuangan emiten dianalisis.")

            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            left, mid, right = st.columns([1.1, 1.5, 1.1])

            with left:
                with st.container(border=True):
                    section_title("Data Perusahaan", tone="blue")
                    info_table([
                        ("Nama Perusahaan", st.session_state.company or "Belum Dipilih"),
                        ("Kode Perusahaan", st.session_state.ticker or "-"),
                        ("Sektor", st.session_state.sector or "-"),
                        ("Tahun Analisis", "-"),
                        ("Tanggal Analisis", "-"),
                    ])

            with mid:
                with st.container(border=True):
                    section_title("Rasio Keuangan (Input Model)", tone="blue")
                    ratio_labels = {
                        "X1": "X1 • Modal Kerja / Total Aset",
                        "X2": "X2 • Laba Ditahan / Total Aset",
                        "X3": "X3 • EBIT / Total Aset",
                        "X4": "X4 • Ekuitas / Total Liabilitas",
                    }
                    ratio_rows = [
                        (ratio_labels.get(k, k), "-")
                        for k in ["X1", "X2", "X3", "X4"]
                    ]
                    info_table(ratio_rows)

            with right:
                with st.container(border=True):
                    section_title("Status Financial Distress", tone="blue")
                    st.markdown(
                        """
                        <div style='text-align:center;padding:24px 10px;'>
                            <div style='font-size:32px;margin-bottom:6px;'>⏳</div>
                            <div style='font-weight:800;font-size:14px;color:#94a3b8;'>STATUS: STANDBY</div>
                            <div style='font-size:11.5px;color:#64748b;margin-top:4px;'>Gauge speedometer akan aktif setelah kalkulasi dijalankan.</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # 1. Variabel Rasio Keuangan Model (X1–X5) - Diletakkan tepat di atas bagian metode
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(99,102,241,0.18);color:#818cf8;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(99,102,241,0.3);box-shadow:0 0 12px rgba(99,102,241,0.2);">📊</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">1. Variabel Rasio Keuangan Model (X1–X5)</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Rasio keuangan yang dihitung dari pos laporan keuangan dan menjadi masukan model Altman Z'', MDA, dan XGBoost</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            r = st.session_state.ratios
            cols = st.columns(5)
            labels = {
                "X1": "Working Capital / Total Assets (WC/TA)",
                "X2": "Retained Earnings / Total Assets (RE/TA)",
                "X3": "EBIT / Total Assets (EBIT/TA)",
                "X4": "Common Stock Equity / Total Liabilities (CSE/TL)",
                "X5": "Sales / Total Assets (S/TA - Altman 1968)",
            }
            keys_list = ["X1", "X2", "X3", "X4", "X5"]
            for col, key in zip(cols, keys_list):
                with col:
                    new_val = st.number_input(
                        key,
                        value=float(r.get(key, 0.0)),
                        format="%.4f",
                        help=labels.get(key, key),
                        key=f"input_ratio_{key}"
                    )
                    r[key] = new_val
                    st.caption(labels.get(key, key))
            st.session_state.ratios = r

            if not is_analyzed:
                st.info("💡 **Status Siaga:** Belum ada data emiten yang aktif dianalisis. Anda dapat menginput rasio di atas lalu klik tombol eksekusi manual, atau impor laporan keuangan di menu Data dan Laporan Keuangan.")
                c_mb1, c_mb2 = st.columns(2)
                with c_mb1:
                    if st.button("🚀 Eksekusi Prediksi dari Rasio di Atas", key="btn_exec_manual_ratios_hp", use_container_width=True):
                        st.session_state.has_analyzed = True
                        if not st.session_state.get("ticker"):
                            st.session_state.ticker = "MANUAL"
                            st.session_state.company = "Input Rasio Manual"
                        st.rerun()
                with c_mb2:
                    if st.button("💡 Muat Data Demo (ICBP 2024)", key="btn_load_demo_from_hp_top", use_container_width=True):
                        load_demo_data_icbp()
                        st.rerun()

            cap_audit = st.session_state.get("capping_audit", {})
            if is_analyzed and "X4" in cap_audit:
                st.info(f"🛡️ **Capping Rasio X4 Aktif:** Nilai mentah $X_4$ (`{cap_audit['X4']['raw']:.4f}`) telah dibatasi menjadi **{cap_audit['X4']['capped']:.4f}** agar emiten dengan utang mendekati nol tidak mendistorsi skor Altman Z'' dan MDA.")

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📐 1. ALTMAN Z''-SCORE", "📊 2. Z''-SCORE KOEFISIEN BARU", "🤖 3. PREDIKSI XGBOOST (MACHINE LEARNING)"])

        with t1:
            st.markdown("**Metode Statistik Tradisional (Altman Z''-Score Model)**")
            st.latex(altman_formula(config["altman_coefficients"], latex=True))
            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            if is_analyzed:
                if z > alt_g:
                    z_badge = "🟢 SAFE ZONE"
                    z_kriteria = f"Z'' > {alt_g:.2f} (Zona Aman)"
                elif z >= alt_d:
                    z_badge = "🟡 GREY AREA"
                    z_kriteria = f"{alt_d:.2f} <= Z'' <= {alt_g:.2f} (Zona Abu-Abu / Waspada)"
                else:
                    z_badge = "🔴 DISTRESS ZONE"
                    z_kriteria = f"Z'' < {alt_d:.2f} (Zona Bahaya / Distress)"

                render_styled_dataframe(pd.DataFrame([[
                    f"{z:.2f}",
                    z_badge,
                    z_kriteria,
                    f"Distress < {alt_d:.2f} | Grey [{alt_d:.2f}, {alt_g:.2f}] | Safe > {alt_g:.2f}"
                ]], columns=["Nilai Z''-Score", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Batas Klasifikasi"]), is_light=is_light_theme())
            else:
                render_styled_dataframe(pd.DataFrame([[
                    "-",
                    "⏳ STANDBY",
                    "Menunggu Analisis",
                    f"Distress < {alt_d:.2f} | Grey [{alt_d:.2f}, {alt_g:.2f}] | Safe > {alt_g:.2f}"
                ]], columns=["Nilai Z''-Score", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Batas Klasifikasi"]), is_light=is_light_theme())
            st.caption(
                f"💡 *Klasifikasi 3 Kategori Standar:* "
                f"**Safe Zone** ($Z'' > {alt_g:.2f}$), **Grey Area** (${alt_d:.2f} \\le Z'' \\le {alt_g:.2f}$), dan **Distress Zone** ($Z'' < {alt_d:.2f}$). "
                f"Data emiten yang jatuh pada Grey Area tidak dipaksakan ke dalam kategori biner, melainkan diberi label pemantauan khusus."
            )

        with t2:
            st.markdown("**Z''-Score dengan Koefisien Baru (MDA Empiris BEI)**")
            st.caption(
                "Model ini mengestimasi ulang koefisien diskriminan rasio $X_1$ sampai $X_4$ "
                "berdasarkan seluruh 704 observasi perusahaan manufaktur di BEI:"
            )
            st.latex(mda_formula(config["mda_coefficients"], latex=True))
            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            if is_analyzed:
                if mda > mda_g:
                    mda_badge = "🟢 SAFE ZONE"
                    mda_kriteria = f"Z''_baru > {mda_g:.2f} (Zona Aman)"
                elif mda >= mda_d:
                    mda_badge = "🟡 GREY AREA"
                    mda_kriteria = f"{mda_d:.2f} <= Z''_baru <= {mda_g:.2f} (Zona Abu-Abu / Area Buffer)"
                else:
                    mda_badge = "🔴 DISTRESS ZONE"
                    mda_kriteria = f"Z''_baru < {mda_d:.2f} (Zona Bahaya / Distress)"

                render_styled_dataframe(pd.DataFrame([[
                    f"{mda:.2f}",
                    mda_badge,
                    mda_kriteria,
                    f"{mda_cut:.4f}",
                    f"Distress < {mda_d:.2f} | Grey [{mda_d:.2f}, {mda_g:.2f}] | Safe > {mda_g:.2f}"
                ]], columns=["Nilai Z'' Baru", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Cut-off Objektif", "Batas Rentang Zona"]), is_light=is_light_theme())
            else:
                render_styled_dataframe(pd.DataFrame([[
                    "-",
                    "⏳ STANDBY",
                    "Menunggu Analisis",
                    f"{mda_cut:.4f}",
                    f"Distress < {mda_d:.2f} | Grey [{mda_d:.2f}, {mda_g:.2f}] | Safe > {mda_g:.2f}"
                ]], columns=["Nilai Z'' Baru", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Cut-off Objektif", "Batas Rentang Zona"]), is_light=is_light_theme())
            st.caption(
                f"💡 *Penjelasan Teoretis dan Zona Operasional:* Berdasarkan nilai tengah centroid kelompok Distress "
                f"($\\bar{{Z}}_D = -2.4502$) dan Non-Distress ($\\bar{{Z}}_N = +3.2189$), diperoleh titik potong objektif "
                f"**{mda_cut:.4f}**. Rentang Grey Area dibentuk secara statistik pada interval $[{mda_d:.2f}, {mda_g:.2f}]$ "
                f"untuk menampung observasi transisi tanpa pemaksaan biner."
            )
        
        with t3:
            st.markdown("### Metode Kecerdasan Buatan (XGBoost Classifier)")
            st.caption(
                "Model XGBoost memprediksi probabilitas financial distress menggunakan **4 rasio keuangan (X1 sampai X4)** "
                "dengan pengelompokan 3 Kategori Operasional: **Safe Zone**, **Grey Area**, dan **Distress Zone**."
            )
            
            if is_analyzed:
                # Tampilkan 4 rasio input XGBoost
                c_f1, c_f2, c_f3, c_f4 = st.columns(4)
                c_f1.metric("X1 (WC/TA)", f"{st.session_state.ratios.get('X1', 0.0):.4f}")
                c_f2.metric("X2 (RE/TA)", f"{st.session_state.ratios.get('X2', 0.0):.4f}")
                c_f3.metric("X3 (EBIT/TA)", f"{st.session_state.ratios.get('X3', 0.0):.4f}")
                c_f4.metric("X4 (Equity/TL)", f"{min(float(st.session_state.ratios.get('X4', 0.0)), 3.0):.4f}")

                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

                # Dapatkan kalkulasi detail 3 kategori
                xgb_details = xgboost_predict_detailed(st.session_state.ratios, str(MODEL_PATH), threshold=xgb_th_cfg)

                if not xgb_details.get("available", False):
                    st.warning(
                        "Model XGBoost belum tersedia. Pastikan file model terlatih "
                        "tersimpan di `models/xgb_model.json` atau lakukan pelatihan di menu Pengaturan Model."
                    )
                else:
                    prob_val = xgb_details["probability"]
                    prob_safe = xgb_details["prob_non_distress"]
                    margin_val = xgb_details["margin"]
                    status_val = xgb_details["status"]
                    lbl_val = xgb_details["label"]
                    badge_icon = xgb_details.get("badge", "🟢")
                    xgb_safe_th = float(xgb_th_cfg.get("safe", 0.35))
                    xgb_dist_th = float(xgb_th_cfg.get("distress", 0.65))

                    col_gauge_xgb, col_badge_xgb = st.columns([1.15, 1.0])
                    with col_gauge_xgb:
                        st.markdown("<div style='font-size:12px;font-weight:800;color:#94a3b8;margin-bottom:6px;text-transform:uppercase;'>⏱️ Quantum Gauge Meter (Probabilitas Kebangkrutan)</div>", unsafe_allow_html=True)
                        render_quantum_gauge(prob_val, xgb_th_cfg)
                    with col_badge_xgb:
                        probability_badge(prob_val, status_val, threshold=xgb_th_cfg)

                    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
                    render_feature_importance_chart(st.session_state.ratios)
                    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

                    render_styled_dataframe(pd.DataFrame([[
                        f"{prob_val:.4f} ({prob_val*100:.2f}%)",
                        f"{prob_safe:.4f} ({prob_safe*100:.2f}%)",
                        f"{margin_val:.4f}",
                        f"Safe < {xgb_safe_th*100:.0f}% | Grey [{xgb_safe_th*100:.0f}%, {xgb_dist_th*100:.0f}%] | Distress > {xgb_dist_th*100:.0f}%",
                        f"{badge_icon} {status_val} (Label {lbl_val})"
                    ]], columns=["Probabilitas Distress P(y=1)", "Probabilitas Non-Distress P(y=0)", "Margin Log-odds (ŷ)", "Ambang Batas (3 Kategori)", "Prediksi Model"]),
                    is_light=is_light_theme())
                    
                    st.caption(
                        f"💡 *Formulasi Matematis dan Klasifikasi 3 Zona:* Margin ensemble $\\hat{{y}} = {margin_val:.4f}$ ditransformasikan "
                        f"menjadi probabilitas melalui fungsi Sigmoid: "
                        f"$$p = \\frac{{1}}{{1 + e^{{-\\hat{{y}}}}}} = \\frac{{1}}{{1 + e^{{-({margin_val:.4f})}}}} = {prob_val*100:.2f}\\%$$ "
                        f"Aturan 3 Kategori Operasional: **Safe Zone** ($P < {xgb_safe_th*100:.0f}\\%$), "
                        f"**Grey Area** (${xgb_safe_th*100:.0f}\\% \\le P \\le {xgb_dist_th*100:.0f}\\%$), dan "
                        f"**Distress Zone** ($P > {xgb_dist_th*100:.0f}\\%$). "
                        f"Probabilitas {prob_val*100:.2f}% menetapkan emiten pada **{status_val}**."
                    )
            else:
                c_f1, c_f2, c_f3, c_f4 = st.columns(4)
                c_f1.metric("X1 (WC/TA)", "-")
                c_f2.metric("X2 (RE/TA)", "-")
                c_f3.metric("X3 (EBIT/TA)", "-")
                c_f4.metric("X4 (Equity/TL)", "-")
                st.info("ℹ️ **Model XGBoost Siap:** Silakan masukkan data keuangan emiten atau klik tombol Muat Data Demo untuk melihat estimasi probabilitas kebangkrutan AI.")

        st.markdown("###")
        section_title("Perbandingan Kinerja Model Penelitian (3 Kategori Operasional)")
        alt_d_val = float(config['altman_thresholds']['distress'])
        alt_g_val = float(config['altman_thresholds'].get('grey', 2.99))

        if is_analyzed:
            alt_badge_str = "🟢 SAFE ZONE" if z_cls == "aman" else ("🟡 GREY AREA" if z_cls in ("grey area", "grey", "waspada") else "🔴 DISTRESS ZONE")
            mda_badge_str = "🟢 SAFE ZONE" if mda_cls == "aman" else ("🟡 GREY AREA" if mda_cls in ("grey area", "grey") else "🔴 DISTRESS ZONE")
            if xgb_prob is None:
                xgb_val_str = "N/A"
                xgb_thresh_str = f"Safe < {xgb_th_cfg.get('safe', 0.35)*100:.0f}% | Distress > {xgb_th_cfg.get('distress', 0.65)*100:.0f}%"
                xgb_badge_str = "⚪ MODEL BELUM TERSEDIA"
            else:
                xgb_val_str = f"{xgb_prob:.4f} ({xgb_prob*100:.2f}%)"
                xgb_thresh_str = f"Safe < {xgb_th_cfg.get('safe', 0.35)*100:.0f}% | Distress > {xgb_th_cfg.get('distress', 0.65)*100:.0f}%"
                xgb_badge_str = "🔴 DISTRESS ZONE" if xgb_label == 1 else ("🟡 GREY AREA" if xgb_label == 2 else "🟢 SAFE ZONE")

            comparison = pd.DataFrame([
                ["📐 Altman Z''-Score (Benchmark)", f"{z:.2f}", f"Distress < {alt_d_val:.2f} | Safe > {alt_g_val:.2f}", alt_badge_str, "Model Teoretis Klasik (Altman 1995/2017)"],
                ["📊 Z''-Score (Koefisien Baru)", f"{mda:.2f}", f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])", mda_badge_str, "Model Empiris Diskriminan BEI"],
                ["🤖 XGBoost Machine Learning", xgb_val_str, xgb_thresh_str, xgb_badge_str, "Model Non-Linear AI"],
            ], columns=["Pendekatan Model", "Nilai / Probabilitas", "Cut-off / Threshold (3 Zona)", "Zona Klasifikasi (3 Kategori)", "Keterangan Metodologi"])
            render_styled_dataframe(comparison, is_light=is_light_theme())

            conclusion_box(
                "Kesimpulan Analisis Komparatif (3 Kategori)",
                f"Sistem menampilkan perbandingan independen dari tiga pendekatan. Hasil konsensus sistem berada pada zona <b>{overall}</b>. "
                "Data pada Grey Area diperlakukan sebagai zona waspada/ketidakpastian tanpa pemaksaan biner, memberikan wawasan analitis yang lebih mendalam untuk pengambilan keputusan manajerial dan investasi."
            )

            st.markdown("###")
            save_col1, save_col2 = st.columns([2.5, 1.5])
            with save_col1:
                st.caption("💾 **Dokumentasikan Hasil:** Simpan analisis emiten ini ke database riwayat untuk audit dan dokumentasi.")
            with save_col2:
                if st.button("Simpan ke Riwayat Prediksi", key="btn_save_pred_hp", use_container_width=True):
                    save_prediction_to_db(
                        st.session_state.username,
                        st.session_state.company,
                        st.session_state.ticker,
                        int(st.session_state.year),
                        z, z_cls, mda, mda_cls, xgb_prob or 0.0
                    )
                    st.success("✅ Hasil analisis berhasil disimpan ke basis data riwayat!")
        else:
            comparison = pd.DataFrame([
                ["📐 Altman Z''-Score (Benchmark)", "-", f"Distress < {alt_d_val:.2f} | Safe > {alt_g_val:.2f}", "⏳ STANDBY", "Model Teoretis Klasik (Altman 1995/2017)"],
                ["📊 Z''-Score (Koefisien Baru)", "-", f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])", "⏳ STANDBY", "Model Empiris Diskriminan BEI"],
                ["🤖 XGBoost Machine Learning", "-", f"Safe < {xgb_th_cfg.get('safe', 0.35)*100:.0f}% | Distress > {xgb_th_cfg.get('distress', 0.65)*100:.0f}%", "⏳ STANDBY", "Model Non-Linear AI"],
            ], columns=["Pendekatan Model", "Nilai / Probabilitas", "Cut-off / Threshold (3 Zona)", "Zona Klasifikasi (3 Kategori)", "Keterangan Metodologi"])
            render_styled_dataframe(comparison, is_light=is_light_theme())

            conclusion_box(
                "Kesimpulan Analisis Komparatif (3 Kategori)",
                "Sistem saat ini dalam status siaga (Standby). Belum ada emiten yang dianalisis. Silakan masukkan data laporan keuangan atau muat data demo untuk melihat evaluasi multi-model secara langsung."
            )
            st.caption("ℹ️ Tombol simpan ke basis data riwayat akan aktif setelah analisis emiten dijalankan.")

        st.markdown("---")
        section_title(
            "💡 Intelijen Finansial & Analisis Keputusan (Beyond Prediction)",
            "Peralatan analisis strategis bagi Investor, Analis Kredit, dan Manajemen: Diagnosa akar masalah, radar solvabilitas, rekomendasi aksi nyata, simulator what-if, dan memorandum investasi"
        )

        if not is_analyzed:
            with st.container(border=True):
                st.info("💡 **Intelijen Finansial & Analisis Keputusan Siaga:** Seluruh instrumen evaluasi lanjutan (Analisis Investor Saham, Mitigasi Kreditur Perbankan, Diagnosa Titik Kritis, Radar Solvabilitas & Arus Kas, Panduan Stakeholder, Simulator 'What-If', dan Memorandum Eksekutif) akan otomatis aktif dan terkalkulasi setelah data laporan keuangan emiten dianalisis.")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("💡 Muat Data Demo (ICBP 2024)", key="btn_load_demo_from_hp_beyond", use_container_width=True):
                        load_demo_data_icbp()
                        st.rerun()
                with col_c2:
                    if st.button("📑 Input Data Laporan Keuangan", key="btn_goto_dl_from_hp_beyond", use_container_width=True):
                        set_page("Data & Laporan Keuangan")
                        st.rerun()
        else:
            drivers = diagnose_distress_drivers(st.session_state.ratios, config["altman_coefficients"], config["altman_thresholds"])
            adv_metrics = calculate_advanced_metrics(st.session_state.financials)
            resilience = evaluate_financial_resilience(z, z_cls, mda, mda_cls, xgb_prob, adv_metrics)
            recommendations = generate_stakeholder_recommendations(z, z_cls, xgb_prob, drivers, adv_metrics, st.session_state.financials)
            breakeven = calculate_distress_breakeven(st.session_state.financials, config["altman_coefficients"], config["altman_thresholds"])
            equity_analysis = analyze_equity_investor(z, z_cls, mda, mda_cls, xgb_prob, st.session_state.ratios, st.session_state.financials)
            lender_analysis = analyze_lender_creditor(z, z_cls, mda, mda_cls, xgb_prob, st.session_state.ratios, st.session_state.financials)

            tab_intel_eq, tab_intel_cred, tab_intel1, tab_intel2, tab_intel3, tab_intel4, tab_intel5 = st.tabs([
                "📈 1. Khusus Investor Saham",
                "🏦 2. Khusus Kreditur & Perbankan",
                "🩺 3. Diagnosa Akar Masalah",
                "📊 4. Radar Solvabilitas & Arus Kas",
                "🎯 5. Panduan Stakeholder",
                "🧪 6. Simulator 'What-If'",
                "📑 7. Memorandum Eksekutif",
            ])

            with tab_intel_eq:
                st.markdown("#### 📈 Analisis Keputusan Strategis: Investor Saham (Equity Investors)")
                st.caption("Evaluasi posisi investasi taktis, kepatuhan legal dividen, serta deteksi risiko dilusi modal akibat Rights Issue diskon atau Debt-to-Equity swap.")
                render_equity_investor_dashboard(equity_analysis)

            with tab_intel_cred:
                st.markdown("#### 🏦 Penilaian Risiko Kreditur & Lembaga Perbankan (Lenders & Creditors)")
                st.caption("Mitigasi risiko kredit bermasalah (NPL), penetapan kebijakan plafon, pengetatan klausul covenants kontraktual, serta mekanisme pengamanan agunan dan cash sweep.")
                render_lender_creditor_dashboard(lender_analysis)

            with tab_intel1:
                st.markdown("#### 🩺 Dekomposisi Faktor & Diagnosa Titik Kritis")
                st.caption("Mengetahui rasio mana yang menjadi beban penyeret skor (bottleneck) dan rasio mana yang menjadi penopang utama kesehatan perusahaan.")

                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    st.error(f"**🚨 Faktor Penekan Terberat (Worst Driver):**\n\n**{drivers['worst_driver_label']}** (Kontribusi: `{drivers['contributions'][drivers['worst_driver']]:+.2f}` poin)")
                with c_d2:
                    st.success(f"**🛡️ Faktor Penopang Terkuat (Best Driver):**\n\n**{drivers['best_driver_label']}** (Kontribusi: `{drivers['contributions'][drivers['best_driver']]:+.2f}` poin)")

                render_factor_chart(drivers)

                st.markdown("##### Rincian Analisis Komprehensif Masing-Masing Rasio:")
                for item in drivers["findings"]:
                    sev_icon = "🚨" if item["severity"] == "KRITIS" else ("⚠️" if item["severity"] in ("WASPADA", "Waspada") else "✅")
                    with st.expander(f"{sev_icon} [{item['severity']}] {item['name']} (Nilai: {item['value']:.4f} | Kontribusi: {item['contribution']:+.2f} poin)", expanded=(item["severity"] == "KRITIS")):
                        st.markdown(f"**Analisis Dampak Finansial:**\n{item['analysis']}")
                        st.info(f"💡 **Rekomendasi Tindakan Korektif:**\n{item['recommendation']}")

            with tab_intel2:
                st.markdown("#### 📊 Indeks Ketahanan Finansial Komposit & Rasio Pelengkap")
                st.caption("Analisis menyeluruh mencakup likuiditas jangka pendek, beban bunga (ICR), struktur utang (DER), dan arus kas operasional.")

                render_resilience_card(resilience)

                st.markdown("##### 🔍 6 Rasio Kunci Likuiditas, Arus Kas & Produktivitas")
                g1, g2, g3 = st.columns(3)
                g4, g5, g6 = st.columns(3)
                grid_cols = [g1, g2, g3, g4, g5, g6]
                metric_keys = ["current_ratio", "icr", "der", "ocf_to_liab", "roa", "npm"]

                for col, m_key in zip(grid_cols, metric_keys):
                    m_info = adv_metrics.get(m_key, {})
                    with col:
                        val = m_info.get("val")
                        val_disp = f"{val:.2f}{m_info.get('unit', '')}" if val is not None else "N/A"
                        status = m_info.get("status", "N/A")
                        if status == "Aman":
                            status_badge = "<span style='padding:3px 8px;border-radius:8px;background:rgba(20,184,166,0.18);color:#2dd4bf;border:1px solid rgba(20,184,166,0.35);font-size:10.5px;font-weight:800;'>🟢 AMAN</span>"
                            card_bg = "linear-gradient(135deg, rgba(20, 184, 166, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)"
                            card_border = "rgba(20, 184, 166, 0.35)"
                            card_num_color = "#2dd4bf"
                        elif status in ("WASPADA", "Waspada"):
                            status_badge = "<span style='padding:3px 8px;border-radius:8px;background:rgba(245,158,11,0.18);color:#fbbf24;border:1px solid rgba(245,158,11,0.35);font-size:10.5px;font-weight:800;'>🟡 WASPADA</span>"
                            card_bg = "linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)"
                            card_border = "rgba(245, 158, 11, 0.35)"
                            card_num_color = "#fbbf24"
                        elif status in ("Bahaya", "BAHAYA"):
                            status_badge = "<span style='padding:3px 8px;border-radius:8px;background:rgba(244,63,94,0.18);color:#fb7185;border:1px solid rgba(244,63,94,0.35);font-size:10.5px;font-weight:800;'>🔴 BAHAYA</span>"
                            card_bg = "linear-gradient(135deg, rgba(244, 63, 94, 0.14) 0%, rgba(15, 23, 42, 0.85) 100%)"
                            card_border = "rgba(244, 63, 94, 0.35)"
                            card_num_color = "#fb7185"
                        else:
                            status_badge = "<span style='padding:3px 8px;border-radius:8px;background:rgba(148,163,184,0.14);color:#cbd5e1;border:1px solid rgba(148,163,184,0.25);font-size:10.5px;font-weight:800;'>⚪ N/A</span>"
                            card_bg = "rgba(15, 23, 42, 0.8)"
                            card_border = "rgba(255, 255, 255, 0.08)"
                            card_num_color = "#f8fafc"

                        with st.container(border=True):
                            st.markdown(
                                f"""
                                <div style="background:{card_bg};border:1px solid {card_border};border-radius:14px;padding:12px 14px;margin-bottom:8px;box-shadow:0 4px 16px rgba(0,0,0,0.35);backdrop-filter:blur(10px);">
                                    <div style="display:flex;justify-content:space-between;align-items:center;">
                                        <span style="font-size:12px;font-weight:750;color:#cbd5e1;">{html.escape(m_info.get('name', m_key))}</span>
                                        {status_badge}
                                    </div>
                                    <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:8px;">
                                        <div style="font-size:24px;font-weight:900;color:{card_num_color};font-family:'JetBrains Mono', monospace;text-shadow:0 0 12px {card_num_color}40;">
                                            {val_disp}
                                        </div>
                                        <span style="font-size:13px;color:{card_num_color};">↗</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            st.caption(f"Tolok Ukur: **{m_info.get('benchmark', '-')}** • {m_info.get('desc', '')}")

            with tab_intel3:
                st.markdown("#### 🎯 Matriks Panduan Tindakan Strategis Multi-Stakeholder")
                st.caption("Bukan sekadar label distress/aman, berikut adalah rekomendasi aksi nyata yang dapat langsung diterapkan oleh berbagai pihak berkepentingan:")

                render_recommendation_card(
                    "Bagi Investor Saham (Equity Investors)",
                    recommendations["investor"]["stance"],
                    recommendations["investor"]["points"],
                    recommendations["investor"]["tone"]
                )

                render_recommendation_card(
                    "Bagi Kreditur & Lembaga Perbankan (Lenders / Banks)",
                    recommendations["kreditur"]["stance"],
                    recommendations["kreditur"]["points"],
                    recommendations["kreditur"]["tone"]
                )

                render_recommendation_card(
                    "Bagi Manajemen Emiten & Dewan Direksi (Corporate Turnaround)",
                    recommendations["manajemen"]["stance"],
                    recommendations["manajemen"]["points"],
                    recommendations["manajemen"]["tone"]
                )

            with tab_intel4:
                st.markdown("#### 🧪 Simulator Skenario 'What-If' & Uji Sensitivitas Ketahanan")
                st.caption("Simulasikan skenario pemulihan (*turnaround*) atau tekanan pasar (*stress test*) untuk melihat dampaknya terhadap skor kesehatan keuangan secara interaktif.")

                if breakeven.get("available"):
                    st.markdown("##### 🎯 Target Pemulihan Laba Usaha (Break-Even Distress Point)")
                    curr_ebit = breakeven["current_ebit"]
                    req_distress = breakeven["required_ebit_exit_distress"]
                    req_safe = breakeven["required_ebit_safe"]
                    b_c1, b_c2, b_c3 = st.columns(3)
                    b_c1.metric("EBIT Saat Ini", f"Rp {int(curr_ebit):,}" if abs(curr_ebit) >= 1000 else f"Rp {curr_ebit:,.2f}")
                    b_c2.metric("Target Keluar Distress (Z'' > 1.10)", f"Rp {int(req_distress):,}" if abs(req_distress) >= 1000 else f"Rp {req_distress:,.2f}", f"Gap: {int(breakeven['gap_to_exit_distress']):,}")
                    b_c3.metric("Target Zona Aman (Z'' > 2.60)", f"Rp {int(req_safe):,}" if abs(req_safe) >= 1000 else f"Rp {req_safe:,.2f}", f"Gap: {int(breakeven['gap_to_safe']):,}")
                    st.markdown("---")

                st.markdown("##### 🎛️ Masukkan Parameter Simulasi Interaktif:")
                sc_col1, sc_col2 = st.columns(2)
                with sc_col1:
                    sim_ebit_pct = st.slider("Perubahan Laba Operasi (EBIT) (%):", -50.0, 150.0, 0.0, 5.0, help="Simulasikan kenaikan/penurunan penjualan dan laba operasional.")
                    sim_wc_boost = st.number_input("Tambahan Modal Kerja Bersih (Rp):", value=0.0, step=100000000.0, help="Contoh: Percepatan penagihan piutang atau penambahan kas.")
                with sc_col2:
                    sim_debt_pay = st.number_input("Pelunasan Utang (Deleveraging) (Rp):", value=0.0, step=100000000.0, help="Pengurangan total kewajiban pinjaman berbunga.")
                    sim_eq_inject = st.number_input("Suntikan Ekuitas / Modal Baru (Rp):", value=0.0, step=100000000.0, help="Penerbitan saham baru (Rights Issue / Private Placement).")

                sim_res = simulate_what_if(
                    st.session_state.financials,
                    config["altman_coefficients"],
                    config["altman_thresholds"],
                    delta_ebit_pct=sim_ebit_pct,
                    debt_reduction_nominal=sim_debt_pay,
                    working_capital_boost=sim_wc_boost,
                    equity_injection=sim_eq_inject,
                    base_ratios=st.session_state.ratios,
                )

                res_c1, res_c2, res_c3 = st.columns(3)
                res_c1.metric("Skor Z'' Semula", f"{sim_res['z_orig']:.2f}", sim_res['z_cls_orig'].upper())
                res_c2.metric("Skor Z'' Hasil Simulasi", f"{sim_res['z_sim']:.2f}", f"Delta: {sim_res['delta_z']:+.2f}", delta_color="normal")
                res_c3.metric("Status Klasifikasi Baru", sim_res['z_cls_sim'].upper(), "Status Berubah! 🎉" if sim_res['status_changed'] else "Status Tetap")

                if sim_res["improved"]:
                    st.success(f"📈 Skenario ini berhasil menaikkan skor Altman Z'' sebesar **{sim_res['delta_z']:+.2f} poin** (dari {sim_res['z_orig']:.2f} menjadi **{sim_res['z_sim']:.2f}**).")
                elif sim_res["delta_z"] < 0:
                    st.warning(f"📉 Skenario tekanan ini menurunkan skor Altman Z'' sebesar **{sim_res['delta_z']:.2f} poin**.")

            with tab_intel5:
                st.markdown("#### 📑 Memorandum Analisis Eksekutif dan Unduh Laporan")
                st.caption("Dokumen ringkasan terstruktur standar komite investasi (Investment Committee Memo) siap pakai untuk rapat direksi atau pertimbangan portofolio.")

                memo_markdown = generate_executive_memo_text(
                    st.session_state.company,
                    st.session_state.ticker,
                    int(st.session_state.year),
                    z,
                    z_cls,
                    mda,
                    mda_cls,
                    xgb_prob,
                    resilience,
                    drivers,
                    adv_metrics,
                    recommendations,
                    equity_analysis=equity_analysis,
                    lender_analysis=lender_analysis,
                )

                st.download_button(
                    "📥 Unduh Executive Investment Memo (.md)",
                    memo_markdown.encode("utf-8"),
                    file_name=f"Executive_Memo_{st.session_state.ticker}_{st.session_state.year}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    type="primary",
                )

                with st.container(border=True):
                    st.markdown(memo_markdown)
        
    elif page in ("Perbandingan dan Evaluasi Model", "Perbandingan & Evaluasi Model", "Perbandingan Hasil", "Evaluasi Model"):
        section_title("Perbandingan Hasil dan Evaluasi Model", "Komparasi metodologis multi-model dan matriks evaluasi validasi empiris BEI", tone="blue")

        is_light = is_light_theme()
        is_analyzed = bool(st.session_state.get("has_analyzed", False) and st.session_state.get("ticker"))

        # Top Bar Emiten Aktif dan Navigasi Cepat (Single-Level Columns, Anti-Tertumpuk & Sisi Rapi)
        c_ph_em, c_ph_b1, c_ph_b2 = st.columns([2.1, 1.15, 0.75], gap="small")
        with c_ph_em:
            bar_em_bg = "#ffffff" if is_light else "rgba(15, 23, 42, 0.75)"
            bar_em_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
            bar_em_txt = "#334155" if is_light else "#cbd5e1"
            bar_em_name = "#0f172a" if is_light else "#ffffff"
            st.markdown(
                f"""
                <div style="background:{bar_em_bg};border:1.5px solid {bar_em_border};border-radius:9px;min-height:38px;height:38px;padding:0 14px;margin-bottom:0;display:flex;align-items:center;gap:10px;box-shadow:0 2px 6px rgba(15,23,42,0.04);box-sizing:border-box;">
                    <span style="font-size:16px;line-height:1;flex-shrink:0;">🏢</span>
                    <div style="font-size:12px;color:{bar_em_txt};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        Emiten Teranalisis: <b style="color:{bar_em_name};">{st.session_state.company or 'Belum Dipilih'} ({st.session_state.ticker or '-'})</b> • Periode: <b style="color:#2563eb;">{st.session_state.year if is_analyzed else '-'}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_ph_b1:
            if st.button("📈 Rasio dan Hasil Prediksi", key="btn_goto_rh_from_pe", use_container_width=True, help="Buka halaman rasio dan hasil prediksi"):
                set_page("Rasio dan Hasil Prediksi")
                st.rerun()
        with c_ph_b2:
            if st.button("🏠 Buka Dashboard", key="btn_goto_dash_from_pe", use_container_width=True, help="Kembali ke dashboard utama"):
                set_page("Dashboard")
                st.rerun()

        cmp_tabs = st.tabs([
            "📊 Komparasi Output Multi-Model (Altman vs MDA vs XGBoost)",
            "🎯 Evaluasi Model dan Metrik Performa AI (Fitur No. 6)",
            "🔬 Validasi Empiris dan Matriks Evaluasi BEI"
        ])

        with cmp_tabs[0]:
            xgb_thresh = float(config.get("xgb_threshold", 0.5))
            xgb_th_cfg = config.get("xgb_thresholds", {"safe": 0.35, "distress": 0.65, "cutoff": xgb_thresh})
            alt_d_val = float(config['altman_thresholds']['distress'])
            alt_g_val = float(config['altman_thresholds'].get('grey', 2.99))
            mda_th_dict = config.get("mda_thresholds", {"distress": 0.0, "grey": 1.0, "cutoff": float(config.get("mda_threshold", 0.3844))})
            mda_d_val = float(mda_th_dict.get("distress", 0.0))
            mda_g_val = float(mda_th_dict.get("grey", mda_th_dict.get("safe", 1.0)))

            if is_analyzed:
                z, z_cls, mda, mda_cls, xgb_prob, xgb_label = current_results()
                cat3 = determine_3category_status(z, z_cls, mda, mda_cls, xgb_prob, xgb_thresh=xgb_th_cfg)
                alt_badge_str = "🟢 SAFE ZONE" if z_cls == "aman" else ("🟡 GREY AREA" if z_cls in ("grey area", "grey", "waspada") else "🔴 DISTRESS ZONE")
                mda_badge_str = "🟢 SAFE ZONE" if mda_cls == "aman" else ("🟡 GREY AREA" if mda_cls in ("grey area", "grey") else "🔴 DISTRESS ZONE")
                if xgb_prob is None:
                    xgb_val_str = "N/A"
                    xgb_thresh_str = f"Safe < {xgb_th_cfg.get('safe', 0.35)*100:.0f}% | Distress > {xgb_th_cfg.get('distress', 0.65)*100:.0f}%"
                    xgb_badge_str = "⚪ BELUM ADA MODEL"
                    xgb_konsensus_str = "N/A"
                else:
                    xgb_z_eq = calculate_xgb_equivalent_z_score(xgb_prob)
                    xgb_val_str = f"{xgb_prob*100:.2f}% ({xgb_prob:.4f}) • Eq. Z: {xgb_z_eq:.2f}"
                    xgb_thresh_str = f"Safe < {xgb_th_cfg.get('safe', 0.35)*100:.0f}% | Distress > {xgb_th_cfg.get('distress', 0.65)*100:.0f}%"
                    xgb_badge_str = "🔴 DISTRESS ZONE" if xgb_label == 1 else ("🟡 GREY AREA" if xgb_label == 2 else "🟢 SAFE ZONE")
                    xgb_konsensus_str = "Distress Zone" if xgb_label == 1 else ("Grey Area" if xgb_label == 2 else "Safe Zone")

                with st.container(border=True):
                    df = pd.DataFrame({
                        "Pendekatan Model": ["📐 Altman Z''-Score (Benchmark)", "📊 Z''-Score (Koefisien Baru)", "🤖 XGBoost Machine Learning"],
                        "Nilai / Probabilitas": [
                            f"{z:.2f}",
                            f"{mda:.2f}",
                            xgb_val_str
                        ],
                        "Batas / Threshold (3 Zona)": [
                            f"Distress < {alt_d_val:.2f} | Safe > {alt_g_val:.2f}",
                            f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d_val:.1f}, {mda_g_val:.1f}])",
                            xgb_thresh_str
                        ],
                        "Zona Klasifikasi (3 Kategori)": [
                            alt_badge_str,
                            mda_badge_str,
                            xgb_badge_str
                        ],
                        "Status Konsensus": [
                            "Distress Zone" if z_cls == "distress" else ("Grey Area" if z_cls in ("grey", "grey area", "waspada") else "Safe Zone"),
                            "Distress Zone" if mda_cls == "distress" else ("Grey Area" if mda_cls in ("grey", "grey area") else "Safe Zone"),
                            xgb_konsensus_str
                        ],
                        "Keterangan Metodologi": [
                            "Model Teoretis Baku (Altman 1995/2017)",
                            "Model Empiris Diskriminan BEI",
                            "Model AI Non-Linear"
                        ]
                    })
                    render_styled_dataframe(df, is_light=is_light_theme())

                    box_kons_bg = "#ffffff" if is_light else "rgba(30, 41, 59, 0.7)"
                    box_kons_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
                    box_kons_txt = "#1e293b" if is_light else "#cbd5e1"
                    st.markdown(
                        f"""
                        <div style="background:{box_kons_bg};border:1.5px solid {box_kons_border};border-radius:10px;padding:10px 14px;margin-top:12px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;box-shadow:0 2px 6px rgba(15,23,42,0.04);">
                            <span style="font-size:13px;color:{box_kons_txt};font-weight:750;">🎯 Status Konsensus 3 Kategori Terintegrasi:</span>
                            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:12.5px;font-weight:800;background:{cat3['color']}22;color:{cat3['color']};border:1px solid {cat3['color']}55;">
                                {cat3['badge_icon']} {cat3['status']} • {cat3['summary_note']}
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
                    col_radar_cmp, col_bar_cmp = st.columns([1.1, 1.0])
                    with col_radar_cmp:
                        st.markdown("##### 🎯 Radar Konvergensi Multidimensi")
                        st.caption("Pemetaan komparatif profil rasio keuangan emiten terhadap batas aman benchmark industri.")
                        render_radar_chart(st.session_state.ratios)
                    with col_bar_cmp:
                        st.markdown("##### 📊 Distribusi Skor Antar-Metode")
                        st.caption("Perbandingan terkalibrasi skor statistik dan probabilitas inferensi machine learning.")
                        render_score_distribution_chart(z, mda, xgb_prob, key_suffix="perbandingan", config=config)

            else:
                xgb_thresh_str = f"Safe < {xgb_th_cfg.get('safe', 0.35)*100:.0f}% | Distress > {xgb_th_cfg.get('distress', 0.65)*100:.0f}%"
                with st.container(border=True):
                    df = pd.DataFrame({
                        "Pendekatan Model": ["📐 Altman Z''-Score (Benchmark)", "📊 Z''-Score (Koefisien Baru)", "🤖 XGBoost Machine Learning"],
                        "Nilai / Probabilitas": ["-", "-", "-"],
                        "Batas / Threshold (3 Zona)": [
                            f"Distress < {alt_d_val:.2f} | Safe > {alt_g_val:.2f}",
                            f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d_val:.1f}, {mda_g_val:.1f}])",
                            xgb_thresh_str
                        ],
                        "Zona Klasifikasi (3 Kategori)": ["⏳ STANDBY", "⏳ STANDBY", "⏳ STANDBY"],
                        "Status Konsensus": ["Belum Dianalisis", "Belum Dianalisis", "Belum Dianalisis"],
                        "Keterangan Metodologi": [
                            "Model Teoretis Baku (Altman 1995/2017)",
                            "Model Empiris Diskriminan BEI",
                            "Model AI Non-Linear"
                        ]
                    })
                    render_styled_dataframe(df, is_light=is_light_theme())

                    box_kons_bg = "#ffffff" if is_light else "rgba(30, 41, 59, 0.7)"
                    box_kons_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
                    box_kons_txt = "#1e293b" if is_light else "#cbd5e1"
                    st.markdown(
                        f"""
                        <div style="background:{box_kons_bg};border:1.5px solid {box_kons_border};border-radius:10px;padding:10px 14px;margin-top:12px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;box-shadow:0 2px 6px rgba(15,23,42,0.04);">
                            <span style="font-size:13px;color:{box_kons_txt};font-weight:750;">🎯 Status Konsensus 3 Kategori Terintegrasi:</span>
                            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:20px;font-size:12.5px;font-weight:800;background:rgba(100,116,139,0.15);color:#64748b;border:1px solid rgba(100,116,139,0.3);">
                                ⏳ STANDBY • Menunggu Analisis Data Emiten
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
                    st.info("ℹ️ **Grafik & Radar Siaga:** Radar konvergensi multidimensi dan grafik distribusi skor akan aktif secara otomatis setelah data laporan keuangan emiten dianalisis.")

            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
            box_teor_bg = "#ffffff" if is_light else "rgba(30, 41, 59, 0.7)"
            box_teor_border = "#bfdbfe" if is_light else "rgba(56, 189, 248, 0.35)"
            box_teor_title = "#0f172a" if is_light else "#f8fafc"
            box_teor_sub = "#334155" if is_light else "#94a3b8"
            box_teor_badge_bg = "#eff6ff" if is_light else "rgba(56, 189, 248, 0.18)"
            box_teor_badge_border = "#bfdbfe" if is_light else "rgba(56, 189, 248, 0.35)"
            box_teor_badge_txt = "#2563eb" if is_light else "#38bdf8"
            st.markdown(
                f"""
                <div style="background: {box_teor_bg}; border: 1.5px solid {box_teor_border}; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(15,23,42,0.04);">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div style="font-size:22px;">🏛️</div>
                            <div>
                                <div style="font-size:15px; font-weight:850; color:{box_teor_title};">
                                    Komparasi Teoretis: Altman Z-Score 1968 (5 Variabel Asli) vs Altman Z''-Score 1995/2017 (4 Variabel Revisi)
                                </div>
                                <div style="font-size:12px; color:{box_teor_sub};">
                                    Rujukan Formula: Altman 1968 (Original 5-Variable) dan Altman 1995 (Emerging Market 4-Variable)
                                </div>
                            </div>
                        </div>
                        <span style="background: {box_teor_badge_bg}; border: 1px solid {box_teor_badge_border}; color: {box_teor_badge_txt}; font-size: 11px; font-weight: 750; padding: 3px 10px; border-radius: 20px;">
                            Formula Benchmark
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if is_analyzed:
                if altman_1968_score:
                    z_1968, z_1968_cls = altman_1968_score(st.session_state.ratios)
                else:
                    z_1968, z_1968_cls = 0.0, "N/A"
                z_1968_disp = f"{z_1968:.2f}"
                cls_badge_68 = "<span style='color:#f87171;font-weight:800;'>🔴 DISTRESS</span>" if z_1968_cls == "distress" else ("<span style='color:#fbbf24;font-weight:800;'>🟡 GREY AREA</span>" if z_1968_cls == "grey area" else "<span style='color:#34d399;font-weight:800;'>🟢 AMAN</span>")
                z_95_disp = f"{z:.2f}"
                cls_badge_95 = "<span style='color:#f87171;font-weight:800;'>🔴 DISTRESS</span>" if z_cls == "distress" else ("<span style='color:#fbbf24;font-weight:800;'>🟡 GREY AREA</span>" if z_cls in ("grey", "waspada") else "<span style='color:#34d399;font-weight:800;'>🟢 AMAN</span>")
            else:
                z_1968_disp = "-"
                cls_badge_68 = "<span style='color:#64748b;font-weight:800;'>⏳ STANDBY</span>"
                z_95_disp = "-"
                cls_badge_95 = "<span style='color:#64748b;font-weight:800;'>⏳ STANDBY</span>"

            c_alt1, c_alt2 = st.columns(2)
            with c_alt1:
                with st.container(border=True):
                    st.markdown("##### 🏛️ Model Altman Asli 1968 (5 Variabel)")
                    st.caption("Didesain awal untuk perusahaan manufaktur go public di AS:")
                    st.latex(r"Z = 1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 0.999 X_5")
                    st.markdown(f"**Skor Z (1968):** `{z_1968_disp}` &nbsp;|&nbsp; **Klasifikasi:** {cls_badge_68}", unsafe_allow_html=True)
                    st.caption("Batas Klasifikasi Baku: Safe (> 2.99), Grey (1.81 - 2.99), Distress (< 1.81)")

            with c_alt2:
                with st.container(border=True):
                    st.markdown("##### 📐 Model Revisi Altman Z'' 1995/2017 (4 Variabel)")
                    st.caption("Disesuaikan untuk Pasar Berkembang / Emerging Market:")
                    st.latex(r"Z'' = 6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4")
                    st.markdown(f"**Skor Z'' (1995):** `{z_95_disp}` &nbsp;|&nbsp; **Klasifikasi:** {cls_badge_95}", unsafe_allow_html=True)
                    st.caption("Batas Klasifikasi: Safe (> 2.60), Grey (1.10 - 2.60), Distress (<= 1.10)")

                st.caption(
                    "💡 **Rasional Ilmiah Eliminasi Variabel $X_5$ (Total Sales / Total Assets):** "
                    "Dalam metodologi keuangan dijelaskan bahwa variabel perputaran penjualan ($X_5$) dieliminasi "
                    "dalam formula Altman Z''-Score 1995/2017 guna meminimalkan efek distorsi ukuran aset (*asset size*) "
                    "serta perbedaan karakteristik perputaran penjualan antar-subsektor industri manufaktur di pasar berkembang (*emerging market*) seperti Bursa Efek Indonesia (BEI)."
                )

        with cmp_tabs[1]:
            active_ratios = st.session_state.get("ratios", {})
            curr_split_sz = float(st.session_state.get("eval_split_ratio", 0.20))
            cur_tr_pct = int(round((1.0 - curr_split_sz) * 100))
            cur_ts_pct = int(round(curr_split_sz * 100))

            eval_metrics_data = get_xgboost_evaluation_metrics(
                active_ratios=active_ratios,
                config=config,
                test_size=curr_split_sz,
            ) if get_xgboost_evaluation_metrics else {}

            # Kontrol latih ulang model dan status dataset
            c_eval_head1, c_eval_head2 = st.columns([3, 1.2])
            with c_eval_head1:
                st.caption(f"Validasi diuji menggunakan 704 observasi laporan keuangan emiten manufaktur BEI dengan porsi evaluasi aktif: **{cur_tr_pct}% Data Latih** dan **{cur_ts_pct}% Data Uji** (stratified split bersih tanpa target leakage).")
            with c_eval_head2:
                if st.button("🔄 Latih Ulang & Evaluasi Live", key="btn_retrain_eval_combined", use_container_width=True, help="Melatih ulang model pada dataset aktual dan memperbarui seluruh metrik evaluasi multi-model"):
                    with st.spinner("Melatih ulang model XGBoost dan menghitung metrik evaluasi multi-model..."):
                        if get_xgboost_evaluation_metrics:
                            eval_metrics_data = get_xgboost_evaluation_metrics(
                                force_retrain=True,
                                active_ratios=active_ratios,
                                config=config,
                                test_size=curr_split_sz,
                            )
                        st.toast(f"Model berhasil dilatih ulang pada porsi evaluasi {cur_tr_pct}/{cur_ts_pct}!", icon="✅")
                        st.rerun()

            render_model_evaluation_dashboard(
                eval_metrics_data,
                config=config,
                active_session_ratios=active_ratios,
            )

        with cmp_tabs[2]:
            st.markdown("#### 🔬 Validasi Empiris & Matriks Kebijakan Pasar Modal (BEI)")
            st.caption("Perbandingan komparatif efektivitas model pada data uji independen industri manufaktur Bursa Efek Indonesia:")

            df_val_summary = pd.DataFrame([
                {"Pendekatan Model": "📐 Altman Z''-Score (1995)", "Akurasi Empiris": "80.85%", "Kekuatan": "Sangat mudah dihitung manual", "Kelemahan": "Asumsi linear kaku, sensitif terhadap outlier utang", "Rekomendasi": "Skrining awal cepat"},
                {"Pendekatan Model": "📊 Z''-Score Koefisien Baru (MDA)", "Akurasi Empiris": "86.52%", "Kekuatan": "Dikalibrasi khusus BEI (704 observasi)", "Kelemahan": "Tidak menangkap interaksi rasio non-linear", "Rekomendasi": "Benchmark statistik lokal"},
                {"Pendekatan Model": "🤖 XGBoost Machine Learning", "Akurasi Empiris": "91.49% (AUC 0.9426)", "Kekuatan": "Menangkap pola non-linear & interaksi kompleks", "Kelemahan": "Memerlukan pipeline komputasi", "Rekomendasi": "Peringatan dini (Early Warning)"},
            ])
            st.dataframe(df_val_summary, use_container_width=True, hide_index=True)

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
            conclusion_box(
                "Relevansi Evaluasi bagi Pengujian Skripsi & Analisis Pasar Modal",
                "Dalam konteks prediksi <i>financial distress</i> di pasar modal, meminimalkan <b>Type II Error (False Negative)</b> "
                "adalah prioritas tertinggi karena kegagalan mendeteksi perusahaan yang terancam bangkrut berakibat fatal bagi kreditur dan investor. "
                "Dengan perolehan <b>Akurasi realistis ~91.5%</b> dan <b>AUC-ROC 0.9426</b> pada data uji independen yang bebas data leakage, model XGBoost terbukti superior dibandingkan model statistik linear "
                "(Altman Z'' 80.85% & MDA 86.52%) dalam menangkap dinamika rasio keuangan non-linear di Bursa Efek Indonesia (BEI)."
            )

    # ========================================================
    # INTEGRASI API TAHUN: PASAR MODAL DAN LAPORAN KEUANGAN BEI
    # ========================================================
    elif page in ("Integrasi API (Tahun)", "Integrasi API Tahun", "Integrasi API Pasar"):
        section_title(
            "Integrasi API dan Laporan Keuangan Tahunan (BEI / IDX)",
            "Pencarian emiten, penarikan data laporan keuangan multi-tahun otomatis, seleksi periode tahun pelaporan, dan sinkronisasi model",
            tone="blue",
        )

        # 1. PENCARIAN DAN KONTROL API
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(59,130,246,0.18);color:#60a5fa;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(59,130,246,0.3);box-shadow:0 0 12px rgba(59,130,246,0.2);">🌐</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">Pencarian dan Penarikan Data Pasar Modal</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Terhubung dengan feed Yahoo Finance (.JK) dan basis data emiten Bursa Efek Indonesia</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_search_t, col_search_btn = st.columns([3, 1.2])
            with col_search_t:
                search_ticker = st.text_input(
                    "Kode Saham Emiten IDX (Ticker)",
                    value=st.session_state.get("api_selected_ticker", st.session_state.ticker or "TLKM"),
                    placeholder="Contoh: ICBP, INDF, ASII, UNVR, KLBF, SMGR, AUTO, TLKM",
                    key="api_page_ticker_search_input",
                ).strip().upper()
            with col_search_btn:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                btn_do_fetch = st.button("🚀 Tarik Data Laporan Keuangan (API)", type="primary", use_container_width=True, key="api_page_btn_fetch")

            api_picked = render_emiten_shortcuts("page_api")
            if api_picked:
                search_ticker = api_picked
                st.session_state.api_selected_ticker = api_picked
                st.session_state.ticker = api_picked
                btn_do_fetch = True

        # Proses fetching jika tombol ditekan atau jika data belum pernah ditarik
        target_ticker_clean = FinancialAPIClient.clean_ticker(search_ticker)
        
        if btn_do_fetch and target_ticker_clean:
            def _do_fetch_api_page():
                return FinancialAPIClient.fetch_emiten_profile_and_financials(target_ticker_clean)

            try:
                fetched_res = run_animated_loading_process(
                    task_name="Pengambilan Live Data Bursa via Multi-Source API",
                    target_info=f"Ticker: {target_ticker_clean} (Multi-Tahun & Neraca L/R)",
                    task_type="api",
                    execute_fn=_do_fetch_api_page,
                    success_title=f"Data Emiten {target_ticker_clean} Berhasil Diunduh!",
                    success_desc="Profil korporasi dan riwayat multi-tahun berhasil disinkronkan dari bursa.",
                )
                st.session_state.api_emiten_data = fetched_res
                st.session_state.api_selected_ticker = target_ticker_clean
                source_tag = fetched_res.get("source", "Multi-Source Pipeline")
                st.toast(f"Data {fetched_res['company']} berhasil ditarik via {source_tag}!", icon="✅")
            except Exception as e:
                render_api_error_feedback(e, target_ticker_clean)

        # Jika belum ada data sama sekali, coba load default emiten manufaktur ICBP (atau TLKM)
        if st.session_state.get("api_emiten_data") is None:
            try:
                st.session_state.api_emiten_data = FinancialAPIClient.fetch_emiten_profile_and_financials("ICBP")
                st.session_state.api_selected_ticker = "ICBP"
            except Exception:
                try:
                    st.session_state.api_emiten_data = FinancialAPIClient.fetch_emiten_profile_and_financials("TLKM")
                except Exception:
                    pass

        api_data = st.session_state.get("api_emiten_data")

        if api_data:
            # 2. PROFIL PERUSAHAAN DAN REAL-TIME MARKET STATS
            with st.container(border=True):
                c_prof1, c_prof2 = st.columns([2.5, 1.5])
                with c_prof1:
                    st.markdown(
                        f"""
                        <div style="font-size:22px;font-weight:900;color:#f8fafc;letter-spacing:-0.3px;">
                            {api_data.get('company', 'Nama Perusahaan')} <span style="font-size:16px;color:#818cf8;font-weight:750;">({api_data.get('ticker')}.JK)</span>
                        </div>
                        <div style="font-size:13px;color:#94a3b8;margin-top:4px;">
                            🏢 Sektor: <b style="color:#e2e8f0;">{api_data.get('sector', '-')}</b> &nbsp;|&nbsp; 
                            🏭 Industri: <b style="color:#e2e8f0;">{api_data.get('industry', '-')}</b> &nbsp;|&nbsp; 
                            💵 Mata Uang: <b style="color:#e2e8f0;">{api_data.get('currency', 'IDR')}</b>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c_prof2:
                    source_str = api_data.get("source", "Multi-Source Feed")
                    time_str = api_data.get("retrieved_at", "Baru saja")
                    st.markdown(
                        f"""
                        <div style="text-align:right;">
                            <span style="display:inline-block;padding:4px 10px;border-radius:12px;background:rgba(20,184,166,0.15);color:#2dd4bf;font-size:11.5px;font-weight:750;border:1px solid rgba(20,184,166,0.3);">
                                🟢 Terintegrasi: {source_str}
                            </span>
                            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">Diperbarui: {time_str}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                trace = api_data.get("provider_trace", [])
                if trace:
                    with st.expander("🔍 Rincian Jejak Multi-Source Pipeline (Fallback Trace)", expanded=False):
                        for t_step in trace:
                            st.caption(f"• {t_step}")

                if api_data.get("year_fallback_note"):
                    st.info(f"💡 {api_data['year_fallback_note']}")

                if api_data.get("is_financial_sector", False):
                    st.warning(
                        "⚠️ **Deteksi Sektor Finansial / Perbankan:** Emiten ini termasuk sektor perbankan. "
                        "Neraca bank tidak memiliki akun modal kerja (*Working Capital*) lancar konvensional. "
                        "Model Altman Z'' dan MDA manufaktur tidak dirancang untuk memprediksi distress sektor perbankan."
                    )

                st.markdown("<div style='margin:10px 0 14px 0;border-top:1px solid rgba(255, 255, 255, 0.08);'></div>", unsafe_allow_html=True)

                # Metric Cards Pasar
                m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns(5)
                price_val = api_data.get("current_price", 0.0)
                mcap_val = api_data.get("market_cap", 0.0)
                pe_val = api_data.get("pe_ratio")
                pbv_val = api_data.get("pbv_ratio")
                div_val = api_data.get("dividend_yield")

                with m_c1:
                    st.metric("Harga Saham", f"Rp {price_val:,.0f}" if price_val else "-")
                with m_c2:
                    st.metric("Kapitalisasi Pasar", f"Rp {mcap_val/1e12:,.2f} T" if mcap_val else "-")
                with m_c3:
                    st.metric("Rasio P/E (TTM)", f"{pe_val:.2f}x" if pe_val else "-")
                with m_c4:
                    st.metric("Rasio P/BV", f"{pbv_val:.2f}x" if pbv_val else "-")
                with m_c5:
                    st.metric("Dividend Yield", f"{div_val*100:.2f}%" if div_val else "-")

            # 3. KONTROL PERIODE TAHUN
            available_years = api_data.get("years", [2024])
            if not available_years:
                available_years = [2024]

            c_yr_select, c_yr_sync = st.columns([2.5, 1.5])
            with c_yr_select:
                selected_view_year = st.radio(
                    "📅 Pilih Tahun Laporan Keuangan untuk Dianalisis dan Dilihat Detailnya:",
                    options=available_years,
                    format_func=lambda y: f"Tahun {y} {'(Terbaru)' if y == available_years[0] else ''}",
                    horizontal=True,
                    key="api_view_year_radio",
                )
            with c_yr_sync:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                btn_load_to_session = st.button(
                    "📥 Terapkan Data Ini ke Sesi Utama dan Simpan",
                    type="primary",
                    use_container_width=True,
                    help="Memasukkan seluruh pos keuangan tahun terpilih ke model prediksi aktif dan mencatatnya ke basis data.",
                    key="btn_apply_api_to_session"
                )

            # Ambil data keuangan untuk tahun terpilih
            fin_year_data = api_data["financials_by_year"].get(selected_view_year, {})
            evidence_year = api_data.get("mapping_evidence", {}).get(selected_view_year, {})

            if btn_load_to_session:
                st.session_state.company = api_data["company"]
                st.session_state.ticker = api_data["ticker"]
                st.session_state.year = int(selected_view_year)
                st.session_state.sector = api_data["sector"]
                
                fin_active = st.session_state.get("financials", {})
                fin_year_data = dict(fin_year_data)
                fin_year_data["report_year"] = int(selected_view_year)
                fin_year_data["ticker"] = api_data["ticker"]

                # Pastikan interest_expense tidak 0 atau hilang
                if float(fin_year_data.get("interest_expense", 0.0) or 0.0) == 0.0:
                    t_u = str(api_data["ticker"]).upper()
                    m_e = MOCK_IDX_DATA.get(t_u, {})
                    m_f = m_e.get("financials_by_year", {}).get(int(selected_view_year), {}) or m_e.get("financials_by_year", {}).get(2024, {})
                    if m_f and float(m_f.get("interest_expense", 0.0) or 0.0) > 0:
                        fin_year_data["interest_expense"] = float(m_f["interest_expense"])
                    elif float(fin_year_data.get("total_debt", 0.0) or 0.0) > 0:
                        fin_year_data["interest_expense"] = float(fin_year_data["total_debt"]) * 0.058
                    elif float(fin_year_data.get("total_liabilities", 0.0) or 0.0) > 0:
                        fin_year_data["interest_expense"] = float(fin_year_data["total_liabilities"]) * 0.038

                fin_active.update(fin_year_data)
                st.session_state.financials = fin_active

                # Sinkronkan nilai input form
                for k, v in fin_year_data.items():
                    if v is not None:
                        str_repr = f"{int(v)}" if isinstance(v, (int, float)) and float(v).is_integer() else (f"{v:.4f}" if isinstance(v, float) else str(v))
                        st.session_state[f"user_input_{k}"] = str_repr
                        st.session_state[f"manual_{k}"] = str_repr

                # Khusus interest_expense: pastikan string terisi di session_state
                ie_val = fin_year_data.get("interest_expense")
                if ie_val is not None:
                    str_ie = f"{int(ie_val)}" if isinstance(ie_val, (int, float)) and float(ie_val).is_integer() else str(ie_val)
                    st.session_state["user_input_interest_expense"] = str_ie
                    st.session_state["manual_interest_expense"] = str_ie

                st.session_state["manual_report_year"] = int(selected_view_year)
                st.session_state["user_input_report_year"] = str(selected_view_year)
                st.session_state["admin_manual_report_year_input"] = int(selected_view_year)

                try:
                    set_ratios_from_financials(fin_active)
                    st.session_state.has_analyzed = True
                    z_now, z_cls_now, mda_now, mda_cls_now, xgb_prob_now, _ = current_results()
                    save_prediction_to_db(
                        st.session_state.username,
                        st.session_state.company,
                        st.session_state.ticker,
                        int(st.session_state.year),
                        z_now, z_cls_now, mda_now, mda_cls_now, xgb_prob_now or 0.0
                    )
                    st.success(f"🎉 Data {api_data['company']} ({api_data['ticker']}) tahun {selected_view_year} berhasil diterapkan ke sesi utama dan disimpan ke database!")
                except Exception as e:
                    st.warning(f"Data diterapkan, namun kalkulasi rasio memiliki catatan: {e}")

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

            # 4. TABBED INTERFACE DETIL DATA DAN MODEL
            tab_fin, tab_audit, tab_val, tab_pred, tab_trend = st.tabs([
                "📋 Laporan Keuangan (Neraca dan Laba Rugi)",
                "🗺️ Pemetaan Pos Akuntansi (Data Engineering)",
                "🔬 Uji Validasi Rekapitulasi BEI (Otomatis)",
                "⚡ Pratinjau Model Prediksi Langsung",
                "📈 Tren Multi-Tahun (Historical Comparison)",
            ])

            with tab_fin:
                st.markdown(f"#### Rincian Pos Keuangan Emiten Tahun {selected_view_year} (Mata Uang: {api_data.get('currency', 'IDR')})")
                
                col_bs, col_is = st.columns(2)
                with col_bs:
                    with st.container(border=True):
                        st.markdown("<div style='font-size:15px;font-weight:800;color:#60a5fa;margin-bottom:8px;'>🏛️ Neraca (Balance Sheet)</div>", unsafe_allow_html=True)
                        bs_items = [
                            ("Total Aset (Total Assets)", fin_year_data.get("total_assets", 0.0)),
                            ("Aset Lancar (Current Assets)", fin_year_data.get("current_assets", 0.0)),
                            ("Total Liabilitas (Total Liabilities)", fin_year_data.get("total_liabilities", 0.0)),
                            ("Liabilitas Jangka Pendek (Current Liabilities)", fin_year_data.get("current_liabilities", 0.0)),
                            ("Modal Kerja Bersih (Working Capital = CA − CL)", fin_year_data.get("working_capital", 0.0)),
                            ("Ekuitas Saham Biasa (Common Stock Equity)", fin_year_data.get("common_stock_equity", 0.0)),
                            ("Laba Ditahan (Retained Earnings)", fin_year_data.get("retained_earnings", 0.0)),
                            ("Total Utang Berbunga (Total Debt)", fin_year_data.get("total_debt", 0.0)),
                        ]
                        df_bs = pd.DataFrame([
                            {
                                "Pos Neraca": name,
                                "Nilai Penuh (Rp)": f"Rp {int(val):,}" if val and val != 0 else ("Rp 0" if val == 0 else "-"),
                                "Dalam Triliun/Miliar": f"Rp {val/1e12:,.2f} T" if abs(val) >= 1e12 else (f"Rp {val/1e9:,.2f} M" if abs(val) >= 1e9 else "-")
                            }
                            for name, val in bs_items
                        ])
                        st.dataframe(df_bs, use_container_width=True, hide_index=True)

                with col_is:
                    with st.container(border=True):
                        st.markdown("<div style='font-size:15px;font-weight:800;color:#34d399;margin-bottom:8px;'>📊 Laba Rugi & Arus Kas (Income & Cash Flow)</div>", unsafe_allow_html=True)
                        is_items = [
                            ("Pendapatan Usaha (Total Revenue)", fin_year_data.get("total_revenue", 0.0)),
                            ("EBIT (Laba Sebelum Bunga & Pajak / Laba Usaha)", fin_year_data.get("ebit", 0.0)),
                            ("Beban Bunga & Keuangan (Interest Expense)", fin_year_data.get("interest_expense", 0.0)),
                            ("Laba Bersih Entitas Induk (Net Income)", fin_year_data.get("net_income", 0.0)),
                            ("Arus Kas Bersih Operasi (Operating Cash Flow)", fin_year_data.get("operating_cash_flow", 0.0)),
                        ]
                        df_is = pd.DataFrame([
                            {
                                "Pos Laba Rugi / Arus Kas": name,
                                "Nilai Penuh (Rp)": f"Rp {int(val):,}" if val and val != 0 else ("Rp 0" if val == 0 else "-"),
                                "Dalam Triliun/Miliar": f"Rp {val/1e12:,.2f} T" if abs(val) >= 1e12 else (f"Rp {val/1e9:,.2f} M" if abs(val) >= 1e9 else "-")
                            }
                            for name, val in is_items
                        ])
                        st.dataframe(df_is, use_container_width=True, hide_index=True)

            with tab_audit:
                st.markdown("#### Audit & Verifikasi Pemetaan Pos Akuntansi (Data Engineering)")
                st.caption(
                    "Tabel di bawah memperlihatkan bagaimana nama akun resmi pada API penyedia dipetakan secara terstandarisasi "
                    "ke dalam 15 variabel proyek prediksi (*VARIABLE_SCHEMA*)."
                )

                audit_rows = []
                for item in VARIABLE_SCHEMA:
                    k = item["key"]
                    val = fin_year_data.get(k)
                    val_str = format_display_value(k, val)
                    ev = evidence_year.get(k, {})
                    matched_alias = ev.get("matched_alias", "Default / Tidak Ada di Feed")
                    is_found = ev.get("is_found", False)

                    status_label = "✅ Ditemukan & Dipetakan" if is_found else ("⚡ Dihitung Formula" if "Kalkulasi" in str(matched_alias) else "⚠️ Nilai Default (0)")
                    
                    audit_rows.append({
                        "Kode": item["code"],
                        "Variabel Proyek": item["label"],
                        "Nilai Terisi": val_str,
                        "Pos Asal pada Feed API": matched_alias,
                        "Status Verifikasi": status_label,
                        "Fungsi Model": item["used_by"],
                    })

                st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)

            with tab_val:
                st.markdown(f"#### 🔬 Uji Validasi Rekapitulasi Historis BEI & Metodologi Skripsi")
                st.caption(
                    "Pemeriksaan otomatis konsistensi data finansial hasil penarikan API terhadap tolok ukur rekapitulasi resmi BEI "
                    "(Lampiran Skripsi: ADES, AALI, ICBP, KICI) serta audit koherensi akuntansi internal dan status capping rasio."
                )

                # Siapkan data keuangan & rasio terkap
                temp_fin_val = complete_financial_values(fin_year_data)
                temp_ratios_val = build_features_from_financials(temp_fin_val)
                z_val = altman_z_score(temp_ratios_val, config["altman_coefficients"])
                z_cls_val = altman_classification(z_val, config["altman_thresholds"])
                mda_val = mda_score(temp_ratios_val, config["mda_coefficients"])
                mda_cls_val = mda_classification(mda_val, config["mda_threshold"])

                val_res = validate_financials_and_ratios(
                    ticker=api_data.get("ticker", ""),
                    year=selected_view_year,
                    financial_values=temp_fin_val,
                    calculated_ratios=temp_ratios_val,
                    altman_score=z_val,
                    altman_status=z_cls_val,
                    mda_score_val=mda_val,
                    mda_status=mda_cls_val,
                )

                # Banner Status
                if val_res["benchmark_found"]:
                    if val_res["is_valid"]:
                        st.success(f"✅ **DATA TERSINKRONISASI 100%:** {val_res['summary']}")
                    else:
                        st.warning(f"⚠️ **TERDAPAT CATATAN SINKRONISASI:** {val_res['summary']}")
                else:
                    st.info(f"🛡️ **UJI KOHERENSI INTERNAL:** {val_res['summary']}")

                # Metric Cards for Validation
                v_col1, v_col2, v_col3 = st.columns(3)
                with v_col1:
                    with st.container(border=True):
                        st.markdown("**Standar Sumber Data**")
                        if val_res["benchmark_found"]:
                            st.write("🏆 **Tercatat di Lampiran Proposal BEI**")
                            st.caption("Verifikasi langsung dengan Laporan Keuangan Audited")
                        else:
                            st.write("🔍 **Emiten Terdaftar Bursa (IDX)**")
                            st.caption("Verifikasi koherensi matematis akuntansi")

                with v_col2:
                    with st.container(border=True):
                        st.markdown("**Status Capping Rasio X4 (Maks 3.0)**")
                        cap_audit = val_res.get("capping_audit", {})
                        if "X4" in cap_audit:
                            st.write(f"🔒 **Capping Diterapkan:** `{cap_audit['X4']['raw']:.4f}` ➔ `{cap_audit['X4']['capped']:.4f}`")
                            st.caption(cap_audit['X4']['rule'])
                        else:
                            x4_now = temp_ratios_val.get("X4", 0.0)
                            st.write(f"✅ **Normal (Tanpa Capping):** `{x4_now:.4f}`")
                            st.caption("Nilai X4 ≤ 3.0 sesuai ambang batas skripsi hal. 41 & 95")

                with v_col3:
                    with st.container(border=True):
                        st.markdown("**Integritas Persamaan Neraca**")
                        ca_v = float(temp_fin_val.get("current_assets", 0.0) or 0.0)
                        cl_v = float(temp_fin_val.get("current_liabilities", 0.0) or 0.0)
                        wc_v = float(temp_fin_val.get("working_capital", 0.0) or 0.0)
                        if abs(wc_v - (ca_v - cl_v)) < 1.0:
                            st.write("✅ **100% Presisi (WC = CA − CL)**")
                            st.caption(f"Modal Kerja = Rp {wc_v:,.0f}")
                        else:
                            st.write("⚠️ **Terdapat Penyesuaian**")
                            st.caption(f"WC: {wc_v} vs CA-CL: {ca_v - cl_v}")

                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                st.markdown("##### 📊 Tabel Hasil Pengujian Validitas Komprehensif")
                df_val = pd.DataFrame(val_res["validation_rows"])
                st.dataframe(df_val, use_container_width=True, hide_index=True)

                with st.expander("ℹ️ Penjelasan Ilmiah Capping & Verifikasi Data (Proposal Skripsi Hal. 41, 95 & Lampiran)"):
                    st.markdown("""
                    1. **Koreksi Pemetaan Akuntansi**:
                       - $X_1 = \\frac{Current\\ Assets - Current\\ Liabilities}{Total\\ Assets}$. Modal kerja ($WC$) wajib dihitung dari selisih aset lancar dan liabilitas lancar tanpa perkiraan buatan.
                       - $X_2 = \\frac{Retained\\ Earnings}{Total\\ Assets}$. Laba ditahan diambil dari pos ekuitas resmi.
                       - $X_3 = \\frac{EBIT}{Total\\ Assets}$. Menggunakan Laba Usaha / Operating Profit audited.
                       - $X_4 = \\frac{Common\\ Stock\\ Equity}{Total\\ Liabilities}$. Rasio nilai buku ekuitas terhadap total liabilitas.
                    2. **Harmonisasi Skala Satuan (Rupiah Penuh)**:
                       - Algoritma pembersih data (`normalize_financial_units`) secara otomatis mendeteksi jika pembilang atau penyebut ditarik dalam satuan berbeda (misal Rp jutaan vs Rupiah penuh) dan mengonversinya ke nominal Rupiah penuh ($10^0$).
                    3. **Penerapan Capping (Pembatasan Nilai Ekstrem)**:
                       - Sesuai standar penelitian, rasio $X_4$ dibatasi secara ketat maksimal **3.0000** (capping) tanpa menghapus baris observasi emiten dari populasi sampel.
                    4. **Validasi Empiris**:
                       - Hasil perhitungan di atas dicocokkan langsung dengan tabel rekapitulasi audited BEI (seperti ADES, AALI, ICBP, KICI) untuk memastikan nilai prediksi akhir 100% konsisten.
                    """)

            with tab_pred:
                st.markdown(f"#### Pratinjau Perhitungan Model Finansial ({api_data['company']} - {selected_view_year})")
                st.caption("Hasil komputasi langsung rasio keuangan X1–X5 beserta tiga model prediksi.")

                # Hitung rasio langsung
                try:
                    temp_fin = complete_financial_values(fin_year_data)
                    preview_ratios = build_features_from_financials(temp_fin)
                    
                    # Tampilkan metrik rasio
                    r_c1, r_c2, r_c3, r_c4, r_c5 = st.columns(5)
                    with r_c1:
                        st.metric("X1 (WC / TA)", f"{preview_ratios['X1']:.4f}", help="Working Capital / Total Assets")
                    with r_c2:
                        st.metric("X2 (RE / TA)", f"{preview_ratios['X2']:.4f}", help="Retained Earnings / Total Assets")
                    with r_c3:
                        st.metric("X3 (EBIT / TA)", f"{preview_ratios['X3']:.4f}", help="EBIT / Total Assets")
                    with r_c4:
                        st.metric("X4 (Equity / TL)", f"{min(preview_ratios['X4'], 3.0):.4f}", help="Common Stock Equity / Total Liabilities (Capped 3.0)")
                    with r_c5:
                        st.metric("X5 (Revenue / TA)", f"{preview_ratios['X5']:.4f}", help="Total Revenue / Total Assets")

                    st.markdown("<div style='margin:12px 0 16px 0;border-top:1px solid rgba(255, 255, 255, 0.08);'></div>", unsafe_allow_html=True)

                    # Model Calculations
                    z_prev = altman_z_score(preview_ratios, config["altman_coefficients"])
                    z_cls_prev = altman_classification(z_prev, config["altman_thresholds"])

                    mda_prev = mda_score(preview_ratios, config["mda_coefficients"])
                    mda_cls_prev = mda_classification(mda_prev, config["mda_threshold"])

                    xgb_prob_prev, xgb_lbl_prev = xgboost_predict(
                        preview_ratios,
                        str(MODEL_PATH) if MODEL_PATH.exists() else None,
                        threshold=config["xgb_threshold"]
                    )

                    pred_c1, pred_c2, pred_c3 = st.columns(3)
                    with pred_c1:
                        with st.container(border=True):
                            tone_z = "teal" if z_cls_prev == "aman" else ("amber" if "grey" in z_cls_prev else "red")
                            st.markdown("##### 📐 Altman Z''-Score")
                            st.metric("Nilai Z''", f"{z_prev:.2f}", delta=z_cls_prev.upper(), delta_color="normal" if z_cls_prev == "aman" else "inverse")
                            st.write(f"**Klasifikasi:** `{z_cls_prev.upper()}`")
                            st.caption(f"Cut-off: Distress ≤ {config['altman_thresholds']['distress']:.2f} | Aman > {config['altman_thresholds']['grey']:.2f}")

                    with pred_c2:
                        with st.container(border=True):
                            st.markdown("##### 📊 Z''-Score Koef. Baru (MDA)")
                            st.metric("Nilai Z'' Baru", f"{mda_prev:.2f}", delta=mda_cls_prev.upper(), delta_color="normal" if mda_cls_prev == "aman" else "inverse")
                            st.write(f"**Klasifikasi:** `{mda_cls_prev.upper()}`")
                            st.caption(f"Titik Potong Objektif BEI: {config['mda_threshold']:.4f}")

                    with pred_c3:
                        with st.container(border=True):
                            st.markdown("##### 🤖 XGBoost AI Model")
                            if xgb_prob_prev is not None:
                                xgb_stat = "DISTRESS" if xgb_lbl_prev == 1 else "NON-DISTRESS"
                                st.metric("Probabilitas Distress", f"{xgb_prob_prev*100:.2f}%", delta=xgb_stat, delta_color="inverse" if xgb_lbl_prev == 1 else "normal")
                                st.write(f"**Hasil:** `{xgb_stat}` (Kelas {xgb_lbl_prev})")
                                st.caption(f"Cut-off Ambang Batas: {config['xgb_threshold']*100:.0f}%")
                            else:
                                st.metric("Probabilitas", "N/A")
                                st.caption("Model XGBoost belum dikalibrasi.")

                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                    col_go_pred, col_go_dash = st.columns(2)
                    with col_go_pred:
                        if st.button("👉 Buka Halaman Hasil Prediksi dan Diagnosa Lengkap", type="secondary", use_container_width=True):
                            set_page("Hasil Prediksi")
                            st.rerun()
                    with col_go_dash:
                        if st.button("🏠 Buka Dashboard dan Analisis Utama", type="secondary", use_container_width=True):
                            set_page("Dashboard dan Analisis" if st.session_state.role == "user" else "Dashboard")
                            st.rerun()

                except Exception as ex:
                    st.error(f"Gagal mempratinjau kalkulasi model: {ex}")

            with tab_trend:
                st.markdown(f"#### Perbandingan Historis Kinerja Keuangan ({api_data['company']})")
                st.caption("Pergerakan Total Aset, Liabilitas, Ekuitas, Pendapatan, dan Laba Bersih lintas tahun pelaporan.")

                trend_data = []
                for yr in sorted(available_years):
                    y_fin = api_data["financials_by_year"].get(yr, {})
                    trend_data.append({
                        "Tahun": str(yr),
                        "Total Aset (Rp Triliun)": round(y_fin.get("total_assets", 0.0) / 1e12, 2),
                        "Total Liabilitas (Rp Triliun)": round(y_fin.get("total_liabilities", 0.0) / 1e12, 2),
                        "Ekuitas (Rp Triliun)": round(y_fin.get("common_stock_equity", 0.0) / 1e12, 2),
                        "Pendapatan (Rp Triliun)": round(y_fin.get("total_revenue", 0.0) / 1e12, 2),
                        "Laba Bersih (Rp Triliun)": round(y_fin.get("net_income", 0.0) / 1e12, 2),
                    })

                df_trend = pd.DataFrame(trend_data)
                st.dataframe(df_trend, use_container_width=True, hide_index=True)

                if len(df_trend) > 1:
                    chart_trend_display = df_trend.set_index("Tahun")[["Total Aset (Rp Triliun)", "Total Liabilitas (Rp Triliun)", "Ekuitas (Rp Triliun)"]]
                    st.line_chart(chart_trend_display)

    # ========================================================
    # 4. HALAMAN KHUSUS ADMIN: HISTORI PREDIKSI LENGKAP
    # ========================================================
    elif page == "Histori Prediksi":
        if st.session_state.role != "admin":
            st.error("Akses ditolak! Halaman ini hanya dapat diakses oleh Administrator.")
            st.stop()

        section_title("Histori dan Riwayat Prediksi Sistem", "Rekapitulasi lengkap hasil analisis dan prediksi financial distress dari seluruh pengguna")

        df_all = get_all_predictions()

        if df_all.empty:
            st.info("ℹ️ Belum ada riwayat prediksi yang tercatat di dalam database sistem.")
            st.caption("Setiap kali analisis dijalankan oleh Pengguna atau Administrator, data riwayat akan otomatis tersimpan di sini.")
            
            z_curr, z_cls_curr, mda_curr, mda_cls_curr, xgb_curr, _ = current_results()
            if st.button("➕ Simpan Data Analisis Sesi Aktif ke Histori", type="primary", key="btn_init_save_hist"):
                save_prediction_to_db(
                    st.session_state.username,
                    st.session_state.company,
                    st.session_state.ticker,
                    int(st.session_state.year),
                    z_curr, z_cls_curr, mda_curr, mda_cls_curr, xgb_curr or 0.0
                )
                st.success("✅ Analisis berhasil disimpan ke histori!")
                st.rerun()
        else:
            tot_pred = len(df_all)
            tot_distress = len(df_all[df_all["z_cls"] == "distress"])
            tot_safe = tot_pred - tot_distress
            unique_users = df_all["username"].nunique()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Prediksi", tot_pred)
            m2.metric("Kasus Distress", tot_distress, f"{(tot_distress/tot_pred)*100:.1f}%")
            m3.metric("Kasus Non-Distress / Grey", tot_safe, f"{(tot_safe/tot_pred)*100:.1f}%")
            m4.metric("Pengguna Berkontribusi", unique_users)

            st.markdown("---")

            # Filter dan Pencarian
            with st.container(border=True):
                st.markdown(f"<div style='font-size:13px;font-weight:800;color:{'#0f172a' if is_light_theme() else '#f8fafc'};margin-bottom:8px;'>🔍 Saring dan Pencarian Riwayat Prediksi</div>", unsafe_allow_html=True)
                f1, f2, f3 = st.columns([1.2, 1.2, 1.6])
                with f1:
                    user_options = ["Semua Pengguna"] + sorted([str(u) for u in df_all["username"].dropna().unique()])
                    selected_user = st.selectbox("Saring Berdasarkan Pengguna:", user_options, key="hist_filter_user")
                with f2:
                    status_options = ["Semua Status", "🚨 Distress", "🟢 Non-Distress / Grey"]
                    selected_status = st.selectbox("Saring Status Klasifikasi:", status_options, key="hist_filter_status")
                with f3:
                    search_kw = st.text_input("Cari Ticker atau Nama Perusahaan:", placeholder="Contoh: BBCA, Astra, dll.", key="hist_filter_search")

            # Menerapkan filter
            df_filtered = df_all.copy()
            if selected_user != "Semua Pengguna":
                df_filtered = df_filtered[df_filtered["username"] == selected_user]
            if selected_status == "🚨 Distress":
                df_filtered = df_filtered[df_filtered["z_cls"] == "distress"]
            elif selected_status == "🟢 Non-Distress / Grey":
                df_filtered = df_filtered[df_filtered["z_cls"] != "distress"]
            if search_kw.strip():
                kw = search_kw.strip().lower()
                df_filtered = df_filtered[
                    df_filtered["company"].str.lower().str.contains(kw, na=False) |
                    df_filtered["ticker"].str.lower().str.contains(kw, na=False)
                ]

            st.caption(f"Menampilkan {len(df_filtered)} dari total {tot_pred} entri riwayat.")

            tab_table, tab_charts = st.tabs(["📋 Tabel Riwayat Prediksi", "📊 Visualisasi dan Analisis"])

            with tab_table:
                df_display = df_filtered.copy()
                df_display = df_display.rename(columns={
                    "id": "ID",
                    "timestamp": "Waktu Analisis",
                    "username": "Pengguna",
                    "company": "Nama Perusahaan",
                    "ticker": "Ticker",
                    "year": "Tahun",
                    "z_score": "Altman Z''",
                    "z_cls": "Status Altman",
                    "mda_score": "MDA Score",
                    "mda_cls": "Status MDA",
                    "xgb_prob": "Prob. XGBoost"
                })
                
                if "Altman Z''" in df_display.columns:
                    df_display["Altman Z''"] = df_display["Altman Z''"].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "-")
                if "MDA Score" in df_display.columns:
                    df_display["MDA Score"] = df_display["MDA Score"].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "-")
                if "Prob. XGBoost" in df_display.columns:
                    df_display["Prob. XGBoost"] = df_display["Prob. XGBoost"].apply(lambda v: f"{v:.4f} ({v*100:.1f}%)" if pd.notna(v) and v is not None else "-")

                st.dataframe(df_display, use_container_width=True, hide_index=True)

                col_dl, col_save_curr = st.columns([1, 1])
                with col_dl:
                    csv_export = df_filtered.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Unduh Data Terfilter (CSV)",
                        csv_export,
                        "histori_prediksi_financial_distress.csv",
                        "text/csv",
                        use_container_width=True,
                    )
                with col_save_curr:
                    z_curr, z_cls_curr, mda_curr, mda_cls_curr, xgb_curr, _ = current_results()
                    if st.button("➕ Simpan Sesi Aktif Saat Ini ke Riwayat", key="btn_save_curr_hist", use_container_width=True):
                        save_prediction_to_db(
                            st.session_state.username,
                            st.session_state.company,
                            st.session_state.ticker,
                            int(st.session_state.year),
                            z_curr, z_cls_curr, mda_curr, mda_cls_curr, xgb_curr or 0.0
                        )
                        st.success("✅ Analisis sesi aktif berhasil disimpan ke riwayat!")
                        st.rerun()

                st.markdown("###")
                st.markdown("#### 🛠️ Tindakan dan Manajemen Riwayat")
                act1, act2 = st.columns(2)
                with act1:
                    st.markdown("**🔍 Tinjau: Muat Data Riwayat ke Sesi Admin**")
                    st.caption("Pilih salah satu entri riwayat untuk dimuat ke sesi aktif dan diperiksa secara detail pada menu Dashboard / Hasil Prediksi.")
                    if not df_filtered.empty:
                        inspect_dict = {
                            f"ID {r['id']} | {r['ticker']} ({r['company']}, {r['year']}) - @{r['username']}": r
                            for _, r in df_filtered.iterrows()
                        }
                        chosen_record_label = st.selectbox("Pilih Riwayat:", list(inspect_dict.keys()), key="select_inspect_record")
                        if st.button("📥 Muat Data ke Sesi", type="primary", key="btn_load_record_session"):
                            rec = inspect_dict[chosen_record_label]
                            st.session_state.company = str(rec["company"])
                            st.session_state.ticker = str(rec["ticker"])
                            st.session_state.year = int(rec["year"])
                            st.session_state.has_analyzed = True
                            st.success(f"Emiten {rec['ticker']} ({rec['company']}) berhasil dimuat ke sesi! Anda dapat melihat hasilnya di menu 'Hasil Prediksi' atau 'Dashboard'.")
                    else:
                        st.caption("Tidak ada data yang cocok dengan filter untuk dimuat.")

                with act2:
                    st.markdown("**🗑️ Hapus Riwayat Prediksi**")
                    st.caption("Pilih untuk menghapus entri spesifik atau mengosongkan seluruh riwayat.")
                    del_hist_mode = st.radio(
                        "Pilihan Penghapusan:",
                        ["Hapus per ID", "💥 Hapus Semua Histori"],
                        horizontal=True,
                        key="hist_del_mode_choice"
                    )
                    if del_hist_mode == "Hapus per ID":
                        del_id = st.number_input("ID Prediksi yang akan dihapus:", min_value=1, step=1, key="hist_del_id_input")
                        if st.button("Hapus Entri dari Database", type="secondary", key="btn_del_hist_entry", use_container_width=True):
                            delete_prediction_by_id(int(del_id))
                            st.warning(f"Entri dengan ID {del_id} telah dihapus.")
                            st.rerun()
                    else:
                        st.warning("⚠️ Perhatian: Seluruh data riwayat prediksi akan dihapus secara permanen dari basis data.")
                        confirm_clear = st.checkbox("Saya yakin ingin menghapus seluruh riwayat", key="chk_confirm_clear")
                        if st.button("💥 Hapus Semua Data Riwayat", type="primary", disabled=not confirm_clear, key="btn_clear_all_hist", use_container_width=True):
                            clear_all_predictions()
                            st.success("✅ Seluruh data riwayat prediksi berhasil dikosongkan.")
                            st.rerun()

            with tab_charts:
                st.markdown("#### Distribusi dan Proporsi Klasifikasi")
                c_chart1, c_chart2 = st.columns(2)
                with c_chart1:
                    st.markdown("**Klasifikasi Altman Z''-Score**")
                    altman_counts = df_filtered["z_cls"].str.upper().value_counts()
                    st.bar_chart(altman_counts)
                with c_chart2:
                    st.markdown("**Klasifikasi MDA Empiris**")
                    mda_counts = df_filtered["mda_cls"].str.upper().value_counts()
                    st.bar_chart(mda_counts)

                st.markdown("---")
                st.markdown("#### Rata-rata Skor per Emiten / Ticker")
                if "ticker" in df_filtered.columns and not df_filtered.empty:
                    ticker_avg = df_filtered.groupby("ticker")[["z_score", "mda_score"]].mean().reset_index()
                    st.dataframe(ticker_avg.rename(columns={"ticker": "Kode Emiten", "z_score": "Rata-rata Altman Z''", "mda_score": "Rata-rata MDA"}), use_container_width=True, hide_index=True)

    # ========================================================
    # 5. HALAMAN DEDIKASI: PENGATURAN PROFIL DAN PREFERENSI ANTARMUKA
    # Dimuat mandiri sebagai halaman terpisah dari fitur profil sidebar
    # ========================================================
    elif page in ("Pengaturan Profil", "Pengaturan Akun", "Profil", "Profile"):
        section_title("Pengaturan Profil dan Preferensi Antarmuka", "Kelola preferensi tema visual aplikasi, kredensial autentikasi pengguna, dan identitas profil resmi", tone="blue")

        current_theme = st.session_state.get("theme", "light")
        is_light = (current_theme == "light")

        header_text_color = "#0f172a" if is_light else "#ffffff"
        sub_text_color = "#334155" if is_light else "#cbd5e1"
        section_box_bg = "#f8fafc" if is_light else "rgba(15, 23, 42, 0.65)"
        section_box_border = "#e2e8f0" if is_light else "rgba(255, 255, 255, 0.12)"
        user_role_disp = "System Administrator" if st.session_state.role == "admin" else "Financial Analyst"
        cur_user = st.session_state.username if st.session_state.username else "admin"

        # Sinkronkan data dari database & session_state
        user_profile_data = get_user_profile(cur_user) or {}
        curr_fullname = st.session_state.get("user_fullname") or user_profile_data.get("full_name") or ("System Administrator" if st.session_state.role == "admin" else "")
        curr_email = st.session_state.get("user_email") or user_profile_data.get("email") or (f"{cur_user.lower()}@distress.ai" if "@" not in cur_user else cur_user)
        curr_phone = st.session_state.get("user_phone") or user_profile_data.get("phone_number", "")
        curr_inst = st.session_state.get("user_institution") or user_profile_data.get("institution", "")
        curr_type = st.session_state.get("user_type") or user_profile_data.get("user_type", "Pekerja / Profesional")
        curr_pos = st.session_state.get("user_position") or user_profile_data.get("position", "")
        curr_city = st.session_state.get("user_city") or user_profile_data.get("city", "")
        curr_bio = st.session_state.get("user_bio") or user_profile_data.get("bio", "")
        curr_avatar = st.session_state.get("user_avatar") or user_profile_data.get("avatar_data", "")

        # Top Bar Navigasi Pintasan (Single-Level Columns, Anti-Tertumpuk & Sisi Rapi)
        c_prof_nav1, c_pnav_b1, c_pnav_b2, c_pnav_b3 = st.columns([1.95, 0.65, 0.65, 0.75], gap="small")
        with c_prof_nav1:
            if curr_avatar:
                top_nav_avatar_html = f'<img src="{curr_avatar}" style="width:24px; height:24px; border-radius:50%; object-fit:cover; border:1.5px solid #2563eb; flex-shrink:0;" />'
            else:
                top_nav_avatar_html = '<span style="font-size:16px; line-height:1; flex-shrink:0;">👤</span>'

            render_clean_html(
                f"""
                <div style="background:{'#ffffff' if is_light else 'rgba(15, 23, 42, 0.75)'}; border:1.5px solid {section_box_border}; border-radius:9px; min-height:38px; height:38px; padding:0 14px; margin-bottom:0; display:flex; align-items:center; gap:10px; box-shadow:{'0 2px 6px rgba(0,0,0,0.03)' if is_light else 'none'}; box-sizing:border-box;">
                    {top_nav_avatar_html}
                    <div style="font-size:12px; color:{sub_text_color} !important; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        Profil Aktif: <b style="color:{header_text_color} !important;">{curr_fullname or cur_user} (@{cur_user})</b> • Hak Akses: <b style="color:#2563eb;">{user_role_disp}</b>
                    </div>
                </div>
                """
            )
        with c_pnav_b1:
            if st.button("🏠 Dashboard", key="btn_prof_goto_dash", use_container_width=True, help="Kembali ke Dashboard Utama"):
                set_page("Dashboard")
                st.rerun()
        with c_pnav_b2:
            if st.button("📈 Prediksi", key="btn_prof_goto_results", use_container_width=True, help="Buka Hasil Prediksi"):
                set_page("Hasil Prediksi")
                st.rerun()
        with c_pnav_b3:
            if st.button("🚪 Keluar Akun", key="btn_prof_top_single_logout", use_container_width=True, help="Keluar dari sesi login sistem"):
                logout_user()

        # KARTU UTAMA IDENTIK SEPERTI GAMBAR FITUR PROFIL
        with st.container(border=True):
            # Top Banner: User Identity Header with Rich Vibrant Status Pills (Image 1)
            th_pill_bg = "#dbeafe" if is_light else "rgba(56, 189, 248, 0.15)"
            th_pill_border = "#93c5fd" if is_light else "rgba(56, 189, 248, 0.35)"
            th_pill_col = "#1d4ed8" if is_light else "#38bdf8"
            th_pill_text = "☀️ Light Mode Aktif" if is_light else "🌙 Dark Mode Aktif"

            role_pill_bg = "#eff6ff" if is_light else "rgba(99, 102, 241, 0.15)"
            role_pill_border = "#bfdbfe" if is_light else "rgba(99, 102, 241, 0.35)"
            role_pill_col = "#2563eb" if is_light else "#818cf8"
            role_pill_text = "👑 " + user_role_disp if st.session_state.role == "admin" else "👤 " + user_role_disp

            avatar_letter = cur_user[0].upper() if cur_user else "U"
            if curr_avatar:
                banner_avatar_html = f'<img src="{curr_avatar}" style="width:46px; height:46px; border-radius:14px; object-fit:cover; border:2px solid #2563eb; box-shadow:0 4px 14px rgba(37,99,235,0.35);" />'
            else:
                banner_avatar_html = f'<div style="width:46px; height:46px; border-radius:14px; background:linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); display:flex; align-items:center; justify-content:center; color:#ffffff !important; font-weight:900; font-size:22px; box-shadow:0 4px 14px rgba(37,99,235,0.35);">{avatar_letter}</div>'

            render_clean_html(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; padding-bottom:14px; border-bottom:1.5px solid {section_box_border}; margin-bottom:16px;">
                    <div style="display:flex; align-items:center; gap:12px;">
                        {banner_avatar_html}
                        <div>
                            <div style="font-size:18px; font-weight:900; color:{header_text_color} !important; letter-spacing:-0.3px;">
                                ⚙️ Pengaturan Akun dan Preferensi Antarmuka
                            </div>
                            <div style="font-size:12px; color:{sub_text_color} !important; font-weight:650; margin-top:2px;">
                                Kelola preferensi skema warna visual aplikasi dan kredensial autentikasi pengguna
                            </div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <span style="background:{role_pill_bg}; border:1px solid {role_pill_border}; color:{role_pill_col} !important; font-size:11px; font-weight:800; padding:4px 10px; border-radius:8px;">
                            {role_pill_text}
                        </span>
                        <span style="background:{'#dcfce7' if is_light else 'rgba(16,185,129,0.2)'}; border:1px solid {'#86efac' if is_light else 'rgba(16,185,129,0.4)'}; color:{'#15803d' if is_light else '#34d399'} !important; font-size:11px; font-weight:800; padding:4px 10px; border-radius:8px;">
                            ● Sesi Online Aktif
                        </span>
                        <span style="background:{th_pill_bg}; border:1px solid {th_pill_border}; color:{th_pill_col} !important; font-size:11px; font-weight:800; padding:4px 10px; border-radius:8px;">
                            {th_pill_text}
                        </span>
                    </div>
                </div>
                """
            )

            # =============================================================
            # SEKSI 1 (PALING ATAS): 📇 KARTU IDENTITAS RESMI PENGGUNA TERVERIFIKASI
            # Menampilkan seluruh data profil yang telah diinput mandiri oleh pengguna
            # =============================================================
            disp_name = (curr_fullname if curr_fullname else cur_user).replace("$", "\\$")
            disp_email = (curr_email if curr_email else "Belum diisi").replace("$", "\\$")
            disp_phone = (curr_phone if curr_phone else "Belum diisi").replace("$", "\\$")
            disp_inst = (curr_inst if curr_inst else "Belum diisi").replace("$", "\\$")
            disp_type = (curr_type if curr_type else "Pekerja / Profesional").replace("$", "\\$")
            disp_pos = (curr_pos if curr_pos else "Belum diisi").replace("$", "\\$")
            disp_city = (curr_city if curr_city else "Belum diisi").replace("$", "\\$")
            disp_bio = (curr_bio if curr_bio else "Belum ada bio singkat profil.").replace("$", "\\$")

            card_hero_bg = "linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(56,189,248,0.03) 100%)" if is_light else "linear-gradient(135deg, rgba(30,41,59,0.7) 0%, rgba(15,23,42,0.85) 100%)"
            card_hero_border = "#bfdbfe" if is_light else "rgba(56,189,248,0.3)"
            tile_bg = "#ffffff" if is_light else "rgba(15,23,42,0.65)"
            tile_border = "#e2e8f0" if is_light else "rgba(255,255,255,0.09)"
            lbl_color = "#64748b" if is_light else "#94a3b8"
            val_color = "#0f172a" if is_light else "#f8fafc"

            if curr_avatar:
                hero_avatar_html = (
                    f'<div style="position:relative; width:92px; height:92px;">'
                    f'<img src="{curr_avatar}" style="width:92px; height:92px; border-radius:50%; object-fit:cover; border:3px solid #2563eb; box-shadow:0 6px 18px rgba(37,99,235,0.35);" />'
                    f'<span style="position:absolute; bottom:2px; right:2px; width:16px; height:16px; background:#10b981; border:2.5px solid {"#ffffff" if is_light else "#0f172a"}; border-radius:50%;" title="Online Aktif"></span>'
                    f'</div>'
                )
                photo_status_badge = '<span style="color:#10b981; font-weight:800; font-size:11px;">✓ Foto Profil Aktif</span>'
            else:
                hero_avatar_html = (
                    f'<div style="position:relative; width:92px; height:92px;">'
                    f'<div style="width:92px; height:92px; border-radius:50%; background:{"#e2e8f0" if is_light else "#1e293b"}; border:2.5px dashed {"#94a3b8" if is_light else "#475569"}; display:flex; align-items:center; justify-content:center; font-size:42px; color:{"#64748b" if is_light else "#94a3b8"};">👤</div>'
                    f'<span style="position:absolute; bottom:2px; right:2px; width:16px; height:16px; background:#10b981; border:2.5px solid {"#ffffff" if is_light else "#0f172a"}; border-radius:50%;" title="Online Aktif"></span>'
                    f'</div>'
                )
                photo_status_badge = f'<span style="color:{lbl_color}; font-weight:700; font-size:11px;">⚪ Belum Ada Foto (Siluet)</span>'

            card_html = f"""
            <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:10px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                <span style="font-size:16px;">📇</span> <span>PROFIL IDENTITAS PENGGUNA TERVERIFIKASI (EXECUTIVE PROFILE CARD)</span>
            </div>
            <div style="border:1.5px solid {card_hero_border}; background:{card_hero_bg}; border-radius:16px; padding:18px 20px; margin-bottom:18px; box-shadow:{'0 4px 18px rgba(37,99,235,0.06)' if is_light else '0 4px 20px rgba(0,0,0,0.35)'};">
                <div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap;">
                    <div style="display:flex; flex-direction:column; align-items:center; gap:6px;">
                        {hero_avatar_html}
                        {photo_status_badge}
                    </div>
                    <div style="flex:1; min-width:260px;">
                        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                            <div style="font-size:22px; font-weight:900; color:{val_color} !important; letter-spacing:-0.4px;">
                                {disp_name}
                            </div>
                            <span style="font-size:12.5px; font-weight:750; color:#2563eb !important; background:{'#eff6ff' if is_light else 'rgba(37,99,235,0.18)'}; padding:2px 8px; border-radius:6px; border:1px solid {'#bfdbfe' if is_light else 'rgba(37,99,235,0.35)'};">
                                @{cur_user}
                            </span>
                            <span style="background:{role_pill_bg}; border:1px solid {role_pill_border}; color:{role_pill_col} !important; font-size:11px; font-weight:800; padding:2px 8px; border-radius:6px;">
                                {role_pill_text}
                            </span>
                            <span style="background:{'#dcfce7' if is_light else 'rgba(16,185,129,0.2)'}; border:1px solid {'#86efac' if is_light else 'rgba(16,185,129,0.4)'}; color:{'#15803d' if is_light else '#34d399'} !important; font-size:11px; font-weight:800; padding:2px 8px; border-radius:6px;">
                                ● Sesi Aktif Online
                            </span>
                        </div>
                        <div style="font-size:12.5px; color:{lbl_color} !important; margin-top:4px; font-weight:600;">
                            Akun Terverifikasi Sistem Analisis Financial Distress • BEI Risk Intelligence Platform
                        </div>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:10px; margin-top:16px;">
                    <div style="background:{tile_bg}; border:1px solid {tile_border}; border-radius:10px; padding:10px 14px;">
                        <div style="font-size:10.5px; font-weight:750; color:{lbl_color} !important; text-transform:uppercase; letter-spacing:0.4px;">🏢 Instansi / Organisasi</div>
                        <div style="font-size:13px; font-weight:800; color:{val_color} !important; margin-top:3px;">{disp_inst}</div>
                    </div>
                    <div style="background:{tile_bg}; border:1px solid {tile_border}; border-radius:10px; padding:10px 14px;">
                        <div style="font-size:10.5px; font-weight:750; color:{lbl_color} !important; text-transform:uppercase; letter-spacing:0.4px;">🏷️ Status (Sebagai)</div>
                        <div style="font-size:13px; font-weight:800; color:#2563eb !important; margin-top:3px;">{disp_type}</div>
                    </div>
                    <div style="background:{tile_bg}; border:1px solid {tile_border}; border-radius:10px; padding:10px 14px;">
                        <div style="font-size:10.5px; font-weight:750; color:{lbl_color} !important; text-transform:uppercase; letter-spacing:0.4px;">💼 Jabatan / Divisi</div>
                        <div style="font-size:13px; font-weight:800; color:{val_color} !important; margin-top:3px;">{disp_pos}</div>
                    </div>
                    <div style="background:{tile_bg}; border:1px solid {tile_border}; border-radius:10px; padding:10px 14px;">
                        <div style="font-size:10.5px; font-weight:750; color:{lbl_color} !important; text-transform:uppercase; letter-spacing:0.4px;">✉️ Alamat Email</div>
                        <div style="font-size:13px; font-weight:800; color:{val_color} !important; margin-top:3px;">{disp_email}</div>
                    </div>
                    <div style="background:{tile_bg}; border:1px solid {tile_border}; border-radius:10px; padding:10px 14px;">
                        <div style="font-size:10.5px; font-weight:750; color:{lbl_color} !important; text-transform:uppercase; letter-spacing:0.4px;">📱 Telepon / WhatsApp</div>
                        <div style="font-size:13px; font-weight:800; color:{val_color} !important; margin-top:3px;">{disp_phone}</div>
                    </div>
                    <div style="background:{tile_bg}; border:1px solid {tile_border}; border-radius:10px; padding:10px 14px;">
                        <div style="font-size:10.5px; font-weight:750; color:{lbl_color} !important; text-transform:uppercase; letter-spacing:0.4px;">📍 Kota / Domisili</div>
                        <div style="font-size:13px; font-weight:800; color:{val_color} !important; margin-top:3px;">{disp_city}</div>
                    </div>
                </div>
                <div style="background:{tile_bg}; border:1px solid {tile_border}; border-radius:10px; padding:10px 14px; margin-top:10px;">
                    <div style="font-size:10.5px; font-weight:750; color:{lbl_color} !important; text-transform:uppercase; letter-spacing:0.4px;">📝 Catatan Singkat / Bio Profesional</div>
                    <div style="font-size:12.5px; font-style:italic; color:{val_color} !important; margin-top:3px; line-height:1.5;">"{disp_bio}"</div>
                </div>
            </div>
            """
            render_clean_html(card_html)

            st.markdown(f"<div style='height:10px; border-bottom:1.5px solid {section_box_border}; margin: 8px 0 18px 0;'></div>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # SEKSI 2: IDENTITAS PENGGUNA DAN KREDENSIAL AKSES
            # -------------------------------------------------------------
            render_clean_html(
                f"""
                <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:12px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px;">🔐</span> <span>IDENTITAS PENGGUNA DAN KREDENSIAL AKSES RESMI</span>
                </div>
                """
            )

            with st.container(border=True):
                # Subseksi A: Foto Profil Pengguna (Default Kosong / Edit Mandiri)
                render_clean_html(
                    f"""
                    <div style="font-size:12px; font-weight:800; color:{sub_text_color} !important; margin-bottom:10px; display:flex; align-items:center; gap:6px;">
                        <span>📷</span> <span>FOTO PROFIL PENGGUNA (DEFAULT KOSONG • DAPAT DIUNGGAH MANDIRI)</span>
                    </div>
                    """
                )
                col_av_prev, col_av_up = st.columns([1.1, 2.9], gap="medium")
                with col_av_prev:
                    if curr_avatar:
                        render_clean_html(
                            f"""
                            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:12px; border:1.5px solid {section_box_border}; border-radius:14px; background:{'#ffffff' if is_light else 'rgba(15, 23, 42, 0.6)'};">
                                <img src="{curr_avatar}" style="width:84px; height:84px; border-radius:50%; object-fit:cover; border:2.5px solid #2563eb; box-shadow:0 4px 14px rgba(37,99,235,0.25);" alt="Foto Profil" />
                                <span style="font-size:11px; font-weight:750; color:#10b981; margin-top:8px;">✓ Foto Aktif Terpasang</span>
                            </div>
                            """
                        )
                    else:
                        render_clean_html(
                            f"""
                            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:12px; border:1.5px dashed {section_box_border}; border-radius:14px; background:{'#ffffff' if is_light else 'rgba(15, 23, 42, 0.4)'};">
                                <div style="width:84px; height:84px; border-radius:50%; background:{'#e2e8f0' if is_light else '#1e293b'}; border:2px dashed {'#94a3b8' if is_light else '#475569'}; display:flex; align-items:center; justify-content:center; font-size:38px; color:{'#64748b' if is_light else '#94a3b8'};">
                                    👤
                                </div>
                                <span style="font-size:11px; font-weight:650; color:{sub_text_color}; margin-top:8px;">Belum Ada Foto Profil</span>
                            </div>
                            """
                        )
                with col_av_up:
                    uploaded_avatar = st.file_uploader(
                        "Unggah Foto Profil Baru (Format: JPG, PNG, WEBP — Maks. 2MB):",
                        type=["jpg", "jpeg", "png", "webp"],
                        key="uploader_user_avatar",
                        help="Pilih file foto wajah resmi Anda untuk disimpan secara persisten."
                    )
                    c_av_btn1, c_av_btn2 = st.columns([1.5, 1])
                    with c_av_btn1:
                        if uploaded_avatar is not None:
                            if st.button("🖼️ Pasang Foto Terpilih", key="btn_apply_uploaded_avatar", use_container_width=True):
                                import base64
                                file_bytes = uploaded_avatar.read()
                                if len(file_bytes) > 2 * 1024 * 1024:
                                    st.error("Ukuran file terlalu besar! Maksimal 2MB.")
                                else:
                                    mime = uploaded_avatar.type or "image/png"
                                    b64_str = base64.b64encode(file_bytes).decode("utf-8")
                                    data_uri = f"data:{mime};base64,{b64_str}"
                                    ok, msg = update_user_credentials(current_username=cur_user, new_avatar_data=data_uri)
                                    if ok:
                                        st.session_state.user_avatar = data_uri
                                        st.toast("Foto profil berhasil dipasang!", icon="✅")
                                        st.rerun()
                                    else:
                                        st.error(f"Gagal memperbarui foto: {msg}")
                    with c_av_btn2:
                        if curr_avatar:
                            if st.button("🗑️ Hapus Foto", key="btn_remove_user_avatar", use_container_width=True, help="Hapus foto profil dan kembalikan ke avatar default"):
                                ok, msg = update_user_credentials(current_username=cur_user, new_avatar_data="")
                                if ok:
                                    st.session_state.user_avatar = ""
                                    st.toast("Foto profil berhasil dikosongkan!", icon="ℹ️")
                                    st.rerun()
                                else:
                                    st.error(f"Gagal menghapus foto: {msg}")

                st.markdown(f"<div style='height:8px; border-bottom:1px dashed {section_box_border}; margin: 12px 0;'></div>", unsafe_allow_html=True)

                # Subseksi B: Kelengkapan Identitas Pengguna dan Kredensial
                # Baris 1: Username dan Password Baru
                c_ea1, c_ea2 = st.columns(2)
                with c_ea1:
                    edit_username = st.text_input("Nama Pengguna (Username)", value=cur_user, key="input_prof_username", help="Nama akun unik untuk autentikasi sistem")
                with c_ea2:
                    edit_password = st.text_input("Kata Sandi Baru (Opsional)", type="password", key="input_prof_password", help="Biarkan kosong jika tetap menggunakan kata sandi saat ini")

                # Baris 2: Nama Lengkap dan Email Resmi
                c_ea3, c_ea4 = st.columns(2)
                with c_ea3:
                    edit_fullname = st.text_input("Nama Lengkap Pengguna", value=curr_fullname, key="input_prof_fullname_val", help="Nama lengkap resmi pengguna untuk laporan dan log audit")
                with c_ea4:
                    edit_email = st.text_input("Alamat Email Resmi", value=curr_email, key="input_prof_email_val", help="Alamat email aktif untuk korespondensi dan pemulihan akun")

                # Baris 3: Nomor Telepon dan Instansi / Organisasi
                c_ea5, c_ea6 = st.columns(2)
                with c_ea5:
                    edit_phone = st.text_input("Nomor Telepon / WhatsApp", value=curr_phone, key="input_prof_phone_val", help="Nomor kontak aktif yang dapat dihubungi")
                with c_ea6:
                    edit_inst = st.text_input("Instansi / Organisasi / Lembaga / Kampus", value=curr_inst, key="input_prof_inst_val", help="Nama institusi atau lembaga tempat berafiliasi")

                # Baris 4: Sebagai (Status Kategori) dan Jabatan / Divisi / Prodi
                c_ea7, c_ea8 = st.columns(2)
                with c_ea7:
                    user_types = [
                        "Pekerja / Profesional",
                        "Mahasiswa",
                        "Dosen / Akademisi",
                        "Peneliti / Riset",
                        "Investor / Trader",
                        "Auditor / Akuntan",
                        "Konsultan Keuangan / Bisnis",
                        "Lainnya"
                    ]
                    type_idx = user_types.index(curr_type) if curr_type in user_types else 0
                    edit_type = st.selectbox("Sebagai (Status / Kategori Pengguna)", options=user_types, index=type_idx, key="input_prof_user_type_val", help="Peran atau status pengguna dalam menggunakan aplikasi")
                with c_ea8:
                    edit_pos = st.text_input("Jabatan / Divisi / Program Studi", value=curr_pos, key="input_prof_pos_val", help="Jabatan fungsional, unit divisi kantor, atau jurusan studi")

                # Baris 5: Kota / Domisili dan Bio / Catatan Singkat
                c_ea9, c_ea10 = st.columns(2)
                with c_ea9:
                    edit_city = st.text_input("Kota / Domisili", value=curr_city, key="input_prof_city_val", help="Kota domisili atau basis kantor Anda saat ini")
                with c_ea10:
                    edit_bio = st.text_area("Catatan Singkat / Bio Profesional (Opsional)", value=curr_bio, key="input_prof_bio_val", help="Deskripsi ringkas mengenai fokus analisis atau profil Anda", height=70)

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            # Baris Tombol Aksi Formulir
            col_s1, col_s2 = st.columns([1.3, 0.7])
            with col_s1:
                if st.button("💾 Simpan Perubahan Identitas dan Profil", type="primary", key="btn_save_prof_page", use_container_width=True):
                    if edit_username.strip():
                        clean_u = edit_username.strip()
                        clean_p = edit_password.strip() if edit_password else None
                        clean_f = edit_fullname.strip() if edit_fullname else ""
                        clean_e = edit_email.strip() if edit_email else ""
                        clean_phone = edit_phone.strip() if edit_phone else ""
                        clean_inst = edit_inst.strip() if edit_inst else ""
                        clean_type = edit_type.strip() if edit_type else ""
                        clean_pos = edit_pos.strip() if edit_pos else ""
                        clean_city = edit_city.strip() if edit_city else ""
                        clean_bio = edit_bio.strip() if edit_bio else ""

                        ok, msg = update_user_credentials(
                            current_username=cur_user,
                            new_username=clean_u,
                            new_password=clean_p,
                            new_email=clean_e,
                            new_full_name=clean_f,
                            new_phone_number=clean_phone,
                            new_institution=clean_inst,
                            new_user_type=clean_type,
                            new_position=clean_pos,
                            new_city=clean_city,
                            new_bio=clean_bio,
                        )
                        if ok:
                            st.session_state.username = clean_u
                            st.session_state.user_fullname = clean_f
                            st.session_state.user_email = clean_e
                            st.session_state.user_phone = clean_phone
                            st.session_state.user_institution = clean_inst
                            st.session_state.user_type = clean_type
                            st.session_state.user_position = clean_pos
                            st.session_state.user_city = clean_city
                            st.session_state.user_bio = clean_bio
                            st.toast("Informasi identitas akun dan profil berhasil disimpan!", icon="✅")
                            st.success(f"✅ {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("Nama pengguna (username) tidak boleh kosong.")
            with col_s2:
                if st.button("✕ Tutup Form", key="btn_close_prof_page", use_container_width=True, help="Tutup pengaturan dan kembali ke Dashboard"):
                    set_page("Dashboard")
                    st.rerun()

            st.markdown(f"<div style='height:14px; border-bottom:1.5px solid {section_box_border}; margin: 12px 0 16px 0;'></div>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # SEKSI 3: PREFERENSI TEMA APLIKASI (THEME SWITCHER)
            # -------------------------------------------------------------
            render_clean_html(
                f"""
                <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:12px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px;">🎨</span> <span>PREFERENSI TEMA APLIKASI (THEME SWITCHER)</span>
                </div>
                """
            )

            col_th_light, col_th_dark = st.columns(2, gap="medium")

            # --- KARTU PILIHAN TEMA 1: LIGHT MODE (BIRU DAN PUTIH) ---
            with col_th_light:
                is_light_sel = current_theme == "light"
                border_color_l = "#2563eb" if is_light_sel else ("#cbd5e1" if is_light else "rgba(255, 255, 255, 0.12)")
                bg_card_l = "#eff6ff" if is_light_sel else ("#ffffff" if is_light else "rgba(15, 23, 42, 0.5)")
                badge_l = '<span style="background:#2563eb; color:#ffffff !important; font-size:10.5px; font-weight:850; padding:3px 10px; border-radius:99px; letter-spacing:0.5px; box-shadow:0 2px 8px rgba(37,99,235,0.4);">✓ TEMA AKTIF</span>' if is_light_sel else f'<span style="color:{sub_text_color} !important; font-size:11px; font-weight:650;">Klik tombol di bawah</span>'

                render_clean_html(
                    f"""
                    <div style="border: 2px solid {border_color_l}; background: {bg_card_l}; border-radius: 16px; padding: 16px; margin-bottom: 8px; transition: all 0.25s ease; box-shadow: {'0 8px 24px rgba(37, 99, 235, 0.18)' if is_light_sel else '0 2px 8px rgba(0,0,0,0.04)'};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                            <div style="font-size:15px; font-weight:900; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                                <span>☀️</span> <span>Light Mode (Mode Terang)</span>
                            </div>
                            {badge_l}
                        </div>
                        <div style="font-size:12px; line-height:1.55; color:{sub_text_color} !important; font-weight:600; margin-bottom: 12px;">
                            Kanvas dominan <b>Putih Bersih</b> dan <b>Abu-abu Sangat Muda</b>, bilah navigasi dan tombol beraksen <b>Royal Blue</b> elegan, serta teks navy gelap berkontras tinggi (Standar WCAG AAA).
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; gap:6px; align-items:center;">
                                <span style="width:18px; height:18px; border-radius:50%; background:#ffffff; border:1.5px solid #cbd5e1; display:inline-block;" title="Putih Bersih (#ffffff)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#38bdf8; display:inline-block;" title="Sky Blue Accent (#38bdf8)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#2563eb; display:inline-block;" title="Royal Blue (#2563eb)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#0f172a; display:inline-block;" title="Dark Navy Text (#0f172a)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#10b981; display:inline-block;" title="Emerald Safe (#10b981)"></span>
                            </div>
                            <span style="font-size:11px; font-weight:800; color:#2563eb !important;">Kontras Tinggi • WCAG AAA</span>
                        </div>
                    </div>
                    """
                )
                if st.button("☀️ Aktifkan Mode Terang (Light Mode)", key="btn_page_theme_light", use_container_width=True, disabled=is_light_sel):
                    st.session_state.theme = "light"
                    st.session_state.prop_ui_theme_mode = "light"
                    st.rerun()

            # --- KARTU PILIHAN TEMA 2: DARK MODE (OBSIDIAN DAN NEON BLUE) ---
            with col_th_dark:
                is_dark_sel = current_theme == "dark"
                border_color_d = "#38bdf8" if is_dark_sel else ("#cbd5e1" if is_light else "rgba(255, 255, 255, 0.12)")
                bg_card_d = "rgba(56, 189, 248, 0.08)" if is_dark_sel else ("#ffffff" if is_light else "rgba(15, 23, 42, 0.5)")
                badge_d = '<span style="background:#0284c7; color:#ffffff !important; font-size:10.5px; font-weight:850; padding:3px 10px; border-radius:99px; letter-spacing:0.5px; box-shadow:0 2px 8px rgba(2,132,199,0.4);">✓ TEMA AKTIF</span>' if is_dark_sel else f'<span style="color:{sub_text_color} !important; font-size:11px; font-weight:650;">Klik tombol di bawah</span>'

                render_clean_html(
                    f"""
                    <div style="border: 2px solid {border_color_d}; background: {bg_card_d}; border-radius: 16px; padding: 16px; margin-bottom: 8px; transition: all 0.25s ease; box-shadow: {'0 8px 24px rgba(56, 189, 248, 0.18)' if is_dark_sel else '0 2px 8px rgba(0,0,0,0.04)'};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                            <div style="font-size:15px; font-weight:900; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                                <span>🌙</span> <span>Dark Mode (Mode Gelap)</span>
                            </div>
                            {badge_d}
                        </div>
                        <div style="font-size:12px; line-height:1.55; color:{sub_text_color} !important; font-weight:600; margin-bottom: 12px;">
                            Latar <b>Obsidian</b> dan <b>Charcoal</b> pekat yang nyaman di mata untuk sesi analisis jangka panjang, dipadukan dengan aksen pendaran <b>Neon Blue / Azure</b> lembut.
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="display:flex; gap:6px; align-items:center;">
                                <span style="width:18px; height:18px; border-radius:50%; background:#070a12; border:1px solid rgba(255,255,255,0.2); display:inline-block;" title="Obsidian Canvas (#070a12)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#111216; border:1px solid rgba(255,255,255,0.2); display:inline-block;" title="Charcoal Sidebar (#111216)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#38bdf8; display:inline-block;" title="Neon Blue Accent (#38bdf8)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#818cf8; display:inline-block;" title="Electric Indigo (#818cf8)"></span>
                                <span style="width:18px; height:18px; border-radius:50%; background:#f8fafc; display:inline-block;" title="Crisp Pearl Text (#f8fafc)"></span>
                            </div>
                            <span style="font-size:11px; font-weight:800; color:#38bdf8 !important;">Eye Comfort • Dark OLED</span>
                        </div>
                    </div>
                    """
                )
                if st.button("🌙 Aktifkan Mode Gelap (Dark Mode)", key="btn_page_theme_dark", use_container_width=True, disabled=is_dark_sel):
                    st.session_state.theme = "dark"
                    st.session_state.prop_ui_theme_mode = "dark"
                    st.rerun()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # SEKSI 4: INFORMASI SESI DAN AUDIT KEAMANAN SISTEM
        # -------------------------------------------------------------
        with st.container(border=True):
            render_clean_html(
                f"""
                <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:12px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px;">🛡️</span> <span>RINGKASAN SESI AKTIF DAN AUDIT HAK AKSES PENGGUNA</span>
                </div>
                """
            )
            col_inf1, col_inf2, col_inf3, col_inf4 = st.columns(4)
            with col_inf1:
                with st.container(border=True):
                    st.caption("Peran dan Tingkat Akses")
                    st.markdown(f"**{role_pill_text}**")
                    st.caption("Akses penuh ke seluruh model" if st.session_state.role == "admin" else "Akses analisis dan prediksi emiten")
            with col_inf2:
                with st.container(border=True):
                    st.caption("Preferensi Antarmuka")
                    st.markdown(f"**{th_pill_text}**")
                    st.caption("Palet kontras WCAG AAA")
            with col_inf3:
                with st.container(border=True):
                    db_inf = get_db_info()
                    st.caption("Mesin Basis Data")
                    st.markdown(f"**🗄️ {db_inf['type']}**")
                    st.caption(db_inf['status'])
            with col_inf4:
                with st.container(border=True):
                    st.caption("Status Sesi Analisis")
                    cnt_preds = len(get_all_predictions())
                    st.markdown(f"**📊 {cnt_preds} Prediksi Tersimpan**")
                    st.caption("Basis data riwayat audit aktif")

    # ========================================================
    # 6. HALAMAN UTAMA: DASHBOARD TERINTEGRASI (SISTEM DAN PREDIKSI)
    # Menggabungkan Dashboard Sistem dan Dashboard Prediksi dengan Status 3 Kategori
    # ========================================================
    else:
        section_title("Dashboard Pemantauan dan Analisis Risiko", tone="blue")

        is_analyzed = bool(st.session_state.get("has_analyzed", False) and st.session_state.get("ticker"))

        xgb_thresh = float(config.get("xgb_threshold", 0.5))
        xgb_th_cfg = config.get("xgb_thresholds", {"safe": 0.35, "distress": 0.65, "cutoff": xgb_thresh})
        xgb_safe_th = float(xgb_th_cfg.get("safe", 0.35))
        xgb_dist_th = float(xgb_th_cfg.get("distress", 0.65))

        alt_d = float(config["altman_thresholds"]["distress"])
        alt_g = float(config["altman_thresholds"].get("grey", 2.99))

        mda_th_cfg = config.get("mda_thresholds", {"distress": 0.0, "grey": 1.0, "cutoff": float(config.get("mda_threshold", 0.3844))})
        mda_d = float(mda_th_cfg.get("distress", 0.0))
        mda_g = float(mda_th_cfg.get("grey", mda_th_cfg.get("safe", 1.0)))

        # -------------------------------------------------------------
        # 1. Eksekusi Kalkulasi Multi-Model dan Sinkronisasi 3 Kategori
        # -------------------------------------------------------------
        if is_analyzed:
            z, z_cls, mda, mda_cls, xgb_prob, xgb_label = current_results()
            cat3 = determine_3category_status(z, z_cls, mda, mda_cls, xgb_prob, xgb_thresh=xgb_th_cfg)
            overall = cat3["status"]
            overall_tone = cat3["tone"]
            overall_trend = f"{cat3['badge_icon']} {cat3['status']}"
            overall_note = cat3["summary_note"]

            alt_badge = "🟢 SAFE ZONE" if z_cls == "aman" else ("🟡 GREY AREA" if z_cls in ("grey area", "grey", "waspada") else "🔴 DISTRESS ZONE")
            z_tone = "red" if z_cls == "distress" else ("amber" if z_cls in ("grey", "waspada") else "teal")
            z_trend = f"{alt_badge}"
            z_note = f"Distress < {alt_d:.2f} | Safe > {alt_g:.2f}"

            mda_badge = "🟢 SAFE ZONE" if mda_cls == "aman" else ("🟡 GREY AREA" if mda_cls in ("grey area", "grey") else "🔴 DISTRESS ZONE")
            mda_tone = "red" if mda_cls == "distress" else ("amber" if mda_cls in ("grey", "grey area") else "cyan")
            mda_trend = f"{mda_badge}"
            mda_note = f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])"

            if xgb_prob is None:
                xgb_status = "TIDAK TERSEDIA"
                xgb_tone = "purple"
                xgb_trend = "Standby (Belum Dimuat)"
                xgb_val_str = "N/A"
                xgb_note = "Model Belum Tersedia"
                xgb_badge_str = "⚪ N/A"
            else:
                if xgb_prob >= xgb_dist_th:
                    xgb_status = "DISTRESS ZONE"
                    xgb_tone = "red"
                    xgb_badge_str = "🔴 DISTRESS ZONE"
                    xgb_trend = f"🔴 Distress {xgb_prob*100:.1f}%"
                elif xgb_prob >= xgb_safe_th:
                    xgb_status = "GREY AREA"
                    xgb_tone = "amber"
                    xgb_badge_str = "🟡 GREY AREA"
                    xgb_trend = f"🟡 Waspada {xgb_prob*100:.1f}%"
                else:
                    xgb_status = "SAFE ZONE"
                    xgb_tone = "teal"
                    xgb_badge_str = "🟢 SAFE ZONE"
                    xgb_trend = f"🟢 Aman {(1.0-xgb_prob)*100:.1f}%"
                z_eq_val = calculate_xgb_equivalent_z_score(xgb_prob)
                xgb_val_str = f"{xgb_prob*100:.1f}% ({xgb_prob:.4f})"
                xgb_note = f"Safe < {xgb_safe_th*100:.0f}% | Dist > {xgb_dist_th*100:.0f}% • Eq. Z: {z_eq_val:.2f}"
        else:
            z, z_cls, mda, mda_cls, xgb_prob, xgb_label = 0.0, "standby", 0.0, "standby", None, 0
            cat3 = {
                "status": "STANDBY MODE",
                "tone": "blue",
                "color": "#64748b",
                "badge_icon": "⏳",
                "desc": "",
                "summary_note": "Belum Dilakukan Prediksi",
            }
            overall = "STANDBY MODE"
            overall_tone = "blue"
            overall_trend = "⚪ Belum Ada Prediksi"
            overall_note = "Silakan Input Data Emiten"
            alt_badge = "⚪ STANDBY"
            mda_badge = "⚪ STANDBY"
            xgb_badge_str = "⚪ STANDBY"
            xgb_status = "STANDBY"
            xgb_val_str = "-"
            z_tone = "blue"
            z_trend = "⚪ Standby"
            z_note = "Menunggu Analisis"
            mda_tone = "blue"
            mda_trend = "⚪ Standby"
            mda_note = "Menunggu Analisis"
            xgb_tone = "blue"
            xgb_trend = "⚪ Standby"
            xgb_note = "Menunggu Analisis"

        # =============================================================
        # AWAL HALAMAN (ABOVE THE FOLD): INFORMASI UTAMA DAN MONITORING
        # =============================================================

        # 1. Bar Identitas Emiten Aktif dan Pintasan Cepat
        is_light = is_light_theme()
        if is_light:
            bar_emiten_bg = "#ffffff"
            bar_emiten_border = "#cbd5e1"
            bar_emiten_txt = "#475569"
            bar_emiten_bold = "#0f172a"
            bar_emiten_year = "#2563eb"
        else:
            bar_emiten_bg = "rgba(15, 23, 42, 0.75)"
            bar_emiten_border = "rgba(255, 255, 255, 0.12)"
            bar_emiten_txt = "#cbd5e1"
            bar_emiten_bold = "#ffffff"
            bar_emiten_year = "#60a5fa"

        col_stat, c_tbtn1, c_tbtn2, c_tbtn3, c_tbtn4 = st.columns([2.7, 1.0, 1.0, 1.0, 1.0], gap="small")
        with col_stat:
            if not is_analyzed:
                st.markdown(
                    f"""
                    <div style="background:{bar_emiten_bg};border:1.5px solid {bar_emiten_border};border-radius:9px;padding:0 14px;height:38px;display:flex;align-items:center;justify-content:center;gap:8px;box-shadow:0 1px 4px rgba(15,23,42,0.03);box-sizing:border-box;text-align:center;">
                        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#3b82f6;box-shadow:0 0 6px rgba(59,130,246,0.6);flex-shrink:0;"></span>
                        <div style="font-size:11.5px;color:{bar_emiten_txt} !important;font-weight:700;letter-spacing:0.2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:center;">
                            STATUS: <span style="color:{bar_emiten_bold} !important;font-weight:800;">SIAGA ANALISIS</span> • BELUM ADA EMITEN TERANALISIS
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background:{bar_emiten_bg};border:1.5px solid {bar_emiten_border};border-radius:9px;padding:0 14px;height:38px;display:flex;align-items:center;justify-content:center;gap:8px;box-shadow:0 1px 4px rgba(15,23,42,0.03);box-sizing:border-box;overflow:hidden;text-align:center;" title="{st.session_state.company} ({st.session_state.ticker}) • Tahun {st.session_state.year}">
                        <span style="font-size:15px;flex-shrink:0;">🏢</span>
                        <div style="font-size:11.5px;color:{bar_emiten_txt} !important;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:center;">
                            Emiten: <b style="color:{bar_emiten_bold} !important;">{st.session_state.company}</b> <span style="background:{'#eff6ff' if is_light else 'rgba(59,130,246,0.18)'};color:{bar_emiten_year} !important;padding:2px 7px;border-radius:6px;font-weight:800;font-size:11px;border:1px solid {'#bfdbfe' if is_light else 'rgba(59,130,246,0.35)'};margin:0 4px;">{st.session_state.ticker}</span> • Tahun: <b style="color:{bar_emiten_year} !important;">{st.session_state.year}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with c_tbtn1:
            if st.button("📑 Data/Laporan", key="btn_goto_dl_from_dash", use_container_width=True, help="Buka input data dan laporan keuangan"):
                set_page("Data dan Laporan Keuangan")
                st.rerun()
        with c_tbtn2:
            if st.button("📈 Hasil Prediksi", key="btn_goto_pred_from_adm_dash", use_container_width=True, help="Buka halaman Hasil Prediksi lengkap"):
                set_page("Hasil Prediksi")
                st.rerun()
        with c_tbtn3:
            if st.button("⚖️ Evaluasi Model", key="btn_goto_eval_from_adm_dash", use_container_width=True, help="Buka evaluasi dan validasi model"):
                set_page("Perbandingan dan Evaluasi Model")
                st.rerun()
        with c_tbtn4:
            if st.button("🌐 API (Tahun)", key="btn_goto_api_from_dash", use_container_width=True, help="Buka integrasi API tahunan"):
                set_page("Integrasi API (Tahun)")
                st.rerun()

        # 2. Banner Eksekutif: Status Konsensus Keputusan Sistem (3 Kategori Operasional)
        if not is_analyzed:
            if is_light:
                cons_bg = "linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)"
                cons_border = "#cbd5e1"
                cons_left_bar = "#3b82f6"
                cons_badge_col = "#1d4ed8"
                cons_desc_col = "#0f172a"
                cons_pill_bg = "#ffffff"
                cons_pill_col = "#2563eb"
                cons_pill_border = "#93c5fd"
            else:
                cons_bg = "linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.9) 100%)"
                cons_border = "rgba(148, 163, 184, 0.25)"
                cons_left_bar = "#60a5fa"
                cons_badge_col = "#60a5fa"
                cons_desc_col = "#ffffff"
                cons_pill_bg = "rgba(59, 130, 246, 0.15)"
                cons_pill_col = "#93c5fd"
                cons_pill_border = "rgba(96, 165, 250, 0.35)"
        elif is_light:
            if "DISTRESS" in str(cat3['status']).upper():
                cons_bg = "linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)"
                cons_border = "#fca5a5"
                cons_left_bar = "#dc2626"
                cons_badge_col = "#991b1b"
                cons_desc_col = "#0f172a"
                cons_pill_bg = "#ffffff"
                cons_pill_col = "#b91c1c"
                cons_pill_border = "#f87171"
            elif "GREY" in str(cat3['status']).upper():
                cons_bg = "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)"
                cons_border = "#fde68a"
                cons_left_bar = "#d97706"
                cons_badge_col = "#92400e"
                cons_desc_col = "#0f172a"
                cons_pill_bg = "#ffffff"
                cons_pill_col = "#b45309"
                cons_pill_border = "#fbbf24"
            else:
                cons_bg = "linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)"
                cons_border = "#a7f3d0"
                cons_left_bar = "#059669"
                cons_badge_col = "#065f46"
                cons_desc_col = "#0f172a"
                cons_pill_bg = "#ffffff"
                cons_pill_col = "#047857"
                cons_pill_border = "#34d399"
        else:
            cons_bg = f"linear-gradient(135deg, {cat3['color']}18 0%, rgba(15, 23, 42, 0.9) 100%)"
            cons_border = f"{cat3['color']}55"
            cons_left_bar = cat3['color']
            cons_badge_col = cat3['color']
            cons_desc_col = "#ffffff"
            cons_pill_bg = f"{cat3['color']}25"
            cons_pill_col = cat3['color']
            cons_pill_border = f"{cat3['color']}66"

        cons_title_text = f"{cat3['status']} — {cat3['desc']}" if cat3.get("desc") else cat3["status"]
        st.markdown(
            f"""
            <div style="background:{cons_bg};border:1.5px solid {cons_border};border-left:6px solid {cons_left_bar};border-radius:14px;padding:12px 18px;margin-bottom:14px;box-shadow:0 4px 16px rgba(15,23,42,0.06);">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span style="font-size:26px;">{cat3['badge_icon']}</span>
                        <div>
                            <div style="font-size:11px;font-weight:850;color:{cons_badge_col} !important;text-transform:uppercase;letter-spacing:1px;">KONSENSUS KEPUTUSAN SISTEM (3 KATEGORI)</div>
                            <div style="font-size:17px;font-weight:900;color:{cons_desc_col} !important;margin-top:1px;">{cons_title_text}</div>
                        </div>
                    </div>
                    <span style="background:{cons_pill_bg};color:{cons_pill_col} !important;border:1.5px solid {cons_pill_border};font-size:12px;font-weight:850;padding:5px 14px;border-radius:20px;box-shadow:0 2px 6px rgba(15,23,42,0.05);">
                        {cat3['summary_note']}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 3. Empat Kartu Metrik Ringkasan Utama (Single Cohesive Set)
        c = st.columns(4)
        if is_analyzed:
            metric_card(c[0], "ALTMAN Z''-SCORE", f"{z:.2f}", z_note, z_tone, trend=z_trend)
            metric_card(c[1], "Z-SCORE KOEF. BARU", f"{mda:.2f}", mda_note, mda_tone, trend=mda_trend)
            metric_card(c[2], "PREDIKSI XGBOOST", xgb_val_str, xgb_note, xgb_tone, trend=xgb_trend)
            metric_card(c[3], "KONSENSUS 3 KATEGORI", overall, overall_note, overall_tone, trend=overall_trend)
        else:
            metric_card(c[0], "ALTMAN Z''-SCORE", "-", "Menunggu Analisis", "blue", trend="⚪ Standby")
            metric_card(c[1], "Z-SCORE KOEF. BARU", "-", "Menunggu Analisis", "blue", trend="⚪ Standby")
            metric_card(c[2], "PREDIKSI XGBOOST", "-", "Menunggu Analisis", "blue", trend="⚪ Standby")
            metric_card(c[3], "KONSENSUS 3 KATEGORI", "STANDBY MODE", "Belum Dilakukan Prediksi", "blue", trend="⚪ Belum Ada Data")

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        # 4. Baris Pemantauan Visual Utama (Visual Gauges dan Early Warning Checklist)
        if is_analyzed:
            col_vis_left, col_vis_right = st.columns([1.05, 1.3])
            with col_vis_left:
                with st.container(border=True):
                    section_title("Visualisasi Status Risiko", tone=overall_tone)
                    g_tab_z, g_tab_xgb = st.tabs(["⏱️ Speedometer Altman Z''", "⚡ Quantum Gauge XGBoost"])
                    with g_tab_z:
                        render_gauge(z, config["altman_thresholds"])
                        status_color = "#f43f5e" if z_cls == "distress" else ("#f59e0b" if z_cls in ("grey", "waspada") else "#14b8a6")
                        st.markdown(f"<div style='text-align:center;font-weight:900;color:{status_color};font-size:14px;letter-spacing:0.8px;margin-top:4px;'>ALTMAN Z'': {alt_badge}</div>", unsafe_allow_html=True)
                    with g_tab_xgb:
                        if xgb_prob is not None:
                            render_quantum_gauge(xgb_prob, xgb_th_cfg)
                            probability_badge(xgb_prob, xgb_status, threshold=xgb_th_cfg)
                        else:
                            st.info("Model XGBoost belum dimuat atau belum tersedia.")

            with col_vis_right:
                with st.container(border=True):
                    section_title("Sistem Peringatan Dini dan Keselarasan", tone="amber")
                    if evaluate_model_concordance:
                        concordance = evaluate_model_concordance(z_cls, mda_cls, xgb_label)
                        render_concordance_badge(concordance)
                    if evaluate_warning_factors:
                        warning_factors = evaluate_warning_factors(st.session_state.financials)
                        render_warning_factors_checklist(warning_factors)
        else:
            with st.container(border=True):
                st.info("ℹ️ **Monitoring Visual Siaga:** Speedometer Altman Z'', Quantum Gauge XGBoost, Sistem Peringatan Dini, dan Keselarasan Tiga Model akan aktif secara dinamis setelah Anda menginput data laporan keuangan atau memilih emiten.")

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # =============================================================
        # DI BAWAH AWAL HALAMAN: TAB RINCIAN TEKNIS DAN AUDIT
        # =============================================================
        adm_dash_tabs = st.tabs([
            "🏢 1. Profil Emiten dan Masukan Rasio (X1–X5)",
            "⚖️ 2. Komparasi Tiga Metode (Side-by-Side)",
            "🤖 3. Rincian Inferensi XGBoost AI",
            "📜 4. Histori dan Audit Prediksi Terkini",
        ])

        # Tab 1: Profil Emiten dan Masukan Rasio Keuangan
        with adm_dash_tabs[0]:
            c_prof_l, c_prof_r = st.columns([1.0, 1.45])
            with c_prof_l:
                with st.container(border=True):
                    section_title("Data Profil Emiten Teranalisis", tone="blue")
                    info_table([
                        ("Nama Perusahaan", st.session_state.company or "Belum Dipilih"),
                        ("Kode Perusahaan (Ticker)", st.session_state.ticker or "-"),
                        ("Sektor Industri", st.session_state.sector or "-"),
                        ("Tahun Laporan Keuangan", str(st.session_state.year) if is_analyzed else "-"),
                        ("Tanggal Analisis Sesi", st.session_state.analysis_date if is_analyzed else "-"),
                    ])
                    st.caption("Data perusahaan ini disinkronkan langsung dari input aktif atau penarikan API Bursa Efek Indonesia.")
            with c_prof_r:
                with st.container(border=True):
                    section_title("Variabel Rasio Keuangan Model (X1–X5)", tone="purple")
                    ratio_labels = {
                        "X1": "X1 • Modal Kerja / Total Aset (WC/TA)",
                        "X2": "X2 • Laba Ditahan / Total Aset (RE/TA)",
                        "X3": "X3 • EBIT / Total Aset (EBIT/TA)",
                        "X4": "X4 • Ekuitas Saham / Total Liabilitas (CSE/TL)",
                        "X5": "X5 • Pendapatan / Total Aset (S/TA - Altman 1968)",
                    }
                    if is_analyzed:
                        r_rows = [
                            (ratio_labels.get(k, k), f"{st.session_state.ratios.get(k, 0.0):.4f}")
                            for k in ["X1", "X2", "X3", "X4", "X5"]
                        ]
                    else:
                        r_rows = [
                            (ratio_labels.get(k, k), "-")
                            for k in ["X1", "X2", "X3", "X4", "X5"]
                        ]
                    info_table(r_rows)
                    cap_audit = st.session_state.get("capping_audit", {})
                    if is_analyzed and "X4" in cap_audit:
                        st.caption(f"🛡️ *Capping X4 Aktif:* `{cap_audit['X4']['raw']:.4f}` ➔ **{cap_audit['X4']['capped']:.4f}** (Maks 3.0)")

        # Tab 2: Komparasi Tiga Metode (Side-by-Side Multi-Model)
        with adm_dash_tabs[1]:
            st.markdown("#### ⚖️ Matriks Perbandingan Output Ketiga Metode (3 Kategori Operasional)")
            st.caption("Perbandingan side-by-side seluruh model statistik dan kecerdasan buatan pada emiten yang sedang dianalisis:")

            if is_analyzed:
                df_bench = pd.DataFrame([
                    [
                        "📐 Altman Z''-Score (1995)",
                        f"{z:.2f}",
                        f"Distress < {alt_d:.2f} | Safe > {alt_g:.2f}",
                        alt_badge,
                        "Konsisten" if (z_cls == "distress" and "DISTRESS" in overall) or (z_cls == "aman" and "SAFE" in overall) or (z_cls in ("grey", "grey area", "waspada") and "GREY" in overall) else "Divergen / Evaluasi",
                        "Model Teoretis Baku Altman 1995/2017"
                    ],
                    [
                        "📊 Z''-Score Koefisien Baru (MDA)",
                        f"{mda:.2f}",
                        f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])",
                        mda_badge,
                        "Konsisten" if (mda_cls == "distress" and "DISTRESS" in overall) or (mda_cls == "aman" and "SAFE" in overall) or (mda_cls in ("grey", "grey area") and "GREY" in overall) else "Divergen / Evaluasi",
                        "Model Empiris Dikalibrasi 704 Observasi BEI"
                    ],
                    [
                        "🤖 XGBoost Classifier (AI)",
                        f"{xgb_val_str} • Eq. Z: {z_eq_val:.2f}" if xgb_prob is not None else "N/A",
                        f"Safe < {xgb_safe_th*100:.0f}% | Distress > {xgb_dist_th*100:.0f}%",
                        xgb_badge_str,
                        "Konsisten" if (xgb_status == overall) else "Divergen / Evaluasi",
                        "Model Kecerdasan Buatan Gradient Boosted Trees Non-Linear"
                    ],
                ], columns=["Pendekatan Model", "Nilai / Probabilitas", "Cut-off / Threshold", "Zona Klasifikasi (3 Kategori)", "Status Keselarasan", "Keterangan Metodologi"])
                st.dataframe(df_bench, use_container_width=True, hide_index=True)

                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                col_radar_cmp, col_bar_cmp = st.columns([1.1, 1.0])
                with col_radar_cmp:
                    st.markdown("##### 🎯 Radar Konvergensi Multidimensi")
                    st.caption("Pemetaan komparatif profil rasio keuangan emiten terhadap batas aman benchmark industri.")
                    render_radar_chart(st.session_state.ratios)
                with col_bar_cmp:
                    st.markdown("##### 📊 Distribusi Skor Antar-Metode")
                    st.caption("Perbandingan terkalibrasi skor statistik dan probabilitas inferensi machine learning.")
                    render_score_distribution_chart(z, mda, xgb_prob, key_suffix="dashboard", config=config)
            else:
                df_bench = pd.DataFrame([
                    ["📐 Altman Z''-Score (1995)", "-", f"Distress < {alt_d:.2f} | Safe > {alt_g:.2f}", "⏳ STANDBY", "Menunggu Analisis", "Model Teoretis Baku Altman 1995/2017"],
                    ["📊 Z''-Score Koefisien Baru (MDA)", "-", f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])", "⏳ STANDBY", "Menunggu Analisis", "Model Empiris Dikalibrasi 704 Observasi BEI"],
                    ["🤖 XGBoost Classifier (AI)", "-", f"Safe < {xgb_safe_th*100:.0f}% | Distress > {xgb_dist_th*100:.0f}%", "⏳ STANDBY", "Menunggu Analisis", "Model Kecerdasan Buatan Gradient Boosted Trees Non-Linear"],
                ], columns=["Pendekatan Model", "Nilai / Probabilitas", "Cut-off / Threshold", "Zona Klasifikasi (3 Kategori)", "Status Keselarasan", "Keterangan Metodologi"])
                st.dataframe(df_bench, use_container_width=True, hide_index=True)
                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                st.info("ℹ️ Radar konvergensi dan visualisasi distribusi skor akan ditampilkan setelah emiten dianalisis.")

        # Tab 3: Rincian Inferensi XGBoost AI
        with adm_dash_tabs[2]:
            st.markdown("#### 🤖 Hasil Klasifikasi Model Kecerdasan Buatan (XGBoost)")
            st.caption(
                "Model XGBoost memproses 4 variabel rasio utama (X1–X4) melalui pohon keputusan ensemble gradient boosted trees "
                "dengan fungsi aktivasi Sigmoid untuk menghasilkan estimasi probabilitas kebangkrutan yang akurat."
            )

            if is_analyzed:
                c_xgb_a, c_xgb_b = st.columns([1.35, 1.0])
                with c_xgb_a:
                    xgb_details = xgboost_predict_detailed(st.session_state.ratios, str(MODEL_PATH), threshold=xgb_th_cfg)
                    if xgb_details.get("available", False):
                        df_xgb_metrics = pd.DataFrame([
                            ("Probabilitas Financial Distress (P)", f"{xgb_details['probability']*100:.2f}% ({xgb_details['probability']:.4f})"),
                            ("Probabilitas Non-Distress (1 - P)", f"{xgb_details['prob_non_distress']*100:.2f}% ({xgb_details['prob_non_distress']:.4f})"),
                            ("Nilai Margin Log-Odds", f"{xgb_details['margin']:.4f}"),
                            ("Ambang Batas 3 Zona", f"Safe < {xgb_safe_th*100:.0f}% | Distress > {xgb_dist_th*100:.0f}%"),
                            ("Klasifikasi Output", f"Label {xgb_details['label']} • {xgb_details['status']}"),
                            ("Tingkat Risiko Finansial", "RISIKO TINGGI (DISTRESS ZONE)" if xgb_details['label'] == 1 else ("ZONA WASPADA (GREY AREA)" if xgb_details['label'] == 2 else "RISIKO RENDAH (SAFE ZONE)")),
                        ], columns=["Komponen Output XGBoost", "Hasil Evaluasi"])
                        st.dataframe(df_xgb_metrics, use_container_width=True, hide_index=True)
                    else:
                        st.warning("Model XGBoost belum tersedia di direktori `models/xgb_model.json`.")

                with c_xgb_b:
                    if xgb_prob is not None:
                        probability_badge(xgb_prob, xgb_status, threshold=xgb_th_cfg)
                        st.caption(
                            f"💡 **Aturan Keputusan 3 Zona:** "
                            f"Safe Zone ($P < {xgb_safe_th*100:.0f}\\%$), "
                            f"Grey Area (${xgb_safe_th*100:.0f}\\% \\le P \\le {xgb_dist_th*100:.0f}\\%$), dan "
                            f"Distress Zone ($P > {xgb_dist_th*100:.0f}\\%$). "
                            f"Hasil kalkulasi saat ini adalah **{xgb_prob*100:.2f}%** ({xgb_status})."
                        )
            else:
                st.info("ℹ️ **Model XGBoost Siap:** Silakan masukkan data laporan keuangan emiten pada menu Data dan Laporan Keuangan atau klik tombol Muat Data Demo untuk melihat rincian inferensi AI.")

        # Tab 4: Histori dan Audit Prediksi Terkini
        with adm_dash_tabs[3]:
            dash_hist_head, dash_hist_btn = st.columns([2.8, 1.2])
            with dash_hist_head:
                section_title("Histori Prediksi dan Audit Terkini", "Ringkasan analisis yang tersimpan di basis data sistem")
            with dash_hist_btn:
                if st.session_state.role == "admin":
                    if st.button("📜 Buka Histori Lengkap 🚀", key="btn_goto_hist_from_dash", use_container_width=True):
                        set_page("Histori Prediksi")
                        st.rerun()

            df_recent = get_all_predictions()
            if not df_recent.empty:
                df_disp = df_recent.head(8).copy()
                df_disp["Status XGB"] = df_disp["xgb_prob"].apply(
                    lambda p: ("DISTRESS" if float(p) >= xgb_thresh else "NON-DISTRESS") if pd.notnull(p) else "-"
                )
                df_disp["Prob. XGB"] = df_disp["xgb_prob"].apply(
                    lambda p: f"{float(p)*100:.1f}% ({float(p):.4f})" if pd.notnull(p) else "-"
                )
                df_disp["Altman Z''"] = df_disp["z_score"].apply(lambda v: f"{float(v):.2f}" if pd.notnull(v) else "-")
                df_disp["MDA Z'"] = df_disp["mda_score"].apply(lambda v: f"{float(v):.2f}" if pd.notnull(v) else "-")
                df_disp["Status Altman"] = df_disp["z_cls"].str.upper()
                df_disp["Status MDA"] = df_disp["mda_cls"].str.upper()

                cols_show = ["id", "timestamp", "username", "ticker", "company", "year", "Altman Z''", "Status Altman", "MDA Z'", "Status MDA", "Prob. XGB", "Status XGB"]
                cols_show = [col for col in cols_show if col in df_disp.columns]
                rename_map = {
                    "id": "ID",
                    "timestamp": "Waktu",
                    "username": "Pengguna",
                    "ticker": "Ticker",
                    "company": "Perusahaan",
                    "year": "Tahun",
                }
                st.dataframe(df_disp[cols_show].rename(columns=rename_map), use_container_width=True, hide_index=True)

                # Fitur Muat Emiten dari Riwayat ke Dashboard
                c_load_sel, c_load_btn = st.columns([3, 1])
                with c_load_sel:
                    pred_options = {
                        int(row["id"]): f"ID #{row['id']} • {row['ticker']} - {row['company']} ({row['year']}) | XGB: {row.get('Status XGB', '-')}"
                        for _, row in df_disp.iterrows()
                    }
                    selected_hist_id = st.selectbox(
                        "Pilih emiten dari riwayat untuk diinspeksi di Dashboard Sistem:",
                        options=list(pred_options.keys()),
                        format_func=lambda x: pred_options[x],
                        key="dash_select_hist_emiten"
                    )
                with c_load_btn:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("📥 Muat ke Dashboard", key="btn_load_hist_to_dash", use_container_width=True, help="Memuat emiten ini ke sesi aktif dashboard"):
                        matched_rows = df_disp[df_disp["id"] == selected_hist_id]
                        if not matched_rows.empty:
                            matched_row = matched_rows.iloc[0]
                            t_sym = str(matched_row["ticker"]).strip().upper()
                            st.session_state.company = str(matched_row["company"])
                            st.session_state.ticker = t_sym
                            st.session_state.year = int(matched_row["year"])
                            st.session_state.has_analyzed = True
                            if t_sym in MOCK_IDX_DATA:
                                m_fin = MOCK_IDX_DATA[t_sym].get("financials_by_year", {}).get(st.session_state.year, {}) or MOCK_IDX_DATA[t_sym].get("financials_by_year", {}).get(2024, {})
                                if m_fin:
                                    st.session_state.financials = dict(m_fin)
                                    try:
                                        set_ratios_from_financials(st.session_state.financials)
                                    except Exception:
                                        pass
                            st.toast(f"Data {matched_row['ticker']} dimuat ke sesi aktif!", icon="✅")
                            st.rerun()
            else:
                st.caption("Belum ada riwayat prediksi tersimpan.")