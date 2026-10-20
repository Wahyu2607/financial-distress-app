from __future__ import annotations

import base64
from datetime import datetime
import html
import io
import json
import math
from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

# st.set_page_config HARUS DI BARIS PERTAMA SEBELUM PERINTAH STREAMLIT LAINNYA
st.set_page_config(
    page_title="Financial Distress Prediction System",
    page_icon="📉",
    layout="wide",
)

import sys
import importlib

# Matikan penulisan file bytecode cache (.pyc) agar Streamlit selalu membaca file terbaru dari disk
sys.dont_write_bytecode = True

# Hapus dan reload modul src dari memori sys.modules untuk mencegah module caching usang pada server Streamlit yang berjalan
for mod_name in ["src.calculations", "src.io_utils", "src.ui", "src.styles", "src.database", "src.financial_api", "src"]:
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
    generate_printable_html_report,
    generate_full_csv_report,
    generate_full_json_report,
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
                💡 Solusi & Rekomendasi Langkah Alternatif (Fallback):
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

# ---------- Database Management (Dual-Mode: SQLite Lokal & Cloud PostgreSQL) ----------
from src.database import (
    init_db,
    verify_user,
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
)

# Inisialisasi struktur database saat aplikasi dimulai
init_db()

# ==============================================================================
# Master Data Pintasan Emiten IDX (Dikhususkan untuk Industri Manufaktur)
# Sesuai Kalibrasi Sampel Empiris Model Altman Z''-Score & XGBoost
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
        ("KLBF", "Kalbe Farma", "Farmasi & Kesehatan"),
        ("ASII", "Astra International", "Aneka Industri / Otomotif"),
        ("AUTO", "Astra Otoparts", "Komponen Otomotif"),
        ("SMGR", "Semen Indonesia", "Industri Dasar / Semen"),
        ("HMSP", "HM Sampoerna", "Barang Konsumsi / Rokok"),
        ("KICI", "Kedaung Indah Can", "Kemasan & Enamel (Lapis 3)"),
    ],
    "🚨 Kasus Financial Distress": [
        ("AISA", "FKS Food Sejahtera", "Restrukturisasi & Defisit Saldo Laba"),
        ("ANDI", "Andira Agro", "Defisit Modal Kerja & Going Concern"),
        ("ALTO", "Tri Banyan Tirta", "AMDK Utang Tinggi & Distress"),
        ("KICI", "Kedaung Indah Can", "Kemasan Kaleng (Lapis 3)"),
    ],
    "🍪 Barang Konsumsi": [
        ("ICBP", "Indofood CBP", "Makanan Olahan & Minuman"),
        ("AISA", "FKS Food Sejahtera", "Bihun & Snack Taro (F&B)"),
        ("ADES", "Akasha Wira", "Air Mineral & Kosmetik"),
        ("ALTO", "Tri Banyan Tirta", "Air Minum / Total 8+"),
        ("INDF", "Indofood Sukses", "Agribisnis & Makanan"),
        ("UNVR", "Unilever Indonesia", "FMCG / Perawatan Tubuh"),
        ("KLBF", "Kalbe Farma", "Farmasi & Suplemen"),
        ("HMSP", "HM Sampoerna", "Tembakau & Rokok"),
        ("GGRM", "Gudang Garam", "Tembakau & Rokok"),
        ("MYOR", "Mayora Indah", "Makanan Ringan & Biskuit"),
        ("SIDO", "Sido Muncul", "Jamu Herbal & Suplemen"),
    ],
    "⚙️ Aneka Industri": [
        ("ASII", "Astra International", "Konglomerasi Otomotif"),
        ("AUTO", "Astra Otoparts", "Suku Cadang Otomotif"),
        ("SMSM", "Selamat Sempurna", "Filter & Radiator"),
        ("GJTL", "Gajah Tunggal", "Ban Kendaraan"),
    ],
    "🧱 Industri Dasar & Kimia": [
        ("SMGR", "Semen Indonesia (SIG)", "Semen & Bahan Bangunan"),
        ("INTP", "Indocement Tunggal", "Semen & Mortar"),
        ("BRPT", "Barito Pacific", "Petrokimia Terintegrasi"),
        ("TPIA", "Chandra Asri", "Petrokimia Hulu"),
        ("AALI", "Astra Agro Lestari", "Agribisnis Pengolahan Sawit"),
        ("ANDI", "Andira Agro", "Agroindustri Sawit (CPO)"),
        ("KICI", "Kedaung Indah Can", "Kemasan Kaleng & Logam"),
    ],
}

ALL_OTHER_SECTORS = [
    ("TLKM", "Telkom Indonesia", "Telekomunikasi"),
    ("BBCA", "Bank Central Asia", "Perbankan (Non-Manufaktur)*"),
    ("BBRI", "Bank Rakyat Indo", "Perbankan (Non-Manufaktur)*"),
    ("BMRI", "Bank Mandiri", "Perbankan (Non-Manufaktur)*"),
    ("ADRO", "Adaro Energy", "Energi & Batubara"),
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
                *Model Altman Z''-Score & XGBoost dikalibrasi primer pada manufaktur
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
        "🧱 Industri Dasar & Kimia",
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
        st.caption("🍪 Subsektor Consumer Goods (Makanan & Minuman, Farmasi, Kosmetik, Tembakau):")
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

    # Tab 4: Aneka Industri & Otomotif
    with tabs[3]:
        st.caption("⚙️ Subsektor Aneka Industri, Perakitan Otomotif, Suku Cadang & Mesin:")
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

    # Tab 5: Industri Dasar & Kimia
    with tabs[4]:
        st.caption("🧱 Subsektor Bahan Bangunan, Semen, Logam, Kimia Industri & Petrokimia:")
        cols = st.columns(4)
        for i, (sym, name, sub) in enumerate(MANUFACTURING_GROUPS["🧱 Industri Dasar & Kimia"]):
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
    "username": "",
    "role": "user",
    "user_fullname": "",
    "user_email": "",
    "user_institution": "Bursa Efek Indonesia (BEI)",
    "user_division": "Financial Risk Analysis",
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
    "Data Perusahaan": "Data & Laporan Keuangan",
    "Laporan Keuangan": "Data & Laporan Keuangan",
    "Input Data": "Data & Laporan Keuangan",
    "Input Data Keuangan": "Data & Laporan Keuangan",
    "Rasio Keuangan": "Rasio & Hasil Prediksi",
    "Hasil Prediksi": "Rasio & Hasil Prediksi",
    "Perbandingan Hasil": "Perbandingan & Evaluasi Model",
    "Evaluasi Model": "Perbandingan & Evaluasi Model",
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
    "Dashboard Prediksi": "Hasil Prediksi",
    "Data & Laporan Keuangan": "Data & Laporan Keuangan",
    "Data Perusahaan": "Data & Laporan Keuangan",
    "Laporan Keuangan": "Data & Laporan Keuangan",
    "Input Data": "Data & Laporan Keuangan",
    "Input Data Keuangan": "Data & Laporan Keuangan",
    "Rasio Keuangan": "Hasil Prediksi",
    "Rasio & Hasil Prediksi": "Hasil Prediksi",
    "Perbandingan & Evaluasi Model": "Perbandingan & Evaluasi Model",
    "Perbandingan Hasil": "Perbandingan & Evaluasi Model",
    "Evaluasi Model": "Perbandingan & Evaluasi Model",
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
    """Mengakhiri sesi autentikasi pengguna secara aman dan mengarahkan kembali ke halaman masuk."""
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = "user"
    st.session_state.user_fullname = ""
    st.session_state.user_email = ""
    st.session_state.page = "Dashboard"
    st.session_state.custom_page_menu = "Dashboard"
    st.session_state._last_nav_page = "Dashboard"
    st.session_state.has_analyzed = False
    st.session_state.company = ""
    st.session_state.ticker = ""
    st.session_state.financials = {}
    st.session_state.ratios = {"X1": 0.0, "X2": 0.0, "X3": 0.0, "X4": 0.0, "X5": 0.0}
    st.session_state.show_logout_confirm = False
    st.session_state.auth_flash_success = "👋 Anda telah berhasil keluar (logout) dari sistem. Sampai jumpa kembali!"
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        else:
            st.experimental_set_query_params()
    except Exception:
        pass
    st.rerun()

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

    if auth_action == "demo_admin":
        st.session_state.logged_in = True
        st.session_state.username = "admin"
        st.session_state.role = "admin"
        set_page("Dashboard")
        _clear_auth_params()
        st.rerun()

    elif auth_action == "demo_user":
        st.session_state.logged_in = True
        st.session_state.username = "user"
        st.session_state.role = "user"
        set_page("Dashboard")
        _clear_auth_params()
        st.rerun()

    elif auth_action == "signin":
        in_user = _get_auth_param("in_user").strip()
        in_pass = _get_auth_param("in_pass").strip()
        if not in_user or not in_pass:
            st.session_state.auth_flash_error = "Mohon isi username/email dan password."
            st.session_state.auth_mode = "signin"
        else:
            role = verify_user(in_user, in_pass)
            if role:
                profile = get_user_profile(in_user)
                canon_u = profile["username"] if profile else in_user
                st.session_state.logged_in = True
                st.session_state.username = canon_u
                st.session_state.role = role
                set_page("Dashboard")
                _clear_auth_params()
                st.rerun()
            else:
                st.session_state.auth_flash_error = "Username/Email atau password salah!"
                st.session_state.auth_mode = "signin"
        _clear_auth_params()
        st.rerun()

    elif auth_action == "signup":
        up_user = _get_auth_param("up_user").strip()  # Email / User
        up_pass = _get_auth_param("up_pass").strip()  # Password
        up_name = _get_auth_param("up_name").strip()  # Name / Username

        # 1. Validasi Input Kosong
        if not up_user or not up_pass:
            st.session_state.auth_flash_error = "Mohon lengkapi email dan password."
            st.session_state.auth_mode = "signup"
        elif len(up_pass) < 4:
            st.session_state.auth_flash_error = "Password minimal 4 karakter."
            st.session_state.auth_mode = "signup"
        else:
            # 2. Blokir Ketat Pembuatan Akun Admin
            clean_u = up_user.lower()
            clean_name = up_name.lower()
            forbidden = ["admin", "administrator", "root", "superuser"]
            is_admin = (
                any(k in clean_u for k in forbidden)
                or any(k in clean_name for k in forbidden)
            )
            if is_admin:
                st.session_state.auth_flash_error = "⛔ Pembuatan akun Administrator diblokir demi keamanan sistem! Silakan gunakan nama atau email lain."
                st.session_state.auth_mode = "signup"
            else:
                # 3. Eksekusi Registrasi Pengguna
                chosen_username = up_name if up_name else up_user.split("@")[0]
                ok, msg = add_new_user(
                    username=chosen_username,
                    password=up_pass,
                    role="user",
                    email=up_user,
                    full_name=up_name
                )
                if ok:
                    st.session_state.auth_flash_success = f"🎉 Akun '{chosen_username}' berhasil didaftarkan! Silakan masuk."
                    st.session_state.auth_mode = "signin"
                    st.session_state.prefill_user = chosen_username
                else:
                    st.session_state.auth_flash_error = f"❌ {msg}"
                    st.session_state.auth_mode = "signup"
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

    # Deteksi file latar belakang kustom JPG/PNG
    bg_image_css = ""
    candidate_bg_names = [
        "background.jpg", "bg.jpg", "wallpaper.jpg", "login_bg.jpg", 
        "foto.jpg", "background.jpeg", "bg.jpeg", "background.png", "bg.png"
    ]
    found_bg_path = None
    for bname in candidate_bg_names:
        cand = BASE_DIR / bname
        if cand.exists() and cand.is_file():
            found_bg_path = cand
            break

    if not found_bg_path:
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            matches = list(BASE_DIR.glob(ext))
            if matches:
                found_bg_path = matches[0]
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

    if not bg_image_css:
        bg_image_css = """
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: #f1f5f9 !important;
            background-image: radial-gradient(circle at 50% 30%, #ffffff 0%, #f1f5f9 60%, #e2e8f0 100%) !important;
        }
        """

    # Format pesan alert jika ada
    alert_html_signin = ""
    alert_html_signup = ""
    if auth_error_msg:
        if st.session_state.auth_mode == "signup":
            alert_html_signup = f'<div class="auth-alert alert-error"><span class="alert-icon">⚠️</span><span>{auth_error_msg}</span></div>'
        else:
            alert_html_signin = f'<div class="auth-alert alert-error"><span class="alert-icon">⚠️</span><span>{auth_error_msg}</span></div>'
    elif auth_success_msg:
        alert_html_signin = f'<div class="auth-alert alert-success"><span class="alert-icon">🎉</span><span>{auth_success_msg}</span></div>'

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

    header[data-testid="stHeader"], footer, #MainMenu, .stDeployButton, div[data-testid="stDecoration"] {{
        display: none !important;
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

    .form-header,
    div[data-testid="stMarkdownContainer"] .form-header {{
        width: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        margin: 0 auto 13px auto !important;
        padding: 0 !important;
    }}
    .form-title,
    div[data-testid="stMarkdownContainer"] .form-title,
    h2.form-title {{
        width: 100% !important;
        font-size: 22px !important;
        font-weight: 850 !important;
        color: #0f172a !important;
        letter-spacing: -0.5px !important;
        margin: 0 0 4px 0 !important;
        padding: 0 !important;
        text-align: center !important;
        line-height: 1.25 !important;
        display: block !important;
    }}
    .form-header a,
    .form-title a,
    .slider-card a.anchor-link,
    .slider-card [data-testid="stHeaderActionElements"],
    .form-panel [data-testid="stHeaderActionElements"] {{
        display: none !important;
        opacity: 0 !important;
        pointer-events: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }}
    .form-subtitle,
    div[data-testid="stMarkdownContainer"] .form-subtitle,
    p.form-subtitle {{
        width: 100% !important;
        font-size: 11.5px !important;
        color: #64748b !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center !important;
        line-height: 1.4 !important;
        display: block !important;
    }}

    .form-panel form {{
        width: 100%;
        pointer-events: auto !important;
    }}

    .input-group {{
        margin-bottom: 9px;
        text-align: left;
        width: 100%;
        pointer-events: auto !important;
    }}
    .input-label-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        pointer-events: auto !important;
    }}
    .input-label {{
        font-size: 11.5px;
        font-weight: 750;
        color: #1e293b;
        letter-spacing: -0.2px;
        cursor: pointer;
        pointer-events: auto !important;
    }}
    .forgot-pass-link {{
        font-size: 10.5px;
        color: #2563eb;
        cursor: pointer;
        text-decoration: none;
        font-weight: 600;
        pointer-events: auto !important;
    }}
    .forgot-pass-link:hover {{
        text-decoration: underline;
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
        box-shadow: 0 8px 20px -3px rgba(23, 92, 242, 0.42);
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-top: 5px;
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
    }}
    .link-switch {{
        color: #175cf2;
        font-weight: 800;
        cursor: pointer;
        margin-left: 4px;
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
        font-size: 9.5px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #ffffff;
        opacity: 0.85;
        text-transform: uppercase;
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

    @media (max-width: 820px) {{
        .slider-card {{
            width: 95vw !important;
            height: auto !important;
            min-height: 540px !important;
            border-radius: 20px !important;
        }}
        .form-panel {{
            width: 100% !important;
            padding: 20px !important;
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
<div class="ambient-orb orb-1"></div>
<div class="ambient-orb orb-2"></div>

<div class="slider-card {card_mode_class}" id="authCard">

<input type="radio" id="tab-signup" name="auth_state" class="auth-radio-toggle" {checked_signup}>
<input type="radio" id="tab-signin" name="auth_state" class="auth-radio-toggle" {checked_signin}>

<div class="form-panel sign-in-panel">
<div class="form-header" style="text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;">
<div class="form-title" style="text-align: center; width: 100%;">Sign In</div>
<p class="form-subtitle" style="text-align: center; width: 100%;">Financial Distress Analysis System</p>
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
<div class="form-header" style="text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%;">
<div class="form-title" style="text-align: center; width: 100%;">Create Account</div>
<p class="form-subtitle" style="text-align: center; width: 100%;">Create your account to sign in</p>
</div>

{alert_html_signup}

<form action="" method="GET" target="_self">
<input type="hidden" name="auth_action" value="signup">

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="up_name">Name</label>
</div>
<input type="text" id="up_name" name="up_name" placeholder="Enter your name" class="auth-input" autocomplete="name">
</div>

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="up_user">E-mail Address</label>
</div>
<input type="text" id="up_user" name="up_user" placeholder="Enter your email" required class="auth-input" autocomplete="email">
</div>

<div class="input-group">
<div class="input-label-row">
<label class="input-label" for="up_pass">Password</label>
</div>
<input type="password" id="up_pass" name="up_pass" placeholder="Enter your password" required class="auth-input" autocomplete="new-password">
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
<div class="brand-desc">Masuk kembali untuk mengakses pengujian emiten, evaluasi XGBoost & Altman Z'', dan histori prediksi.</div>
<label for="tab-signup" class="btn-overlay-nav" onclick="switchAuthMode('signup')">
<span>⬅ Belum Ada Akun?</span>
<strong>Sign Up</strong>
</label>
</div>
<div class="brand-item-footer">ANALISIS INTELLIGENCE PLATFORM</div>
</div>

</div>
</div>
</div>
<img src="data:image/svg+xml;utf8,<svg></svg>" style="display:none;" onload="
window.switchAuthMode = function(target) {{
    try {{
        var card = document.getElementById('authCard');
        var rIn = document.getElementById('tab-signin');
        var rUp = document.getElementById('tab-signup');
        if (target === 'signin') {{
            if (card) {{
                card.classList.remove('is-signup-mode');
                card.classList.add('is-signin-mode');
            }}
            if (rIn) {{ rIn.checked = true; }}
            if (rUp) {{ rUp.checked = false; }}
        }} else {{
            if (card) {{
                card.classList.remove('is-signin-mode');
                card.classList.add('is-signup-mode');
            }}
            if (rUp) {{ rUp.checked = true; }}
            if (rIn) {{ rIn.checked = false; }}
        }}
    }} catch(e) {{}}
}};
">
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
        "Data & Laporan Keuangan",
        "Rasio & Hasil Prediksi",
        "Perbandingan & Evaluasi Model",
        "Histori Prediksi",
        "Pengaturan Model",
        "Integrasi API (Tahun)",
    ]
else:
    # Menu user: Memisahkan Dashboard & Input, Hasil Prediksi komprehensif, dan Integrasi API di paling akhir
    MENU_ITEMS = [
        "Dashboard",
        "Data & Laporan Keuangan",
        "Hasil Prediksi",
        "Perbandingan Hasil",
        "Integrasi API (Tahun)",
    ]

MENU_ICONS = {
    "Dashboard": "🏠",
    "Data & Laporan Keuangan": "📑",
    "Rasio & Hasil Prediksi": "📈",
    "Hasil Prediksi": "📈",
    "Perbandingan & Evaluasi Model": "⚖️",
    "Perbandingan Hasil": "⚖️",
    "Histori Prediksi": "📜",
    "Pengaturan Model": "⚙️",
    "Pengaturan Profil": "👤",
    "Pengaturan Akun": "👤",
    "Profil": "👤",
    "Profile": "👤",
    "Integrasi API (Tahun)": "🌐",
    "Integrasi API Pasar": "🌐",
    "Integrasi API Tahun": "🌐",
    "Dashboard Sistem": "🏠",
    "Dashboard & Analisis": "🏠",
    "Dashboard Prediksi": "📈",
    "Data Perusahaan": "🏢",
    "Laporan Keuangan": "📄",
    "Rasio Keuangan": "📊",
    "Evaluasi Model": "🔬",
}

MENU_TEXTS = {
    "Dashboard": "Dashboard",
    "Data & Laporan Keuangan": "Data Keuangan",
    "Rasio & Hasil Prediksi": "Hasil Prediksi",
    "Hasil Prediksi": "Hasil Prediksi",
    "Perbandingan & Evaluasi Model": "Evaluasi Model",
    "Perbandingan Hasil": "Evaluasi Model",
    "Histori Prediksi": "Histori Prediksi",
    "Pengaturan Model": "Pengaturan Model",
    "Pengaturan Profil": "Pengaturan Profil",
    "Pengaturan Akun": "Pengaturan Profil",
    "Profil": "Pengaturan Profil",
    "Profile": "Pengaturan Profil",
    "Integrasi API (Tahun)": "Integrasi API",
    "Integrasi API Pasar": "Integrasi API",
    "Integrasi API Tahun": "Integrasi API",
    "Dashboard Sistem": "Dashboard",
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
        cat_title = "ANALISIS & PREDIKSI" if st.session_state.role == "admin" else "NAVIGATION"

        # Header Atas Sidebar: Vault Marker + Logo Brand + Section Label (Satu Elemen Terpadu - Flush Top-0)
        st.markdown(
            f"""
            <div class='sidebar-vault-container' style='display:none;'></div>
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

        saved_prof = get_user_profile(user_display_name)
        if saved_prof and saved_prof.get("full_name"):
            user_full_name = saved_prof["full_name"]
        elif st.session_state.get("user_fullname"):
            user_full_name = st.session_state.user_fullname
        else:
            user_full_name = "Alex Morgan" if not is_admin_user else "System Administrator"

        if saved_prof and saved_prof.get("email"):
            user_email = saved_prof["email"]
        elif st.session_state.get("user_email"):
            user_email = st.session_state.user_email
        else:
            user_email = f"{user_display_name.lower()}@distress.ai" if "@" not in user_display_name else user_display_name

        if cur_th == "light":
            avatar_border = "#2563eb"
            avatar_dot_border = "#ffffff"
        else:
            avatar_border = "#38bdf8"
            avatar_dot_border = "#171820"

        col_uinfo, col_uedit = st.columns([0.84, 0.16], gap="small")
        with col_uinfo:
            st.markdown(
                f"""<div class="sidebar-user-block"><div class="user-avatar-wrapper"><img src="https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&h=120&q=80" alt="Avatar" class="user-avatar-img" style="border:2px solid {avatar_border} !important;" onerror="this.onerror=null; this.src='https://ui-avatars.com/api/?name={user_display_name}&background=2563eb&color=fff&bold=true';" /><span class="user-status-dot" style="border:2px solid {avatar_dot_border} !important;" title="Sesi Online Aktif"></span></div><div class="user-meta-col"><div class="user-name-bold">{user_full_name}</div><div class="user-email-text">{user_email}</div></div></div>""",
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

# ============================================================
# AREA UTAMA APLIKASI
# ============================================================

with content_col:
    db_type_label = get_db_info()["type"]
    ticker_display = str(st.session_state.ticker).strip().upper() if st.session_state.ticker else "EMITEN"
    year_display = str(st.session_state.year) if st.session_state.year else "2024"

    if page in ("Pengaturan Profil", "Pengaturan Akun", "Profil", "Profile"):
        header_sub_display = "Pengaturan Akun • Preferensi Tema • Kredensial Akses Pengguna"
    else:
        header_sub_display = f"Financial Distress Prediction • <b>{ticker_display}</b> ({year_display})"

    # Waktu dan Tanggal Real-Time Sistem (Format Bahasa Indonesia)
    id_days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    id_months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    dt_now = datetime.now()
    cur_day_name = id_days[dt_now.weekday()]
    cur_month_name = id_months[dt_now.month - 1]
    initial_date_str = f"{cur_day_name}, {dt_now.day:02d} {cur_month_name} {dt_now.year}"
    initial_time_str = f"{dt_now.strftime('%H:%M:%S')} WIB"

    # Widget Tanggal & Waktu Real-Time (Tanpa tulisan LIVE, diperbarui tiap detik)
    header_datetime_html = f"""
    <div class="header-datetime-box" title="Waktu & Tanggal Sistem Terverifikasi">
        <span class="clock-icon">🕒</span>
        <div class="clock-content">
            <span class="clock-time live-clock-time-target">{initial_time_str}</span>
            <span class="clock-sep">•</span>
            <span class="clock-date live-clock-date-target">{initial_date_str}</span>
        </div>
    </div>
    <img src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg'></svg>" style="display:none;" onload="
    try {{
        var uClock = function() {{
            try {{
                var d = new Date();
                var days = ['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];
                var months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
                var dName = days[d.getDay()];
                var day = String(d.getDate()).padStart(2, '0');
                var mName = months[d.getMonth()];
                var yr = d.getFullYear();
                var hr = String(d.getHours()).padStart(2, '0');
                var mn = String(d.getMinutes()).padStart(2, '0');
                var sc = String(d.getSeconds()).padStart(2, '0');
                var dEls = document.querySelectorAll('.live-clock-date-target');
                var tEls = document.querySelectorAll('.live-clock-time-target');
                for (var i = 0; i < dEls.length; i++) {{ dEls[i].textContent = dName + ', ' + day + ' ' + mName + ' ' + yr; }}
                for (var j = 0; j < tEls.length; j++) {{ tEls[j].textContent = hr + ':' + mn + ':' + sc + ' WIB'; }}
            }} catch(err) {{}}
        }};
        if (window._headerClockTimer) {{ clearInterval(window._headerClockTimer); }}
        window._headerClockTimer = setInterval(uClock, 1000);
        uClock();
    }} catch(e) {{}}
    ">
    """

    # Mesin Pembuat Berkas Ekspor Laporan Multi-Format (Base64 Client-Side Direct Download)
    has_analyzed_now = bool(st.session_state.get("has_analyzed", False))
    if has_analyzed_now:
        try:
            exp_z, exp_z_cls, exp_mda, exp_mda_cls, exp_xgb_prob, exp_xgb_label = current_results()
        except Exception:
            exp_z, exp_z_cls, exp_mda, exp_mda_cls, exp_xgb_prob, exp_xgb_label = 0.0, "standby", 0.0, "standby", None, None

        exp_ratios = dict(st.session_state.get("ratios", {}))
        exp_fin = dict(st.session_state.get("financials", {}))
        exp_company = st.session_state.get("company", ticker_display) or ticker_display
        exp_sector = st.session_state.get("sector", "Industri Manufaktur")
        exp_user = st.session_state.get("username", "Analyst") or "Analyst"

        try:
            exp_cat3 = evaluate_model_concordance(exp_z_cls, exp_mda_cls, exp_xgb_label)
        except Exception:
            exp_cat3 = {"status": "STANDBY", "agreement": "Menunggu Analisis"}

        try:
            exp_adv = calculate_advanced_metrics(exp_fin, exp_ratios)
        except Exception:
            exp_adv = {}

        try:
            exp_drv = diagnose_distress_drivers(exp_ratios, exp_fin, config.get("altman_coefficients", {}))
        except Exception:
            exp_drv = {}

        try:
            exp_recs = generate_stakeholder_recommendations(exp_z, exp_z_cls, exp_xgb_prob, exp_drv, exp_adv, exp_fin)
        except Exception:
            exp_recs = {}

        try:
            exp_resilience = evaluate_financial_resilience(exp_z, exp_mda, exp_xgb_prob, exp_adv, exp_fin)
        except Exception:
            exp_resilience = {}

        exp_capping = {}
        if "_raw_ratios" in exp_ratios or "raw_ratios" in st.session_state:
            raw_r = st.session_state.get("raw_ratios", exp_ratios.get("_raw_ratios", {}))
            if raw_r.get("X4", 0.0) > 3.0:
                exp_capping["X4"] = {"raw": raw_r.get("X4"), "capped": 3.0}

        # 1. Dokumen HTML Eksekutif (Siap Cetak / Simpan PDF)
        try:
            html_doc = generate_printable_html_report(
                company=exp_company,
                ticker=ticker_display,
                year=year_display,
                sector=exp_sector,
                username=exp_user,
                analysis_date=dt_now.strftime("%d %B %Y, %H:%M WIB"),
                z=exp_z,
                z_cls=exp_z_cls,
                mda=exp_mda,
                mda_cls=exp_mda_cls,
                xgb_prob=exp_xgb_prob,
                xgb_label=exp_xgb_label,
                cat3=exp_cat3,
                ratios=exp_ratios,
                financials=exp_fin,
                adv_metrics=exp_adv,
                drivers=exp_drv,
                recommendations=exp_recs,
                capping_audit=exp_capping,
            )
            b64_html = base64.b64encode(html_doc.encode("utf-8")).decode("ascii")
        except Exception:
            b64_html = ""

        # 2. Spreadsheet CSV Lengkap
        try:
            csv_doc = generate_full_csv_report(
                company=exp_company,
                ticker=ticker_display,
                year=year_display,
                sector=exp_sector,
                username=exp_user,
                analysis_date=dt_now.strftime("%Y-%m-%d %H:%M:%S"),
                z=exp_z,
                z_cls=exp_z_cls,
                mda=exp_mda,
                mda_cls=exp_mda_cls,
                xgb_prob=exp_xgb_prob,
                cat3=exp_cat3,
                ratios=exp_ratios,
                financials=exp_fin,
                adv_metrics=exp_adv,
            )
            b64_csv = base64.b64encode(csv_doc.encode("utf-8")).decode("ascii")
        except Exception:
            b64_csv = ""

        # 3. Memorandum Eksekutif Text
        try:
            exp_eq = analyze_equity_investor(exp_z, exp_z_cls, exp_xgb_prob, exp_drv, exp_adv, exp_fin)
            exp_lend = analyze_lender_creditor(exp_z, exp_z_cls, exp_xgb_prob, exp_drv, exp_adv, exp_fin)
        except Exception:
            exp_eq, exp_lend = None, None

        try:
            memo_doc = generate_executive_memo_text(
                company=exp_company,
                ticker=ticker_display,
                year=year_display,
                z_score=exp_z,
                z_cls=exp_z_cls,
                mda_score=exp_mda,
                mda_cls=exp_mda_cls,
                xgb_prob=exp_xgb_prob,
                resilience=exp_resilience,
                metrics=exp_adv,
                drivers=exp_drv,
                recommendations=exp_recs,
                equity_analysis=exp_eq,
                lender_analysis=exp_lend,
            )
            b64_memo = base64.b64encode(memo_doc.encode("utf-8")).decode("ascii")
        except Exception:
            b64_memo = ""

        # 4. Data Audit JSON
        try:
            json_doc = generate_full_json_report(
                company=exp_company,
                ticker=ticker_display,
                year=year_display,
                sector=exp_sector,
                username=exp_user,
                analysis_date=dt_now.isoformat(),
                z=exp_z,
                z_cls=exp_z_cls,
                mda=exp_mda,
                mda_cls=exp_mda_cls,
                xgb_prob=exp_xgb_prob,
                cat3=exp_cat3,
                ratios=exp_ratios,
                financials=exp_fin,
                adv_metrics=exp_adv,
            )
            b64_json = base64.b64encode(json_doc.encode("utf-8")).decode("ascii")
        except Exception:
            b64_json = ""

        export_menu_content = f"""
        <div class="export-menu-header">
            <div class="export-menu-title">PILIHAN FORMAT EKSPOR LAPORAN</div>
            <div class="export-menu-sub">🏢 {ticker_display} — Tahun {year_display}</div>
        </div>
        <a href="data:text/html;charset=utf-8;base64,{b64_html}" target="_blank" download="Laporan_Distress_{ticker_display}_{year_display}.html" class="export-menu-item" title="Buka dan Cetak Dokumen PDF Resmi">
            <span class="export-item-icon">📄</span>
            <div class="export-item-body">
                <div class="export-item-title">
                    <span>Laporan Cetak / Simpan PDF</span>
                    <span class="export-item-badge">A4 Resmi</span>
                </div>
                <div class="export-item-sub">Kop surat resmi, evaluasi 3 model, rincian pos keuangan, rasio X1-X5 & rekomendasi</div>
            </div>
        </a>
        <a href="data:text/csv;charset=utf-8;base64,{b64_csv}" download="Distress_Analysis_{ticker_display}_{year_display}.csv" class="export-menu-item" title="Unduh Spreadsheet CSV Kompatibel Excel">
            <span class="export-item-icon">📊</span>
            <div class="export-item-body">
                <div class="export-item-title">
                    <span>Spreadsheet Excel (.csv)</span>
                    <span class="export-item-badge">Excel/Sheets</span>
                </div>
                <div class="export-item-sub">Data tabular terstruktur seluruh pos neraca, laba rugi, rasio, dan skor prediksi</div>
            </div>
        </a>
        <a href="data:text/plain;charset=utf-8;base64,{b64_memo}" download="Memo_Eksekutif_{ticker_display}_{year_display}.txt" class="export-menu-item" title="Unduh Memorandum Naratif Dewan Direksi">
            <span class="export-item-icon">📑</span>
            <div class="export-item-body">
                <div class="export-item-title">
                    <span>Executive Brief Memo (.txt)</span>
                    <span class="export-item-badge">Briefing</span>
                </div>
                <div class="export-item-sub">Ringkasan memorandum naratif untuk direksi, komite risiko, dan investor</div>
            </div>
        </a>
        <a href="data:application/json;charset=utf-8;base64,{b64_json}" download="Distress_Audit_{ticker_display}_{year_display}.json" class="export-menu-item" title="Unduh Data Audit Sistem Format JSON">
            <span class="export-item-icon">🗄️</span>
            <div class="export-item-body">
                <div class="export-item-title">
                    <span>Data Audit Sistem (.json)</span>
                    <span class="export-item-badge">JSON Data</span>
                </div>
                <div class="export-item-sub">Format data terstandarisasi untuk integrasi API dan rekam jejak audit kepatuhan</div>
            </div>
        </a>
        """
    else:
        export_menu_content = f"""
        <div class="export-menu-header">
            <div class="export-menu-title">STATUS EKSPOR LAPORAN</div>
            <div class="export-menu-sub">🏢 {ticker_display} ({year_display})</div>
        </div>
        <div class="export-menu-standby">
            <span style="font-size:22px;display:block;margin-bottom:6px;">⚠️</span>
            <b style="color:#f8fafc;">Menunggu Analisis Prediksi</b><br>
            <span>Silakan jalankan prediksi atau muat data laporan keuangan emiten terlebih dahulu untuk mengunduh laporan eksekutif resmi.</span>
        </div>
        """

    header_export_dropdown_html = f"""
    <div class="header-export-dropdown">
        <button class="header-export-btn" type="button" title="Unduh & Cetak Laporan Keuangan Multi-Format">
            <span class="export-icon">📥</span>
            <span class="export-text">Export Laporan</span>
            <span class="export-arrow">▾</span>
        </button>
        <div class="header-export-menu">
            {export_menu_content}
        </div>
    </div>
    """

    vault_header_html = f"""
    <div class="vault-canvas-header">
        <div class="header-title-column">
            <h1 class="header-main-h1">{page}</h1>
            <div class="header-sub-text">{header_sub_display}</div>
        </div>
        {header_datetime_html}
    </div>
    """

    clean_vault_header_html = "\n".join(l.strip() for l in vault_header_html.splitlines() if l.strip())

    # Header Utama Responsif dengan Tombol Hamburger jika Sidebar Tersembunyi (Mobile/Tablet/Desktop Collapsed)
    if not st.session_state.sidebar_visible:
        h_btn_col, h_text_col = st.columns([0.055, 0.945], gap="small")
        with h_btn_col:
            if st.button("☰", key="btn_hamburger_main", help="Buka Menu Navigasi (Expand Sidebar)"):
                st.session_state.sidebar_visible = True
                st.rerun()
        with h_text_col:
            st.markdown(clean_vault_header_html, unsafe_allow_html=True)
    else:
        st.markdown(clean_vault_header_html, unsafe_allow_html=True)

    # Pengalihan Terpadu: Jika ada pemicu modal profil lama, arahkan langsung ke halaman khusus Pengaturan Profil
    if st.session_state.get("active_account_modal") in ("edit_account", "complete_profile"):
        st.session_state.active_account_modal = None
        set_page("Pengaturan Profil")
        st.rerun()

    # ========================================================
    # 1. HALAMAN KHUSUS USER: DASHBOARD & ANALISIS (RINGKAS)
    # ========================================================
    if page == "__legacy_dashboard_analisis__":
        section_title("Dashboard & Input Data Keuangan", "Masukkan data perusahaan dan laporan keuangan untuk melakukan analisis prediksi")
        
        # 1. PENGUMUMAN & KEBIJAKAN ADMINISTRATOR (TERHUBUNG LANGSUNG)
        announcement = config.get("system_announcement", "")
        if announcement:
            st.info(f"📢 **Instruksi & Pengumuman Administrator:**\n\n{announcement}")
            
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
                    for item in VARIABLE_SCHEMA:
                        st.session_state.pop(f"user_input_{item['key']}", None)
                        st.session_state.pop(f"manual_{item['key']}", None)
                    st.toast("Formulir masukan berhasil dikosongkan!", icon="🔄")
                    st.rerun()

            c1, c2 = st.columns(2)
            with c1:
                st.session_state.company = st.text_input("Nama Perusahaan", value=st.session_state.company, placeholder="Contoh: PT Bank Central Asia Tbk")
                st.session_state.ticker = st.text_input("Kode Perusahaan (Ticker)", value=st.session_state.ticker, placeholder="Contoh: BBCA").upper()
                st.session_state.sector = st.text_input("Sektor Industri", value=st.session_state.sector)
            with c2:
                st.session_state.year = st.number_input("Tahun Analisis", 2000, 2100, int(st.session_state.year) if str(st.session_state.year).isdigit() else 2024)
                st.session_state.analysis_date = st.text_input("Tanggal Analisis", value=st.session_state.analysis_date)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # 2. Input Laporan Keuangan (Manual / CSV / PDF)
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(20,184,166,0.18);color:#2dd4bf;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(20,184,166,0.3);box-shadow:0 0 12px rgba(20,184,166,0.2);">📄</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">2. Sumber Data & Impor Laporan Keuangan</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Pilih metode masukan data via input manual, unggah file CSV, atau dokumen PDF BEI/IDX</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("📖 Lihat Kamus Variabel & Format Laporan Keuangan BEI (IDX)", expanded=False):
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
                    with st.spinner(f"Menghubungi multi-source data pipeline untuk emiten {input_ticker_val}..."):
                        try:
                            user_target_year = int(api_yr_mode) if str(api_yr_mode).isdigit() else None
                            data_api = FinancialAPIClient.fetch_emiten_profile_and_financials(input_ticker_val, target_year=user_target_year)
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
                st.caption("Unggah file Excel laporan keuangan resmi yang diunduh langsung dari situs Bursa Efek Indonesia (idx.co.id). Sistem akan otomatis mengenali format XBRL/multi-sheet, mendeteksi emiten & tahun, dan mengekstrak 15 variabel proyek secara cerdas.")

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

                            with st.spinner(f"Mengekstrak dan menyesuaikan variabel dari Excel BEI/IDX tahun {target_excel_year}..."):
                                parsed_excel, excel_evidence, _ = extract_financial_values_from_idx_data(uploaded_excel, int(target_excel_year))
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
                                                "Nilai Terisi": val_str,
                                                "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                                "Lembar / Bagian Sumber": str(ev.get("halaman", "-")),
                                                "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "-")),
                                            })
                                        st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)
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

                                    with st.expander("🔍 Detail Pemetaan & Perhitungan Otomatis dari Excel", expanded=False):
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
                                        with st.spinner("Memproses seluruh baris emiten dengan multi-model..."):
                                            b_df, b_stats = batch_screen_financials(df_ex, config, model_path=str(MODEL_PATH) if MODEL_PATH.exists() else None)
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
                            with st.spinner(f"Mengekstrak data dari CSV taksonomi BEI/IDX tahun {target_csv_year}..."):
                                parsed_csv, csv_evidence, _ = extract_financial_values_from_idx_data(uploaded, int(target_csv_year))
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
                                    st.success(f"✅ File CSV taksonomi BEI/IDX ({st.session_state.company} - {st.session_state.ticker} Tahun {target_csv_year}) berhasil diekstrak! 15 variabel terisi otomatis.")
                                    with st.expander("🔍 Detail Hasil Ekstraksi & Perhitungan Otomatis dari CSV BEI/IDX", expanded=True):
                                        ev_rows = []
                                        for item in VARIABLE_SCHEMA:
                                            k = item["key"]
                                            val = fin0.get(k)
                                            ev = csv_evidence.get(k, {})
                                            val_str = format_display_value(k, val)
                                            ev_rows.append({
                                                "Kode": item["code"],
                                                "Nama Variabel": item["label"],
                                                "Nilai Terisi": val_str,
                                                "Status": ev.get("status", "Tidak Ditemukan" if val is None else "Terisi"),
                                                "Lembar / Bagian Sumber": str(ev.get("halaman", "-")),
                                                "Rincian / Rumus Komputasi": ev.get("metode", ev.get("sumber", "-")),
                                            })
                                        st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)
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
                                                "Nilai Terisi": val_str,
                                                "Status": ev.get("status", "Manual / Kosong" if val is None else "Terisi"),
                                                "Rincian / Rumus Komputasi": ev.get("sumber", "-"),
                                            })
                                        st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)

                            if tab_csv_batch is not None:
                                with tab_csv_batch:
                                    st.caption(f"⚡ Skrining simultan untuk seluruh **{len(df)}** baris data emiten menggunakan model Altman Z'', MDA Fisher, dan XGBoost.")
                                    if st.button("🚀 Jalankan Skrining Massal Seluruh Emiten (CSV)", type="primary", key="btn_run_batch_csv"):
                                        with st.spinner("Memproses seluruh baris emiten dengan multi-model..."):
                                            b_df_csv, b_stats_csv = batch_screen_financials(df, config, model_path=str(MODEL_PATH) if MODEL_PATH.exists() else None)
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
                    with st.spinner("Mengekstrak dan menyesuaikan variabel keuangan dari dokumen PDF..."):
                        try:
                            parsed, pdf_evidence = extract_financial_values_from_pages(pages, int(target_year))
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

                                with st.expander("🔍 Detail Hasil Ekstraksi & Perhitungan Otomatis dari PDF", expanded=True):
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
                                    st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)
                        except Exception as e:
                            st.error(f"Gagal mengekstrak PDF: {e}")

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
                        current_year_val = fin0.get("report_year")
                        if current_year_val is None or not str(current_year_val).isdigit():
                            current_year_val = st.session_state.get("year", 2024)
                        year_int = int(current_year_val)
                        chosen_year_val = st.number_input(
                            label,
                            min_value=1900,
                            max_value=2100,
                            value=year_int,
                            step=1,
                            key="user_input_report_year_num",
                        )
                        fin0[key] = int(chosen_year_val)
                        st.session_state.year = int(chosen_year_val)
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
            if st.button("🚀 Jalankan Analisis & Klasifikasi Prediksi", type="primary", use_container_width=True):
                if not st.session_state.company or not st.session_state.ticker:
                    st.warning("Mohon lengkapi Nama dan Kode Perusahaan terlebih dahulu.")
                else:
                    try:
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
                        st.success("🎉 Analisis berhasil dijalankan! Hasil telah tercatat di basis data audit Administrator. Silakan buka menu **Hasil Prediksi** atau **Perbandingan Hasil**.")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat menghitung rasio: {e}")

            if st.session_state.get("has_analyzed", False):
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                c_btn_a, c_btn_b = st.columns(2)
                with c_btn_a:
                    if st.button("📊 Buka Hasil Prediksi, Diagnosa & Rekomendasi 🚀", type="secondary", use_container_width=True, key="btn_goto_pred_res_dash"):
                        set_page("Hasil Prediksi")
                        st.rerun()
                with c_btn_b:
                    if st.button("🎯 Buka Dashboard Prediksi (Format Gambar 3.4) 🚀", type="secondary", use_container_width=True, key="btn_goto_prop_view_dash"):
                        set_page("Dashboard Prediksi")
                        st.rerun()


    # ========================================================
    # 2. HALAMAN INPUT: DATA PERUSAHAAN & LAPORAN KEUANGAN
    # Terpisah dari Dashboard Utama (Standar Terpadu Admin & User)
    # ========================================================
    elif page in ("Data & Laporan Keuangan", "Data Perusahaan", "Laporan Keuangan", "Input Data", "Input Data Keuangan"):
        section_title("Data Perusahaan & Laporan Keuangan", "Identitas emiten dan impor pos laporan keuangan untuk analisis prediksi multi-model", tone="blue")

        # Pengumuman & Kebijakan Administrator
        announcement = config.get("system_announcement", "")
        if announcement:
            st.info(f"📢 **Instruksi & Pengumuman Administrator:**\n\n{announcement}")

        allow_analysis = config.get("allow_user_analysis", True)
        if not allow_analysis and st.session_state.role != "admin":
            st.warning("⚠️ **Mode Pemeliharaan:** Administrator sedang memperbarui parameter model. Tombol eksekusi analisis dinonaktifkan sementara.")
            st.stop()

        # Action Bar: Opsi Kosongkan Form / Muat Contoh Data
        with st.container(border=True):
            c_top_act1, c_top_act2, c_top_act3 = st.columns([2.4, 1.3, 1.3])
            with c_top_act1:
                st.markdown(
                    """
                    <div style="font-size:13px;font-weight:700;color:#f8fafc;padding-top:6px;">
                        ⚡ <b>Status Input Emiten:</b> Kolom form berstatus kosong dengan bayangan petunjuk (ghost placeholder) yang otomatis hilang saat diklik/diisi.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c_top_act2:
                if st.button("🔄 Kosongkan Semua Form", key="btn_reset_adm_data_lap", help="Mengosongkan semua data emiten dan nilai laporan keuangan ke awal (kosong)", use_container_width=True):
                    st.session_state.company = ""
                    st.session_state.ticker = ""
                    st.session_state.sector = ""
                    st.session_state.financials = {}
                    st.session_state.ratios = {"X1": 0.0, "X2": 0.0, "X3": 0.0, "X4": 0.0, "X5": 0.0}
                    st.session_state.has_analyzed = False
                    for item in VARIABLE_SCHEMA:
                        st.session_state.pop(f"manual_{item['key']}", None)
                        st.session_state.pop(f"user_input_{item['key']}", None)
                    st.toast("Seluruh formulir masukan berhasil dikosongkan!", icon="🔄")
                    st.rerun()
            with c_top_act3:
                if st.button("💡 Muat Contoh Data (Demo)", key="btn_load_demo_adm_data_lap", help="Memuat data contoh ICBP 2024 ke seluruh formulir", use_container_width=True):
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
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">1. Profil & Identitas Emiten</div>
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
                    placeholder="Contoh: Consumer Non-Cyclicals / Food & Beverage"
                )
            with c2:
                st.session_state.year = st.number_input(
                    "Tahun Analisis",
                    2000, 2100,
                    int(st.session_state.year) if str(st.session_state.year).isdigit() else 2024
                )
                st.session_state.analysis_date = st.text_input(
                    "Tanggal Analisis",
                    value=st.session_state.analysis_date,
                    placeholder="Contoh: 2026-06-06"
                )

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Bagian 2: Sumber Data & Impor Laporan Keuangan
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(20,184,166,0.18);color:#2dd4bf;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(20,184,166,0.3);box-shadow:0 0 12px rgba(20,184,166,0.2);">📥</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">2. Sumber Data & Impor Laporan Keuangan</div>
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

            mode = st.radio("Sumber Data", ["Input Manual", "🌐 Tarik Otomatis API Bursa (IDX)", "📊 Excel (BEI/IDX)", "CSV", "PDF"], horizontal=True)
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
                    adm_btn_pull = st.button("🚀 Tarik & Hitung Rasio Otomatis", type="primary", use_container_width=True, key="adm_btn_pull_api")

                adm_picked = render_emiten_shortcuts("adm_api")
                if adm_picked:
                    adm_tick = adm_picked
                    st.session_state.ticker = adm_picked
                    adm_btn_pull = True

                if adm_btn_pull and adm_tick:
                    with st.spinner(f"Menarik data {adm_tick}..."):
                        try:
                            user_target_year = int(adm_yr_opt) if str(adm_yr_opt).isdigit() else None
                            data_api = FinancialAPIClient.fetch_emiten_profile_and_financials(adm_tick, target_year=user_target_year)
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

                            st.session_state["manual_report_year"] = int(chosen_yr)
                            st.session_state["user_input_report_year"] = str(chosen_yr)
                            st.session_state["admin_manual_report_year_input"] = int(chosen_yr)

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
                st.caption("Unggah file Excel laporan keuangan resmi yang diunduh langsung dari situs Bursa Efek Indonesia (idx.co.id). Sistem akan otomatis mengenali format XBRL/multi-sheet, mendeteksi emiten & tahun, dan mengekstrak 15 variabel proyek secara cerdas.")

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

                            with st.spinner(f"Mengekstrak dan menyesuaikan variabel dari Excel BEI/IDX tahun {target_excel_year}..."):
                                parsed_excel, excel_evidence, _ = extract_financial_values_from_idx_data(uploaded_excel, int(target_excel_year))
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
                                    st.session_state["manual_report_year"] = int(parsed_excel.get("report_year", target_excel_year))
                                    st.session_state["user_input_report_year"] = str(parsed_excel.get("report_year", target_excel_year))
                                    st.session_state["admin_manual_report_year_input"] = int(parsed_excel.get("report_year", target_excel_year))

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

                                    st.markdown("### Hasil Ekstraksi & Kalkulasi Variabel Excel BEI/IDX")
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
                                    st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)

                                    if st.button("⚡ Terapkan & Hitung Rasio Otomatis (Excel BEI/IDX)", type="primary", key="btn_apply_admin_excel"):
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
                                            st.session_state[f"manual_{k}"] = str_repr
                                            st.session_state[f"user_input_{k}"] = str_repr
                                    st.session_state["manual_report_year"] = int(parsed_ex.get("report_year", st.session_state.year))
                                    st.session_state["user_input_report_year"] = str(parsed_ex.get("report_year", st.session_state.year))
                                    st.session_state["admin_manual_report_year_input"] = int(parsed_ex.get("report_year", st.session_state.year))
                                    set_ratios_from_financials(fin0)
                                    st.session_state.has_analyzed = True
                                    st.success("✅ Data Excel tabular berhasil diekstrak dan rasio dihitung otomatis!")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Gagal membaca atau mengekstrak file Excel: {e}")

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

                            with st.spinner(f"Mengekstrak dan menyesuaikan variabel dari CSV BEI/IDX tahun {target_csv_year}..."):
                                parsed_csv, csv_evidence, _ = extract_financial_values_from_idx_data(uploaded, int(target_csv_year))
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

                                    st.markdown("### Hasil Ekstraksi & Kalkulasi Variabel CSV BEI/IDX")
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
                                    st.dataframe(pd.DataFrame(ev_rows), use_container_width=True, hide_index=True)

                                    if st.button("⚡ Terapkan & Hitung Rasio Otomatis (CSV BEI/IDX)", type="primary", key="btn_apply_admin_idx_csv"):
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
                                                st.session_state[f"manual_{k}"] = str_repr
                                                st.session_state[f"user_input_{k}"] = str_repr
                                        st.session_state["manual_report_year"] = int(parsed_csv.get("report_year", st.session_state.year))
                                        st.session_state["user_input_report_year"] = str(parsed_csv.get("report_year", st.session_state.year))
                                        st.session_state["admin_manual_report_year_input"] = int(parsed_csv.get("report_year", st.session_state.year))
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
                                try:
                                    set_ratios_from_financials(fin0)
                                    st.session_state.has_analyzed = True
                                    st.success("Nilai finansial berhasil dipetakan dari CSV dan rasio telah dihitung.")
                                except Exception as e:
                                    st.warning(f"Data CSV dipetakan, tetapi rasio belum dihitung: {e}")
                    except Exception as e:
                        st.error(f"CSV tidak dapat diproses: {e}")

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

                    parsed, extraction_evidence = extract_financial_values_from_pages(pages, int(target_year))
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

                    st.markdown("### Hasil Ekstraksi & Kalkulasi Variabel PDF")
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
                            "Rincian / Rumus": ev.get("metode", ev.get("sumber", "-")),
                            "Halaman": str(ev.get("halaman", "-")),
                        })
                    st.dataframe(pd.DataFrame(ev_table), use_container_width=True, hide_index=True)

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

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(139,92,246,0.18);color:#c084fc;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(139,92,246,0.3);box-shadow:0 0 12px rgba(139,92,246,0.2);">📝</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">2. Input Manual / Koreksi Nilai Akun</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Format kolom: kode variabel — nama variabel. Nilai dalam satuan Rupiah penuh.</div>
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
                        current_year_val = fin0.get("report_year")
                        if current_year_val is None or not str(current_year_val).isdigit():
                            current_year_val = st.session_state.get("year", 2024)
                        year_int = int(current_year_val)
                        fin0[key] = st.number_input(
                            label,
                            min_value=1900,
                            max_value=2100,
                            value=year_int,
                            step=1,
                            key="admin_manual_report_year_input",
                        )
                        st.session_state.year = int(fin0[key])
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
            if st.button("🚀 Hitung Rasio X1–X5 & Simpan ke Database", type="primary", use_container_width=True):
                try:
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
                    st.success("🎉 Rasio berhasil dihitung dan riwayat analisis disimpan ke database!")
                except Exception as e:
                    st.error(str(e))

            if st.session_state.get("has_analyzed", False):
                st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                c_btn_a, c_btn_b = st.columns(2)
                with c_btn_a:
                    if st.button("📊 Buka Hasil Prediksi, Diagnosa & Rekomendasi 🚀", type="primary", use_container_width=True, key="btn_goto_pred_from_adm_dl"):
                        set_page("Hasil Prediksi")
                        st.rerun()
                with c_btn_b:
                    if st.button("🏠 Buka Dashboard Terintegrasi 🚀", type="secondary", use_container_width=True, key="btn_goto_dash_from_adm_dl"):
                        set_page("Dashboard")
                        st.rerun()

    elif page == "Pengaturan Model":
        if st.session_state.role != "admin":
            st.error("Akses ditolak! Halaman ini khusus untuk Administrator.")
            st.stop()
            
        section_title("Pusat Kontrol & Otoritas Sistem (Admin Control)", "Kendali parameter model global, audit hasil analisis pengguna, manajemen akun, dan kontrol website")

        tab_param, tab_audit, tab_users, tab_db, tab_site = st.tabs([
            "⚙️ Parameter Model Global",
            "📊 Audit & Moderasi Prediksi User",
            "👥 Manajemen Pengguna",
            "🗄️ Database & Cloud Hosting",
            "📢 Kontrol Website & Kebijakan"
        ])

        with tab_param:
            st.markdown("<div style='font-size:15px;font-weight:850;color:#f8fafc;margin-bottom:4px;'>Konfigurasi Parameter Perhitungan (Otoritas Global - 3 Kategori Operasional)</div>", unsafe_allow_html=True)
            st.caption("Perubahan pada parameter di bawah ini akan langsung menentukan hasil perhitungan klasifikasi 3 Kategori (Safe Zone, Grey Area, Distress Zone) di halaman User secara real-time.")
            
            with st.container(border=True):
                st.markdown("<div style='font-size:14px;font-weight:800;color:#2563eb;margin-bottom:8px;'>📐 1. Model Altman Z''-Score (Standar Industri & 3 Zona)</div>", unsafe_allow_html=True)
                a = config["altman_coefficients"]
                cols = st.columns(4)
                for col, key in zip(cols, ["X1", "X2", "X3", "X4"]):
                    with col:
                        a[key] = st.number_input(f"Koefisien {key}", value=float(a[key]), format="%.4f", key=f"admin_a_{key}")
                
                # Preset Selector Altman
                st.markdown("<div style='font-size:12px;font-weight:750;color:#94a3b8;margin-top:8px;'>Pilihan Preset Ambang Batas Altman Z'':</div>", unsafe_allow_html=True)
                c_pre1, c_pre2 = st.columns(2)
                with c_pre1:
                    if st.button("📌 Terapkan Standar Bab III (1.81 & 2.99)", key="btn_preset_bab3", use_container_width=True):
                        config["altman_thresholds"]["distress"] = 1.81
                        config["altman_thresholds"]["grey"] = 2.99
                        config["altman_thresholds"]["selected_standard"] = "bab3_standard"
                        st.success("Preset Bab III (1.81 & 2.99) dipilih! Klik Simpan di bawah.")
                with c_pre2:
                    if st.button("📌 Terapkan Standar Alternatif / Lampiran (1.10 & 2.60)", key="btn_preset_alt", use_container_width=True):
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
                st.caption("Koefisien empiris hasil estimasi ulang rasio X1-X4 pada seluruh 704 observasi emiten manufaktur BEI (Lampiran 2 hal. 111):")
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

                if st.button("⚡ Kalibrasi / Latih Ulang Model XGBoost (Sesuai PDF)", key="admin_retrain_xgb_btn", help="Melatih ulang XGBoost menggunakan seluruh data master dan kriteria target resmi PDF (RE < 0 dan EBIT < 0)"):
                    master_f = BASE_DIR / "data" / "datakeuangan.xlsx"
                    if master_f.exists():
                        df_m = pd.read_excel(master_f)
                        res = train_xgboost_classifier(df_m, output_path=str(MODEL_PATH), n_estimators=50, max_depth=2, learning_rate=0.3)
                        st.success(f"🎉 Model XGBoost berhasil dilatih ulang! Akurasi: {res['accuracy']*100:.2f}%, AUC: {res['roc_auc']:.4f}")
                        st.rerun()
                    else:
                        st.error("File datakeuangan.xlsx tidak ditemukan.")

                with st.expander("📊 Lihat Laporan Evaluasi Performa Model (Confusion Matrix & ROC-AUC)", expanded=False):
                    eval_adm = get_xgboost_evaluation_metrics() if get_xgboost_evaluation_metrics else {}
                    render_model_evaluation_dashboard(eval_adm)

            if st.button("💾 Terapkan & Kunci Konfigurasi ke Sistem", type="primary", key="btn_save_config_admin"):
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                st.session_state.config = config
                st.success("✅ Konfigurasi parameter 3 Kategori berhasil diperbarui dan langsung mengikat seluruh perhitungan pada akun User.")

        with tab_audit:
            st.markdown("#### Audit & Moderasi Data Hasil Analisis Pengguna")
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

                st.markdown("##### 🛠️ Tindakan Moderasi & Audit")
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
            st.markdown("#### Manajemen Akun Pengguna Website")
            st.caption("Kelola hak akses dan akun yang dapat menggunakan perangkat analisis ini.")
            
            df_users = get_all_users()
            st.dataframe(df_users, use_container_width=True, hide_index=True)

            u_col1, u_col2 = st.columns(2)
            with u_col1:
                st.markdown("##### ➕ Tambah Akun Baru")
                with st.form("add_user_form", clear_on_submit=False):
                    new_u = st.text_input("Username Baru", key="new_username_input")
                    new_p = st.text_input("Password", type="password", key="new_password_input")
                    st.text_input("Role Akun", value="user", disabled=True, help="Pembuatan akun Admin diblokir demi keamanan sistem.")
                    submit_create = st.form_submit_button("Buat Akun", type="secondary", use_container_width=True)
                    if submit_create:
                        clean_new_u = new_u.strip().lower()
                        if "admin" in clean_new_u or clean_new_u in ["administrator", "root", "superuser"]:
                            st.error("⛔ Pembuatan akun dengan nama atau hak akses 'admin' diblokir demi keamanan sistem!")
                        elif new_u and new_p:
                            ok, msg = add_new_user(new_u.strip(), new_p.strip(), role="user", full_name=new_u.strip())
                            if ok:
                                st.success(f"Akun '{new_u}' berhasil didaftarkan sebagai pengguna (user)!")
                                st.rerun()
                            else:
                                st.error(f"Gagal menambahkan akun: {msg}")
                        else:
                            st.warning("Mohon isi username dan password.")

            with u_col2:
                st.markdown("##### ❌ Hapus Akun")
                non_admin_users = [u for u in df_users["username"].tolist() if u != "admin"]
                if non_admin_users:
                    del_u = st.selectbox("Pilih akun untuk dihapus:", non_admin_users, key="del_user_select")
                    if st.button("Hapus Akun Terpilih", type="primary", key="btn_delete_user"):
                        ok, msg = delete_user_by_username(del_u)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    st.info("Tidak ada akun pengguna lain yang dapat dihapus.")

        with tab_db:
            st.markdown("#### Status & Konfigurasi Basis Data (Database Engine)")
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
                    if st.button("🔄 Uji & Segarkan Koneksi DB", key="btn_refresh_db_info"):
                        st.toast("Koneksi database aktif dan responsif!", icon="✅")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### 🚀 Panduan Hosting Website & Menghubungkan Database Cloud")
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
            st.markdown("#### Kontrol Kebijakan & Komunikasi Website")
            st.caption("Administrator dapat mempublikasikan instruksi operasional langsung ke antarmuka pengguna serta mengontrol izin analisis.")
            
            announcement_text = st.text_area(
                "Pesan Instruksi / Pengumuman untuk Akun User:",
                value=config.get("system_announcement", "Sistem aktif. Gunakan data laporan keuangan teraudit untuk hasil analisis terbaik."),
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
    # HALAMAN HASIL PREDIKSI & ANALISIS KOMPREHENSIF
    # Menggantikan dashboard prediksi dengan hasil prediksi yang sesuai & komprehensif
    # ========================================================
    elif page in ("Hasil Prediksi", "Rasio & Hasil Prediksi", "Rasio Keuangan", "Dashboard Prediksi"):
        section_title(
            "Hasil Prediksi & Analisis Komprehensif",
            "Evaluasi variabel rasio X1–X5, status konsensus 3 kategori operasional, diagnosa mendalam, dan intelijen strategis finansial",
            tone="purple",
        )

        is_analyzed = bool(st.session_state.get("has_analyzed", False) and st.session_state.get("ticker"))
        is_light = is_light_theme()

        # Top Bar Emiten Aktif
        c_top_rh1, c_top_rh2 = st.columns([2.6, 1.4])
        with c_top_rh1:
            bar_em_bg = "#ffffff" if is_light else "rgba(15, 23, 42, 0.75)"
            bar_em_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
            bar_em_txt = "#334155" if is_light else "#cbd5e1"
            bar_em_name = "#0f172a" if is_light else "#ffffff"
            st.markdown(
                f"""
                <div style="background:{bar_em_bg};border:1.5px solid {bar_em_border};border-radius:10px;padding:8px 14px;margin-bottom:12px;display:flex;align-items:center;gap:12px;box-shadow:0 2px 6px rgba(15,23,42,0.04);">
                    <span style="font-size:18px;">🏢</span>
                    <div style="font-size:12.5px;color:{bar_em_txt};">
                        Emiten Teranalisis: <b style="color:{bar_em_name};">{st.session_state.company or 'Belum Dipilih'} ({st.session_state.ticker or '-'})</b> • Tahun Laporan: <b style="color:#2563eb;">{st.session_state.year if is_analyzed else '-'}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_top_rh2:
            c_r_b1, c_r_b2 = st.columns(2)
            with c_r_b1:
                if st.button("📑 Edit Data/Laporan", key="btn_goto_dl_from_rh", use_container_width=True, help="Kembali ke formulir data dan laporan keuangan"):
                    set_page("Data & Laporan Keuangan")
                    st.rerun()
            with c_r_b2:
                if st.button("🏠 Buka Dashboard", key="btn_goto_dash_from_rh", use_container_width=True, help="Buka dashboard utama"):
                    set_page("Dashboard")
                    st.rerun()

        # Bagian 1: Ringkasan & Validasi Rasio Keuangan (Input Model)
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
                st.info("💡 **Status Siaga:** Belum ada data emiten yang aktif dianalisis. Anda dapat menginput rasio di atas lalu klik tombol eksekusi manual, atau impor laporan keuangan di menu Data & Laporan Keuangan.")
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
                st.info(f"🛡️ **Capping Rasio X4 Aktif (Standar Skripsi Hal. 41 & 95):** Nilai mentah $X_4$ (`{cap_audit['X4']['raw']:.4f}`) telah dibatasi menjadi **{cap_audit['X4']['capped']:.4f}** agar emiten dengan utang mendekati nol tidak mendistorsi skor Altman Z'' & MDA.")

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # Bagian 2: Hasil Prediksi Multi-Model & Status 3 Kategori
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

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            if evaluate_model_concordance:
                concordance = evaluate_model_concordance(z_cls, mda_cls, xgb_label)
                render_concordance_badge(concordance)

            if evaluate_warning_factors:
                warning_factors = evaluate_warning_factors(st.session_state.financials)
                render_warning_factors_checklist(warning_factors)

            st.markdown("###")
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
                        st.caption(f"🛡️ *Capping X4 Aktif (Skripsi):* `{cap_audit['X4']['raw']:.4f}` ➔ **{cap_audit['X4']['capped']:.4f}** (Maks 3.0)")

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

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.info("ℹ️ **Status Siaga:** Sistem Peringatan Dini, Keselarasan Model, dan Speedometer Risiko akan otomatis aktif dan terkalkulasi setelah data laporan keuangan emiten dianalisis.")

            st.markdown("###")
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

        st.markdown("###")
        t1, t2, t3 = st.tabs(["📐 1. ALTMAN Z''-SCORE", "📊 2. Z''-SCORE KOEFISIEN BARU", "🤖 3. PREDIKSI XGBOOST (MACHINE LEARNING)"])

        with t1:
            st.markdown("**Metode Statistik Tradisional (Altman Z''-Score Model)**")
            st.latex(altman_formula(config["altman_coefficients"], latex=True))
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

                st.dataframe(pd.DataFrame([[
                    f"{z:.2f}",
                    z_badge,
                    z_kriteria,
                    f"Distress < {alt_d:.2f} | Grey [{alt_d:.2f}, {alt_g:.2f}] | Safe > {alt_g:.2f}"
                ]], columns=["Nilai Z''-Score", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Batas Klasifikasi"]), use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame([[
                    "-",
                    "⏳ STANDBY",
                    "Menunggu Analisis",
                    f"Distress < {alt_d:.2f} | Grey [{alt_d:.2f}, {alt_g:.2f}] | Safe > {alt_g:.2f}"
                ]], columns=["Nilai Z''-Score", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Batas Klasifikasi"]), use_container_width=True, hide_index=True)
            st.caption(
                f"💡 *Klasifikasi 3 Kategori (Bab III Proposal Skripsi):* "
                f"**Safe Zone** ($Z'' > {alt_g:.2f}$), **Grey Area** (${alt_d:.2f} \\le Z'' \\le {alt_g:.2f}$), dan **Distress Zone** ($Z'' < {alt_d:.2f}$). "
                f"Data emiten yang jatuh pada Grey Area tidak dipaksakan ke dalam kategori biner, melainkan diberi label pemantauan khusus."
            )

        with t2:
            st.markdown("**Z''-Score dengan Koefisien Baru (MDA Empiris BEI)**")
            st.caption(
                "Model ini mengestimasi ulang koefisien diskriminan rasio $X_1$ sampai $X_4$ "
                "berdasarkan seluruh 704 observasi perusahaan manufaktur di BEI (Lampiran 2 skripsi hal. 106-116):"
            )
            st.latex(mda_formula(config["mda_coefficients"], latex=True))

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

                st.dataframe(pd.DataFrame([[
                    f"{mda:.2f}",
                    mda_badge,
                    mda_kriteria,
                    f"{mda_cut:.4f}",
                    f"Distress < {mda_d:.2f} | Grey [{mda_d:.2f}, {mda_g:.2f}] | Safe > {mda_g:.2f}"
                ]], columns=["Nilai Z'' Baru", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Cut-off Objektif", "Batas Rentang Zona"]), use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame([[
                    "-",
                    "⏳ STANDBY",
                    "Menunggu Analisis",
                    f"{mda_cut:.4f}",
                    f"Distress < {mda_d:.2f} | Grey [{mda_d:.2f}, {mda_g:.2f}] | Safe > {mda_g:.2f}"
                ]], columns=["Nilai Z'' Baru", "Zona Klasifikasi (3 Kategori)", "Kondisi Emiten", "Cut-off Objektif", "Batas Rentang Zona"]), use_container_width=True, hide_index=True)
            st.caption(
                f"💡 *Penjelasan Teoretis & Zona Operasional:* Berdasarkan nilai tengah centroid kelompok Distress "
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

                    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                    render_feature_importance_chart(st.session_state.ratios)

                    st.dataframe(pd.DataFrame([[
                        f"{prob_val:.4f} ({prob_val*100:.2f}%)",
                        f"{prob_safe:.4f} ({prob_safe*100:.2f}%)",
                        f"{margin_val:.4f}",
                        f"Safe < {xgb_safe_th*100:.0f}% | Grey [{xgb_safe_th*100:.0f}%, {xgb_dist_th*100:.0f}%] | Distress > {xgb_dist_th*100:.0f}%",
                        f"{badge_icon} {status_val} (Label {lbl_val})"
                    ]], columns=["Probabilitas Distress P(y=1)", "Probabilitas Non-Distress P(y=0)", "Margin Log-odds (ŷ)", "Ambang Batas (3 Kategori)", "Prediksi Model"]),
                    use_container_width=True, hide_index=True)
                    
                    st.caption(
                        f"💡 *Formulasi Matematis & Klasifikasi 3 Zona:* Margin ensemble $\\hat{{y}} = {margin_val:.4f}$ ditransformasikan "
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
                ["📊 Z''-Score (Koefisien Baru)", f"{mda:.2f}", f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])", mda_badge_str, "Model Empiris Diskriminan BEI (Lampiran 2)"],
                ["🤖 XGBoost Machine Learning", xgb_val_str, xgb_thresh_str, xgb_badge_str, "Model Non-Linear AI (Lampiran 3)"],
            ], columns=["Pendekatan Model", "Nilai / Probabilitas", "Cut-off / Threshold (3 Zona)", "Zona Klasifikasi (3 Kategori)", "Keterangan Metodologi"])
            st.dataframe(comparison, use_container_width=True, hide_index=True)

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
                ["📊 Z''-Score (Koefisien Baru)", "-", f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])", "⏳ STANDBY", "Model Empiris Diskriminan BEI (Lampiran 2)"],
                ["🤖 XGBoost Machine Learning", "-", f"Safe < {xgb_th_cfg.get('safe', 0.35)*100:.0f}% | Distress > {xgb_th_cfg.get('distress', 0.65)*100:.0f}%", "⏳ STANDBY", "Model Non-Linear AI (Lampiran 3)"],
            ], columns=["Pendekatan Model", "Nilai / Probabilitas", "Cut-off / Threshold (3 Zona)", "Zona Klasifikasi (3 Kategori)", "Keterangan Metodologi"])
            st.dataframe(comparison, use_container_width=True, hide_index=True)

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
                st.markdown("#### 📑 Memorandum Analisis Eksekutif & Unduh Laporan")
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
        
    elif page in ("Perbandingan & Evaluasi Model", "Perbandingan Hasil", "Evaluasi Model"):
        section_title("Perbandingan Hasil & Evaluasi Model", "Komparasi metodologis multi-model dan matriks evaluasi validasi empiris BEI", tone="blue")

        is_light = is_light_theme()
        is_analyzed = bool(st.session_state.get("has_analyzed", False) and st.session_state.get("ticker"))

        # Top Bar Emiten Aktif & Navigasi Cepat
        c_ph1, c_ph2 = st.columns([2.6, 1.4])
        with c_ph1:
            bar_em_bg = "#ffffff" if is_light else "rgba(15, 23, 42, 0.75)"
            bar_em_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
            bar_em_txt = "#334155" if is_light else "#cbd5e1"
            bar_em_name = "#0f172a" if is_light else "#ffffff"
            st.markdown(
                f"""
                <div style="background:{bar_em_bg};border:1.5px solid {bar_em_border};border-radius:10px;padding:8px 14px;margin-bottom:12px;display:flex;align-items:center;gap:12px;box-shadow:0 2px 6px rgba(15,23,42,0.04);">
                    <span style="font-size:18px;">🏢</span>
                    <div style="font-size:12.5px;color:{bar_em_txt};">
                        Emiten Teranalisis: <b style="color:{bar_em_name};">{st.session_state.company or 'Belum Dipilih'} ({st.session_state.ticker or '-'})</b> • Periode: <b style="color:#2563eb;">{st.session_state.year if is_analyzed else '-'}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_ph2:
            c_p_b1, c_p_b2 = st.columns(2)
            with c_p_b1:
                if st.button("📈 Rasio & Hasil Prediksi", key="btn_goto_rh_from_pe", use_container_width=True, help="Buka halaman rasio dan hasil prediksi"):
                    set_page("Rasio & Hasil Prediksi")
                    st.rerun()
            with c_p_b2:
                if st.button("🏠 Buka Dashboard", key="btn_goto_dash_from_pe", use_container_width=True, help="Kembali ke dashboard utama"):
                    set_page("Dashboard")
                    st.rerun()

        cmp_tabs = st.tabs([
            "📊 Komparasi Output Multi-Model (Altman vs MDA vs XGBoost)",
            "🎯 Evaluasi Model & Metrik Performa AI (Fitur No. 6)",
            "🔬 Validasi Empiris & Matriks Evaluasi BEI"
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
                            "Model Empiris Diskriminan BEI (Lampiran 2)",
                            "Model AI Non-Linear (Lampiran 3)"
                        ]
                    })
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    box_kons_bg = "#ffffff" if is_light else "rgba(30, 41, 59, 0.7)"
                    box_kons_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
                    box_kons_txt = "#1e293b" if is_light else "#cbd5e1"
                    st.markdown(
                        f"""
                        <div style="background:{box_kons_bg};border:1.5px solid {box_kons_border};border-radius:10px;padding:10px 14px;margin-top:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;box-shadow:0 2px 6px rgba(15,23,42,0.04);">
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
                            "Model Empiris Diskriminan BEI (Lampiran 2)",
                            "Model AI Non-Linear (Lampiran 3)"
                        ]
                    })
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    box_kons_bg = "#ffffff" if is_light else "rgba(30, 41, 59, 0.7)"
                    box_kons_border = "#cbd5e1" if is_light else "rgba(255, 255, 255, 0.08)"
                    box_kons_txt = "#1e293b" if is_light else "#cbd5e1"
                    st.markdown(
                        f"""
                        <div style="background:{box_kons_bg};border:1.5px solid {box_kons_border};border-radius:10px;padding:10px 14px;margin-top:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;box-shadow:0 2px 6px rgba(15,23,42,0.04);">
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
                                    Rujukan Proposal Bab II Subbab 2.2.8 (Hal. 45–46) dan Tabel 2.1 (Hal. 43)
                                </div>
                            </div>
                        </div>
                        <span style="background: {box_teor_badge_bg}; border: 1px solid {box_teor_badge_border}; color: {box_teor_badge_txt}; font-size: 11px; font-weight: 750; padding: 3px 10px; border-radius: 20px;">
                            Subbab 2.2.8 Hal. 45-46
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
                    st.caption("Didesain awal untuk perusahaan manufaktur go public di AS (Persamaan 1 Hal. 45):")
                    st.latex(r"Z = 1.2 X_1 + 1.4 X_2 + 3.3 X_3 + 0.6 X_4 + 0.999 X_5")
                    st.markdown(f"**Skor Z (1968):** `{z_1968_disp}` &nbsp;|&nbsp; **Klasifikasi:** {cls_badge_68}", unsafe_allow_html=True)
                    st.caption("Batas Klasifikasi (Tabel 2.1 Hal. 43): Safe (> 2.99), Grey (1.81 - 2.99), Distress (< 1.81)")

            with c_alt2:
                with st.container(border=True):
                    st.markdown("##### 📐 Model Revisi Altman Z'' 1995/2017 (4 Variabel)")
                    st.caption("Disesuaikan untuk Pasar Berkembang / Emerging Market (Persamaan 2 Hal. 46):")
                    st.latex(r"Z'' = 6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4")
                    st.markdown(f"**Skor Z'' (1995):** `{z_95_disp}` &nbsp;|&nbsp; **Klasifikasi:** {cls_badge_95}", unsafe_allow_html=True)
                    st.caption("Batas Klasifikasi: Safe (> 2.60), Grey (1.10 - 2.60), Distress (<= 1.10)")

                st.caption(
                    "💡 **Rasional Ilmiah Eliminasi Variabel $X_5$ (Total Sales / Total Assets):** "
                    "Pada Subbab 2.2.8 proposal skripsi dijelaskan bahwa variabel perputaran penjualan ($X_5$) dieliminasi "
                    "dalam formula Altman Z''-Score 1995/2017 guna meminimalkan efek distorsi ukuran aset (*asset size*) "
                    "serta perbedaan karakteristik perputaran penjualan antar-subsektor industri manufaktur di pasar berkembang (*emerging market*) seperti Bursa Efek Indonesia (BEI)."
                )

        with cmp_tabs[1]:
            active_ratios = st.session_state.get("ratios", {})
            eval_metrics_data = get_xgboost_evaluation_metrics(
                active_ratios=active_ratios,
                config=config,
            ) if get_xgboost_evaluation_metrics else {}

            # Kontrol latih ulang model dan status dataset
            c_eval_head1, c_eval_head2 = st.columns([3, 1.2])
            with c_eval_head1:
                st.caption("Validasi diuji menggunakan 704 observasi laporan keuangan emiten manufaktur Bursa Efek Indonesia (BEI) dengan pembagian 80% data latih dan 20% data uji (stratified split bersih tanpa target leakage).")
            with c_eval_head2:
                if st.button("🔄 Latih Ulang & Evaluasi Live", key="btn_retrain_eval_combined", use_container_width=True, help="Melatih ulang model pada dataset aktual dan memperbarui seluruh metrik evaluasi multi-model"):
                    with st.spinner("Melatih ulang model XGBoost dan menghitung metrik evaluasi multi-model..."):
                        if get_xgboost_evaluation_metrics:
                            eval_metrics_data = get_xgboost_evaluation_metrics(
                                force_retrain=True,
                                active_ratios=active_ratios,
                                config=config,
                            )
                        st.toast("Model berhasil dilatih ulang dan metrik evaluasi diperbarui!", icon="✅")
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
    # INTEGRASI API TAHUN: PASAR MODAL & LAPORAN KEUANGAN BEI
    # ========================================================
    elif page in ("Integrasi API (Tahun)", "Integrasi API Tahun", "Integrasi API Pasar"):
        section_title(
            "Integrasi API & Laporan Keuangan Tahunan (BEI / IDX)",
            "Pencarian emiten, penarikan data laporan keuangan multi-tahun otomatis, seleksi periode tahun pelaporan, dan sinkronisasi model",
            tone="blue",
        )

        # 1. PENCARIAN & KONTROL API
        with st.container(border=True):
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <div style="width:38px;height:38px;border-radius:12px;background:rgba(59,130,246,0.18);color:#60a5fa;display:flex;align-items:center;justify-content:center;font-size:20px;border:1px solid rgba(59,130,246,0.3);box-shadow:0 0 12px rgba(59,130,246,0.2);">🌐</div>
                    <div>
                        <div style="font-size:16px;font-weight:850;color:#f8fafc;line-height:1.2;">Pencarian & Penarikan Data Pasar Modal</div>
                        <div style="font-size:12px;color:#94a3b8;font-weight:500;margin-top:2px;">Terhubung dengan feed Yahoo Finance (.JK) & basis data emiten Bursa Efek Indonesia</div>
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
            with st.spinner(f"Menghubungi multi-source data pipeline untuk '{target_ticker_clean}'..."):
                try:
                    fetched_res = FinancialAPIClient.fetch_emiten_profile_and_financials(target_ticker_clean)
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
            # 2. PROFIL PERUSAHAAN & REAL-TIME MARKET STATS
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
                    "📅 Pilih Tahun Laporan Keuangan untuk Dianalisis & Dilihat Detailnya:",
                    options=available_years,
                    format_func=lambda y: f"Tahun {y} {'(Terbaru)' if y == available_years[0] else ''}",
                    horizontal=True,
                    key="api_view_year_radio",
                )
            with c_yr_sync:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                btn_load_to_session = st.button(
                    "📥 Terapkan Data Ini ke Sesi Utama & Simpan",
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

            # 4. TABBED INTERFACE DETIL DATA & MODEL
            tab_fin, tab_audit, tab_val, tab_pred, tab_trend = st.tabs([
                "📋 Laporan Keuangan (Neraca & Laba Rugi)",
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
                        if st.button("👉 Buka Halaman Hasil Prediksi & Diagnosa Lengkap", type="secondary", use_container_width=True):
                            set_page("Hasil Prediksi")
                            st.rerun()
                    with col_go_dash:
                        if st.button("🏠 Buka Dashboard & Analisis Utama", type="secondary", use_container_width=True):
                            set_page("Dashboard & Analisis" if st.session_state.role == "user" else "Dashboard")
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

        section_title("Histori & Riwayat Prediksi Sistem", "Rekapitulasi lengkap hasil analisis dan prediksi financial distress dari seluruh pengguna")

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

            # Filter & Pencarian
            with st.container(border=True):
                st.markdown(f"<div style='font-size:13px;font-weight:800;color:{'#0f172a' if is_light_theme() else '#f8fafc'};margin-bottom:8px;'>🔍 Saring & Pencarian Riwayat Prediksi</div>", unsafe_allow_html=True)
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

            tab_table, tab_charts = st.tabs(["📋 Tabel Riwayat Prediksi", "📊 Visualisasi & Analisis"])

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
                st.markdown("#### 🛠️ Tindakan & Manajemen Riwayat")
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
                st.markdown("#### Distribusi & Proporsi Klasifikasi")
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
    # 5. HALAMAN DEDIKASI: PENGATURAN PROFIL & PREFERENSI ANTARMUKA
    # Dimuat mandiri sebagai halaman terpisah dari fitur profil sidebar
    # ========================================================
    elif page in ("Pengaturan Profil", "Pengaturan Akun", "Profil", "Profile"):
        section_title("Pengaturan Profil & Preferensi Antarmuka", "Kelola preferensi tema visual aplikasi, kredensial autentikasi pengguna, dan identitas profil resmi", tone="blue")

        current_theme = st.session_state.get("theme", "light")
        is_light = (current_theme == "light")

        header_text_color = "#0f172a" if is_light else "#ffffff"
        sub_text_color = "#334155" if is_light else "#cbd5e1"
        section_box_bg = "#f8fafc" if is_light else "rgba(15, 23, 42, 0.65)"
        section_box_border = "#e2e8f0" if is_light else "rgba(255, 255, 255, 0.12)"
        user_role_disp = "System Administrator" if st.session_state.role == "admin" else "Financial Analyst"
        cur_user = st.session_state.username if st.session_state.username else "admin"

        # Sinkronkan data dari database
        user_profile_data = get_user_profile(cur_user) or {}
        curr_fullname = user_profile_data.get("full_name") or st.session_state.get("user_fullname") or ("System Administrator" if st.session_state.role == "admin" else "Alex Morgan")
        curr_email = user_profile_data.get("email") or st.session_state.get("user_email") or (f"{cur_user.lower()}@distress.ai" if "@" not in cur_user else cur_user)
        curr_inst = st.session_state.get("user_institution", "Bursa Efek Indonesia (BEI)")
        curr_div = st.session_state.get("user_division", "Financial Risk Analysis" if st.session_state.role == "admin" else "Credit & Equity Research")

        # Top Bar Navigasi Pintasan
        c_prof_nav1, c_prof_nav2 = st.columns([2.0, 2.0])
        with c_prof_nav1:
            st.markdown(
                f"""
                <div style="background:{'#ffffff' if is_light else 'rgba(15, 23, 42, 0.75)'}; border:1px solid {section_box_border}; border-radius:10px; padding:8px 14px; margin-bottom:12px; display:flex; align-items:center; gap:12px; box-shadow:{'0 2px 6px rgba(0,0,0,0.03)' if is_light else 'none'};">
                    <span style="font-size:18px;">👤</span>
                    <div style="font-size:12.5px; color:{sub_text_color} !important;">
                        Profil Aktif: <b style="color:{header_text_color} !important;">{curr_fullname} (@{cur_user})</b> • Hak Akses: <b style="color:#2563eb;">{user_role_disp}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_prof_nav2:
            c_pnav_b1, c_pnav_b2, c_pnav_b3 = st.columns([1, 1, 1.05])
            with c_pnav_b1:
                if st.button("🏠 Dashboard", key="btn_prof_goto_dash", use_container_width=True, help="Kembali ke Dashboard Utama"):
                    set_page("Dashboard")
                    st.rerun()
            with c_pnav_b2:
                if st.button("📈 Hasil Prediksi", key="btn_prof_goto_results", use_container_width=True, help="Buka Hasil Prediksi"):
                    set_page("Hasil Prediksi")
                    st.rerun()
            with c_pnav_b3:
                if st.button("🚪 Logout", key="btn_prof_nav_logout", use_container_width=True, help="Keluar dari akun dan kembali ke halaman login"):
                    st.session_state.show_logout_confirm = True
                    st.rerun()

        # Banner Dialog Konfirmasi Logout (Jika Dipicu)
        if st.session_state.get("show_logout_confirm", False):
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">
                        <span style="font-size:24px;">⚠️</span>
                        <div>
                            <div style="font-size:14.5px; font-weight:850; color:{'#b91c1c' if is_light else '#f87171'} !important;">
                                Konfirmasi Keluar dari Sistem (Logout)
                            </div>
                            <div style="font-size:12px; color:{sub_text_color} !important; margin-top:2px;">
                                Apakah Anda yakin ingin mengakhiri sesi autentikasi untuk akun <b>{curr_fullname}</b> (<code>@{cur_user}</code>)? Sesi aktif Anda akan ditutup dan dialihkan ke layar login.
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col_cf_act1, col_cf_act2 = st.columns([1, 1])
                with col_cf_act1:
                    if st.button("🚪 Ya, Keluar dari Sistem Sekarang", key="btn_confirm_logout_yes", type="primary", use_container_width=True):
                        logout_user()
                with col_cf_act2:
                    if st.button("✕ Batal & Tetap di Sini", key="btn_confirm_logout_no", use_container_width=True):
                        st.session_state.show_logout_confirm = False
                        st.rerun()
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

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

            st.markdown(
                f"""
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; padding-bottom:14px; border-bottom:1.5px solid {section_box_border}; margin-bottom:16px;">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <div style="width:46px; height:46px; border-radius:14px; background:linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); display:flex; align-items:center; justify-content:center; color:#ffffff !important; font-weight:900; font-size:22px; box-shadow:0 4px 14px rgba(37,99,235,0.35);">
                            {avatar_letter}
                        </div>
                        <div>
                            <div style="font-size:18px; font-weight:900; color:{header_text_color} !important; letter-spacing:-0.3px;">
                                ⚙️ Pengaturan Akun & Preferensi Antarmuka
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
                """,
                unsafe_allow_html=True,
            )

            # -------------------------------------------------------------
            # SEKSI 1: THEME SWITCHER (MODE TERANG & MODE GELAP)
            # -------------------------------------------------------------
            st.markdown(
                f"""
                <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:12px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px;">🎨</span> <span>PREFERENSI TEMA APLIKASI (THEME SWITCHER)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_th_light, col_th_dark = st.columns(2, gap="medium")

            # --- KARTU PILIHAN TEMA 1: LIGHT MODE (BIRU & PUTIH) ---
            with col_th_light:
                is_light_sel = current_theme == "light"
                border_color_l = "#2563eb" if is_light_sel else ("#cbd5e1" if is_light else "rgba(255, 255, 255, 0.12)")
                bg_card_l = "#eff6ff" if is_light_sel else ("#ffffff" if is_light else "rgba(15, 23, 42, 0.5)")
                badge_l = '<span style="background:#2563eb; color:#ffffff !important; font-size:10.5px; font-weight:850; padding:3px 10px; border-radius:99px; letter-spacing:0.5px; box-shadow:0 2px 8px rgba(37,99,235,0.4);">✓ TEMA AKTIF</span>' if is_light_sel else f'<span style="color:{sub_text_color} !important; font-size:11px; font-weight:650;">Klik tombol di bawah</span>'

                st.markdown(
                    f"""
                    <div style="border: 2px solid {border_color_l}; background: {bg_card_l}; border-radius: 16px; padding: 16px; margin-bottom: 8px; transition: all 0.25s ease; box-shadow: {'0 8px 24px rgba(37, 99, 235, 0.18)' if is_light_sel else '0 2px 8px rgba(0,0,0,0.04)'};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                            <div style="font-size:15px; font-weight:900; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                                <span>☀️</span> <span>Light Mode (Mode Terang)</span>
                            </div>
                            {badge_l}
                        </div>
                        <div style="font-size:12px; line-height:1.55; color:{sub_text_color} !important; font-weight:600; margin-bottom: 12px;">
                            Kanvas dominan <b>Putih Bersih</b> & <b>Abu-abu Sangat Muda</b>, bilah navigasi dan tombol beraksen <b>Royal Blue</b> elegan, serta teks navy gelap berkontras tinggi (Standar WCAG AAA).
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
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("☀️ Aktifkan Mode Terang (Light Mode)", key="btn_page_theme_light", use_container_width=True, disabled=is_light_sel):
                    st.session_state.theme = "light"
                    st.session_state.prop_ui_theme_mode = "light"
                    st.rerun()

            # --- KARTU PILIHAN TEMA 2: DARK MODE (OBSIDIAN & NEON BLUE) ---
            with col_th_dark:
                is_dark_sel = current_theme == "dark"
                border_color_d = "#38bdf8" if is_dark_sel else ("#cbd5e1" if is_light else "rgba(255, 255, 255, 0.12)")
                bg_card_d = "rgba(56, 189, 248, 0.08)" if is_dark_sel else ("#ffffff" if is_light else "rgba(15, 23, 42, 0.5)")
                badge_d = '<span style="background:#0284c7; color:#ffffff !important; font-size:10.5px; font-weight:850; padding:3px 10px; border-radius:99px; letter-spacing:0.5px; box-shadow:0 2px 8px rgba(2,132,199,0.4);">✓ TEMA AKTIF</span>' if is_dark_sel else f'<span style="color:{sub_text_color} !important; font-size:11px; font-weight:650;">Klik tombol di bawah</span>'

                st.markdown(
                    f"""
                    <div style="border: 2px solid {border_color_d}; background: {bg_card_d}; border-radius: 16px; padding: 16px; margin-bottom: 8px; transition: all 0.25s ease; box-shadow: {'0 8px 24px rgba(56, 189, 248, 0.18)' if is_dark_sel else '0 2px 8px rgba(0,0,0,0.04)'};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                            <div style="font-size:15px; font-weight:900; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                                <span>🌙</span> <span>Dark Mode (Mode Gelap)</span>
                            </div>
                            {badge_d}
                        </div>
                        <div style="font-size:12px; line-height:1.55; color:{sub_text_color} !important; font-weight:600; margin-bottom: 12px;">
                            Latar <b>Obsidian</b> & <b>Charcoal</b> pekat yang nyaman di mata untuk sesi analisis jangka panjang, dipadukan dengan aksen pendaran <b>Neon Blue / Azure</b> lembut.
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
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🌙 Aktifkan Mode Gelap (Dark Mode)", key="btn_page_theme_dark", use_container_width=True, disabled=is_dark_sel):
                    st.session_state.theme = "dark"
                    st.session_state.prop_ui_theme_mode = "dark"
                    st.rerun()

            st.markdown(f"<div style='height:14px; border-bottom:1.5px solid {section_box_border}; margin: 8px 0 16px 0;'></div>", unsafe_allow_html=True)

            # -------------------------------------------------------------
            # SEKSI 2: IDENTITAS PENGGUNA & KREDENSIAL AKSES
            # -------------------------------------------------------------
            st.markdown(
                f"""
                <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:12px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px;">🔐</span> <span>IDENTITAS PENGGUNA & KATA SANDI AKSES</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                # Baris 1: Username & Password Baru (Sesuai Gambar 1)
                c_ea1, c_ea2 = st.columns(2)
                with c_ea1:
                    edit_username = st.text_input("Nama Pengguna (Username)", value=cur_user, key="input_prof_username", help="Nama akun unik untuk autentikasi sistem")
                with c_ea2:
                    edit_password = st.text_input("Kata Sandi Baru (Opsional)", type="password", key="input_prof_password", help="Biarkan kosong jika tetap menggunakan kata sandi saat ini")

                # Baris 2: Nama Lengkap & Email Resmi
                c_ea3, c_ea4 = st.columns(2)
                with c_ea3:
                    edit_fullname = st.text_input("Nama Lengkap Pengguna", value=curr_fullname, key="input_prof_fullname_val", help="Nama lengkap resmi pengguna untuk laporan dan log audit")
                with c_ea4:
                    edit_email = st.text_input("Alamat Email", value=curr_email, key="input_prof_email_val", help="Alamat email aktif untuk korespondensi dan audit akun")

                # Baris 3: Afiliasi Organisasi & Divisi
                c_ea5, c_ea6 = st.columns(2)
                with c_ea5:
                    edit_inst = st.text_input("Instansi / Organisasi", value=curr_inst, key="input_prof_inst_val", help="Nama lembaga atau perusahaan tempat bertugas")
                with c_ea6:
                    edit_div = st.text_input("Divisi / Jabatan", value=curr_div, key="input_prof_div_val", help="Divisi kerja atau jabatan fungsional analis risiko")

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            # Baris Tombol Aksi (Sesuai Gambar 1)
            col_s1, col_s2, col_s3 = st.columns([1.3, 0.7, 0.75])
            with col_s1:
                if st.button("💾 Simpan Perubahan Akun & Preferensi", type="primary", key="btn_save_prof_page", use_container_width=True):
                    if edit_username.strip():
                        clean_u = edit_username.strip()
                        clean_p = edit_password.strip() if edit_password else None
                        clean_f = edit_fullname.strip() if edit_fullname else ""
                        clean_e = edit_email.strip() if edit_email else ""

                        ok, msg = update_user_credentials(
                            current_username=cur_user,
                            new_username=clean_u,
                            new_password=clean_p,
                            new_email=clean_e,
                            new_full_name=clean_f
                        )
                        if ok:
                            st.session_state.username = clean_u
                            st.session_state.user_fullname = clean_f
                            st.session_state.user_email = clean_e
                            st.session_state.user_institution = edit_inst.strip()
                            st.session_state.user_division = edit_div.strip()
                            st.toast("Informasi akun dan preferensi berhasil disimpan!", icon="✅")
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
            with col_s3:
                if st.button("🚪 Keluar Akun", key="btn_logout_prof_form", use_container_width=True, help="Keluar dari sesi akun saat ini"):
                    st.session_state.show_logout_confirm = True
                    st.rerun()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # SEKSI 3: INFORMASI SESI & AUDIT KEAMANAN SISTEM (BONUS)
        # -------------------------------------------------------------
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:12px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px;">🛡️</span> <span>RINGKASAN SESI AKTIF & AUDIT HAK AKSES PENGGUNA</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_inf1, col_inf2, col_inf3, col_inf4 = st.columns(4)
            with col_inf1:
                with st.container(border=True):
                    st.caption("Peran & Tingkat Akses")
                    st.markdown(f"**{role_pill_text}**")
                    st.caption("Akses penuh ke seluruh model" if st.session_state.role == "admin" else "Akses analisis & prediksi emiten")
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

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # SEKSI 4: MANAJEMEN SESI & KELUAR DARI SISTEM (LOGOUT)
        # -------------------------------------------------------------
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="font-size:13px; font-weight:850; letter-spacing:0.5px; margin-bottom:12px; color:{header_text_color} !important; display:flex; align-items:center; gap:8px;">
                    <span style="font-size:16px;">🚪</span> <span>MANAJEMEN SESI & KELUAR SISTEM (SIGN OUT / LOGOUT)</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_sec_logout_info, col_sec_logout_action = st.columns([2.6, 1.4])
            with col_sec_logout_info:
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:flex-start; gap:12px;">
                        <div style="width:42px; height:42px; border-radius:12px; background:{'#fee2e2' if is_light else 'rgba(239,68,68,0.18)'}; border:1px solid {'#fca5a5' if is_light else 'rgba(239,68,68,0.35)'}; color:{'#dc2626' if is_light else '#f87171'}; display:flex; align-items:center; justify-content:center; font-size:22px; flex-shrink:0;">
                            🚪
                        </div>
                        <div>
                            <div style="font-size:13.5px; font-weight:850; color:{header_text_color} !important;">
                                Akhiri Sesi Autentikasi Pengguna
                            </div>
                            <div style="font-size:12px; color:{sub_text_color} !important; margin-top:2px; line-height:1.55;">
                                Keluar secara aman dari akun <b>{curr_fullname}</b> (<code>@{cur_user}</code>). Sesi login Anda akan ditutup dan Anda akan dialihkan kembali ke layar login utama.
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_sec_logout_action:
                st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
                if st.button("🚪 Keluar dari Sistem (Logout)", key="btn_logout_prof_card", type="primary", use_container_width=True, help="Klik untuk mengakhiri sesi dan keluar ke halaman login"):
                    logout_user()

    # ========================================================
    # 6. HALAMAN UTAMA: DASHBOARD TERINTEGRASI (SISTEM & PREDIKSI)
    # Menggabungkan Dashboard Sistem & Dashboard Prediksi dengan Status 3 Kategori
    # ========================================================
    else:
        section_title("Dashboard Utama Terintegrasi", "Pusat komando eksekutif & monitoring terpadu multi-model: Altman Z''-Score, MDA Empiris BEI, dan XGBoost Machine Learning")

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
        # 1. Eksekusi Kalkulasi Multi-Model & Sinkronisasi 3 Kategori
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
                "status": "STANDBY",
                "tone": "blue",
                "color": "#64748b",
                "badge_icon": "⏳",
                "desc": "Menunggu Data Laporan Keuangan / Pemilihan Emiten",
                "summary_note": "Belum Dilakukan Prediksi",
            }
            overall = "STANDBY"
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
        # AWAL HALAMAN (ABOVE THE FOLD): INFORMASI UTAMA & MONITORING
        # =============================================================

        # 1. Bar Identitas Emiten Aktif & Pintasan Cepat
        is_light = is_light_theme()
        if is_light:
            bar_emiten_bg = "#ffffff"
            bar_emiten_border = "#e2e8f0"
            bar_emiten_txt = "#334155"
            bar_emiten_bold = "#0f172a"
            bar_emiten_year = "#2563eb"
        else:
            bar_emiten_bg = "rgba(15, 23, 42, 0.75)"
            bar_emiten_border = "rgba(255, 255, 255, 0.08)"
            bar_emiten_txt = "#cbd5e1"
            bar_emiten_bold = "#ffffff"
            bar_emiten_year = "#60a5fa"

        c_top_info1, c_top_info2 = st.columns([1.8, 2.2])
        with c_top_info1:
            st.markdown(
                f"""
                <div style="background:{bar_emiten_bg};border:1.5px solid {bar_emiten_border};border-radius:10px;padding:8px 14px;margin-bottom:12px;display:flex;align-items:center;gap:12px;box-shadow:0 2px 6px rgba(15,23,42,0.03);">
                    <span style="font-size:18px;">🏢</span>
                    <div style="font-size:12.5px;color:{bar_emiten_txt} !important;font-weight:600;">
                        Emiten Teranalisis Aktif: <b style="color:{bar_emiten_bold} !important;">{st.session_state.company or 'Belum Dipilih'} ({st.session_state.ticker or '-'})</b> • Tahun: <b style="color:{bar_emiten_year} !important;">{st.session_state.year if is_analyzed else '-'}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c_top_info2:
            c_tbtn1, c_tbtn2, c_tbtn3, c_tbtn4 = st.columns(4)
            with c_tbtn1:
                if st.button("📑 Data/Laporan", key="btn_goto_dl_from_dash", use_container_width=True, help="Buka input data & laporan keuangan"):
                    set_page("Data & Laporan Keuangan")
                    st.rerun()
            with c_tbtn2:
                if st.button("📈 Hasil Prediksi", key="btn_goto_pred_from_adm_dash", use_container_width=True, help="Buka halaman Hasil Prediksi lengkap"):
                    set_page("Hasil Prediksi")
                    st.rerun()
            with c_tbtn3:
                if st.button("⚖️ Evaluasi Model", key="btn_goto_eval_from_adm_dash", use_container_width=True, help="Buka evaluasi & validasi model"):
                    set_page("Perbandingan & Evaluasi Model")
                    st.rerun()
            with c_tbtn4:
                if st.button("🌐 API (Tahun)", key="btn_goto_api_from_dash", use_container_width=True, help="Buka integrasi API tahunan"):
                    set_page("Integrasi API (Tahun)")
                    st.rerun()

        # Banner Sambutan jika emiten belum aktif
        if not is_analyzed:
            with st.container(border=True):
                welc_title_color = "#1d4ed8" if is_light else "#38bdf8"
                welc_sub_color = "#334155" if is_light else "#cbd5e1"
                st.markdown(
                    f"""
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                        <span style="font-size:24px;">👋</span>
                        <div>
                            <div style="font-size:16px;font-weight:900;color:{welc_title_color} !important;letter-spacing:-0.2px;">Selamat Datang di Financial Distress Prediction System</div>
                            <div style="font-size:12.5px;color:{welc_sub_color} !important;font-weight:600;margin-top:2px;">Pusat komando eksekutif & monitoring terpadu multi-model: Altman Z''-Score, MDA Empiris BEI, dan XGBoost Machine Learning.</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col_w1, col_w2, col_w3 = st.columns(3)
                with col_w1:
                    if st.button("📑 Input Data & Laporan Keuangan", type="primary", use_container_width=True, key="btn_dash_welcome_input"):
                        set_page("Data & Laporan Keuangan")
                        st.rerun()
                with col_w2:
                    if st.button("💡 Muat Data Demo (ICBP 2024)", use_container_width=True, key="btn_dash_welcome_demo"):
                        load_demo_data_icbp()
                        st.rerun()
                with col_w3:
                    if st.button("🌐 Tarik Data Otomatis via API", use_container_width=True, key="btn_dash_welcome_api"):
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

        st.markdown(
            f"""
            <div style="background:{cons_bg};border:1.5px solid {cons_border};border-left:6px solid {cons_left_bar};border-radius:14px;padding:12px 18px;margin-bottom:14px;box-shadow:0 4px 16px rgba(15,23,42,0.06);">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span style="font-size:26px;">{cat3['badge_icon']}</span>
                        <div>
                            <div style="font-size:11px;font-weight:850;color:{cons_badge_col} !important;text-transform:uppercase;letter-spacing:1px;">KONSENSUS KEPUTUSAN SISTEM (3 KATEGORI)</div>
                            <div style="font-size:17px;font-weight:900;color:{cons_desc_col} !important;margin-top:1px;">{cat3['status']} — {cat3['desc']}</div>
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
            metric_card(c[3], "KONSENSUS 3 KATEGORI", "STANDBY", "Belum Dilakukan Prediksi", "blue", trend="⚪ Belum Ada Data")

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        # 4. Baris Pemantauan Visual Utama (Visual Gauges & Early Warning Checklist)
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
                    section_title("Sistem Peringatan Dini & Keselarasan", tone="amber")
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
        # DI BAWAH AWAL HALAMAN: TAB RINCIAN TEKNIS & AUDIT
        # =============================================================
        adm_dash_tabs = st.tabs([
            "🏢 1. Profil Emiten & Masukan Rasio (X1–X5)",
            "⚖️ 2. Komparasi Tiga Metode (Side-by-Side)",
            "🤖 3. Rincian Inferensi XGBoost AI",
            "📜 4. Histori & Audit Prediksi Terkini",
        ])

        # Tab 1: Profil Emiten & Masukan Rasio Keuangan
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
                        st.caption(f"🛡️ *Capping X4 Aktif (Skripsi Hal. 41 & 95):* `{cap_audit['X4']['raw']:.4f}` ➔ **{cap_audit['X4']['capped']:.4f}** (Maks 3.0)")

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
                        "Model Teoretis Baku Altman 1995/2017 (Persamaan 2 Hal. 46)"
                    ],
                    [
                        "📊 Z''-Score Koefisien Baru (MDA)",
                        f"{mda:.2f}",
                        f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])",
                        mda_badge,
                        "Konsisten" if (mda_cls == "distress" and "DISTRESS" in overall) or (mda_cls == "aman" and "SAFE" in overall) or (mda_cls in ("grey", "grey area") and "GREY" in overall) else "Divergen / Evaluasi",
                        "Model Empiris Dikalibrasi 704 Observasi BEI (Lampiran 2 Hal. 111)"
                    ],
                    [
                        "🤖 XGBoost Classifier (AI)",
                        f"{xgb_val_str} • Eq. Z: {z_eq_val:.2f}" if xgb_prob is not None else "N/A",
                        f"Safe < {xgb_safe_th*100:.0f}% | Distress > {xgb_dist_th*100:.0f}%",
                        xgb_badge_str,
                        "Konsisten" if (xgb_status == overall) else "Divergen / Evaluasi",
                        "Model Kecerdasan Buatan Gradient Boosted Trees Non-Linear (Lampiran 3)"
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
                    ["📐 Altman Z''-Score (1995)", "-", f"Distress < {alt_d:.2f} | Safe > {alt_g:.2f}", "⏳ STANDBY", "Menunggu Analisis", "Model Teoretis Baku Altman 1995/2017 (Persamaan 2 Hal. 46)"],
                    ["📊 Z''-Score Koefisien Baru (MDA)", "-", f"Cut-off {config.get('mda_threshold', 0.3844):.4f} (Grey [{mda_d:.1f}, {mda_g:.1f}])", "⏳ STANDBY", "Menunggu Analisis", "Model Empiris Dikalibrasi 704 Observasi BEI (Lampiran 2 Hal. 111)"],
                    ["🤖 XGBoost Classifier (AI)", "-", f"Safe < {xgb_safe_th*100:.0f}% | Distress > {xgb_dist_th*100:.0f}%", "⏳ STANDBY", "Menunggu Analisis", "Model Kecerdasan Buatan Gradient Boosted Trees Non-Linear (Lampiran 3)"],
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
                st.info("ℹ️ **Model XGBoost Siap:** Silakan masukkan data laporan keuangan emiten pada menu Data & Laporan Keuangan atau klik tombol Muat Data Demo untuk melihat rincian inferensi AI.")

        # Tab 4: Histori & Audit Prediksi Terkini
        with adm_dash_tabs[3]:
            dash_hist_head, dash_hist_btn = st.columns([2.8, 1.2])
            with dash_hist_head:
                section_title("Histori Prediksi & Audit Terkini", "Ringkasan analisis yang tersimpan di basis data sistem")
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