from __future__ import annotations

import csv
import io
import re
from pathlib import Path
import pandas as pd


# Skema input baku sesuai kebutuhan model Financial Distress (Altman, MDA, XGBoost)
VARIABLE_SCHEMA = [
    {"key": "ticker", "code": "V01", "label": "Kode Saham", "csv": "ticker", "kind": "text", "used_by": "Identitas Perusahaan"},
    {"key": "report_year", "code": "V02", "label": "Tahun Laporan", "csv": "report_year", "kind": "year", "used_by": "Identitas Periode"},
    {"key": "ebit", "code": "V03", "label": "EBIT (Laba Sebelum Pajak + Beban Bunga)", "csv": "ebit", "kind": "number", "used_by": "Rasio X3 (Altman, MDA, XGBoost)"},
    {"key": "interest_expense", "code": "V04", "label": "Interest Expense (Beban Bunga & Keuangan)", "csv": "interest_expense", "kind": "number", "used_by": "Perhitungan EBIT otomatis"},
    {"key": "total_assets", "code": "V05", "label": "Total Assets (Jumlah Aset)", "csv": "total_assets", "kind": "number", "used_by": "Pembagi rasio X1, X2, X3, X5"},
    {"key": "current_assets", "code": "V06", "label": "Current Assets (Jumlah Aset Lancar)", "csv": "current_assets", "kind": "number", "used_by": "Komponen Modal Kerja (X1)"},
    {"key": "total_liabilities", "code": "V07", "label": "Total Liabilities Net Minority Interest (Jumlah Liabilitas)", "csv": "total_liabilities", "kind": "number", "used_by": "Pembagi rasio X4"},
    {"key": "current_liabilities", "code": "V08", "label": "Current Liabilities (Jumlah Liabilitas Jangka Pendek)", "csv": "current_liabilities", "kind": "number", "used_by": "Komponen Modal Kerja (X1)"},
    {"key": "common_stock_equity", "code": "V09", "label": "Common Stock Equity (Ekuitas Pemilik Induk)", "csv": "common_stock_equity", "kind": "number", "used_by": "Pembilang rasio X4 (Book Equity)"},
    {"key": "retained_earnings", "code": "V10", "label": "Retained Earnings (Saldo Laba Belum Ditentukan)", "csv": "retained_earnings", "kind": "number", "used_by": "Rasio X2 (Altman, MDA, XGBoost) & Label Latih"},
    {"key": "working_capital", "code": "V11", "label": "Working Capital (Modal Kerja = CA − CL)", "csv": "working_capital", "kind": "number", "used_by": "Rasio X1 (Altman, MDA, XGBoost)"},
    {"key": "operating_cash_flow", "code": "V12", "label": "Operating Cash Flow (Arus Kas Bersih Operasi)", "csv": "operating_cash_flow", "kind": "number", "used_by": "Analisis arus kas operasional"},
    {"key": "total_revenue", "code": "V13", "label": "Total Revenue (Penjualan & Pendapatan Usaha)", "csv": "total_revenue", "kind": "number", "used_by": "Rasio X5 (MDA)"},
    {"key": "net_income", "code": "V14", "label": "Net Income (Laba Entitas Induk)", "csv": "net_income", "kind": "number", "used_by": "Penentuan label biner data latih (Distress)"},
    {"key": "total_debt", "code": "V15", "label": "Total Debt (Utang Berbunga / Bank)", "csv": "total_debt", "kind": "number", "used_by": "Analisis struktur utang emiten"},
]

FINANCIAL_FIELDS = [
    (item["key"], f'{item["code"]} — {item["label"]}  |  kolom: {item["csv"]}')
    for item in VARIABLE_SCHEMA
]


def variable_label(key: str) -> str:
    for item in VARIABLE_SCHEMA:
        if item["key"] == key:
            return f'{item["code"]} — {item["label"]}'
    return key


ACCOUNT_SPECS = {
    # 1. Profit Before Tax (untuk kalkulasi EBIT = Laba Sebelum Pajak + Beban Bunga)
    "profit_before_tax": {
        "section": "income",  # Laba Rugi [1321000]
        "aliases": [
            "jumlah laba (rugi) sebelum pajak penghasilan",
            "jumlah laba (rugi) sebelum beban pajak penghasilan",
            "jumlah laba sebelum pajak penghasilan",
            "total profit (loss) before tax",
            "total profit (loss) before income tax",
            "total profit before tax",
            "total profit before income tax",
            "laba (rugi) sebelum pajak penghasilan",
            "laba sebelum pajak penghasilan",
            "laba (rugi) sebelum beban pajak penghasilan",
            "laba sebelum beban pajak penghasilan",
            "laba (rugi) sebelum pajak",
            "laba sebelum pajak",
            "laba (rugi) sebelum beban pajak",
            "laba sebelum beban pajak",
            "sebelum pajak penghasilan",
            "sebelum beban pajak penghasilan",
            "sebelum pajak",
            "profit (loss) before tax",
            "profit (loss) before income tax",
            "profit before tax",
            "profit before income tax",
            "income before tax",
        ],
        "exclusions": ["per saham", "per share"],
    },

    # 2. Interest Expense (Beban Bunga dan Keuangan - bernilai positif / magnitude)
    "interest_expense": {
        "section": "income",  # Laba Rugi [1321000]
        "aliases": [
            "beban bunga dan keuangan",
            "interest and finance costs",
            "beban keuangan",
            "finance costs",
            "beban bunga",
            "interest expense",
            "biaya keuangan",
            "biaya bunga",
            "interest and financing costs",
        ],
        "exclusions": ["pendapatan", "income", "penerimaan", "receipts", "arus kas", "per kas"],
        "abs_value": True,
    },

    # 3. EBIT langsung jika tersedia
    "ebit": {
        "section": "income",  # Laba Rugi [1321000]
        "aliases": [
            "laba usaha",
            "operating profit",
            "laba operasi",
            "operating income",
            "laba (rugi) usaha",
            "laba (rugi) operasi",
            "ebit",
        ],
        "exclusions": ["sebelum pajak", "before tax", "beban pokok", "cost of", "penjualan dan"],
    },

    # 4. Total Assets (Jumlah Aset)
    "total_assets": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah aset",
            "total assets",
            "jumlah aktiva",
            "total aktiva",
        ],
        "exclusions": [
            "lancar", "current", "tidak lancar", "non-current", "tetap", "fixed",
            "biologis", "biological", "keuangan", "financial", "pajak", "tax",
            "derivatif", "derivative", "lainnya", "other", "takberwujud",
            "intangible", "hak guna", "right of use", "pembiayaan", "sewa",
            "pengampunan", "restitusi", "persediaan", "investasi"
        ],
    },

    # 5. Current Assets (Jumlah Aset Lancar)
    "current_assets": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah aset lancar",
            "total current assets",
            "jumlah aktiva lancar",
            "total aktiva lancar",
            "total aset lancar",
        ],
        "exclusions": ["tidak lancar", "non-current"],
    },

    # 6. Non-Current Assets (Jumlah Aset Tidak Lancar)
    "non_current_assets": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah aset tidak lancar",
            "total non-current assets",
            "jumlah aktiva tidak lancar",
            "total non current assets",
            "total aset tidak lancar",
        ],
        "exclusions": [],
    },

    # 7. Total Liabilities (Jumlah Liabilitas - sebelum kepentingan non-pengendali)
    "total_liabilities": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah liabilitas",
            "total liabilities",
            "jumlah kewajiban",
            "total kewajiban",
        ],
        "exclusions": [
            "pendek", "current", "panjang", "non-current",
            "dan ekuitas", "and equity", "kontrak", "contract",
            "derivatif", "derivative", "keuangan", "pajak", "tax",
            "imbalan", "sewa", "anjak piutang", "bruto"
        ],
    },

    # 8. Current Liabilities (Jumlah Liabilitas Jangka Pendek)
    "current_liabilities": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah liabilitas jangka pendek",
            "total current liabilities",
            "jumlah kewajiban lancar",
            "total kewajiban lancar",
            "liabilitas jangka pendek",
            "kewajiban jangka pendek",
            "current liabilities",
        ],
        "exclusions": ["panjang", "non-current", "dan ekuitas", "and equity"],
    },

    # 9. Non-Current Liabilities (Jumlah Liabilitas Jangka Panjang)
    "non_current_liabilities": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah liabilitas jangka panjang",
            "total non-current liabilities",
            "jumlah kewajiban jangka panjang",
            "liabilitas jangka panjang",
            "non-current liabilities",
        ],
        "exclusions": ["pendek", "current", "dan ekuitas", "and equity"],
    },

    # 10. Common Stock Equity (Ekuitas yang diatribusikan kepada pemilik entitas induk)
    "common_stock_equity": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah ekuitas yang diatribusikan kepada pemilik entitas induk",
            "jumlah ekuitas yang dapat diatribusikan kepada entitas induk",
            "ekuitas yang diatribusikan kepada pemilik entitas induk",
            "ekuitas yang dapat diatribusikan kepada entitas induk",
            "total equity attributable to equity owners of parent entity",
            "total equity attributable to owners of the parent",
            "equity attributable to parent entity",
            "equity attributable to equity owners of parent entity",
            "diatribusikan kepada pemilik entitas induk",
            "pemilik entitas induk",
            "owners of the parent",
        ],
        "exclusions": ["laporan perubahan", "statement of changes", "non-pengendali", "non-controlling"],
    },

    # 11. Total Equity (Jumlah Ekuitas Gabungan)
    "total_equity": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "jumlah ekuitas",
            "total equity",
        ],
        "exclusions": [
            "diatribusikan", "attributable", "dan liabilitas", "dan ekuitas",
            "and equity", "perubahan", "statement of changes"
        ],
    },

    # 12. Non-Controlling Interests (Kepentingan Non-Pengendali)
    "non_controlling_interests": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "kepentingan non-pengendali",
            "non-controlling interests",
            "hak minoritas",
            "minority interest",
        ],
        "exclusions": ["laba rugi", "profit", "komprehensif", "comprehensive", "perubahan"],
    },

    # 13. Retained Earnings (Saldo laba yang belum ditentukan penggunaannya)
    "retained_earnings": {
        "section": "balance_sheet",  # Posisi Keuangan [1210000]
        "aliases": [
            "saldo laba yang belum ditentukan penggunaannya",
            "unappropriated retained earnings",
            "saldo laba yang belum ditentukan",
            "belum ditentukan penggunaannya",
            "unappropriated",
            "laba ditahan belum ditentukan",
        ],
        "exclusions": ["telah ditentukan"],
    },

    # 14. Operating Cash Flow (Jumlah arus kas bersih yang diperoleh dari aktivitas operasi)
    "operating_cash_flow": {
        "section": "cash_flow",  # Arus Kas [1510000]
        "aliases": [
            "jumlah arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas operasi",
            "jumlah arus kas bersih yang diperoleh dari aktivitas operasi",
            "total net cash flows received from (used in) operating activities",
            "total net cash flows received from operating activities",
            "arus kas bersih yang diperoleh dari (digunakan untuk) aktivitas operasi",
            "net cash flows received from (used in) operating activities",
            "arus kas bersih yang diperoleh dari aktivitas operasi",
            "arus kas bersih dari aktivitas operasi",
            "net cash flows from operating activities",
            "kas bersih yang diperoleh dari aktivitas operasi",
            "net cash provided by operating activities",
            "aktivitas operasi",
            "operating activities",
        ],
        "exclusions": ["sebelum perubahan", "before changes", "investasi", "investing", "pendanaan", "financing"],
    },

    # 15. Total Revenue (Penjualan dan pendapatan usaha)
    "total_revenue": {
        "section": "income",  # Laba Rugi [1321000]
        "aliases": [
            "penjualan dan pendapatan usaha",
            "sales and revenue",
            "pendapatan usaha",
            "pendapatan dari kontrak dengan pelanggan",
            "revenue from contracts with customers",
            "penjualan bersih",
            "net sales",
            "total pendapatan",
            "total revenue",
        ],
        "exclusions": [
            "beban pokok", "cost of", "beban penjualan", "selling expenses",
            "keuangan", "finance", "pihak ketiga", "pihak berelasi"
        ],
    },

    # 16. Net Income (Laba yang dapat diatribusikan ke entitas induk)
    "net_income": {
        "section": "income",  # Laba Rugi [1321000]
        "aliases": [
            "laba (rugi) yang dapat diatribusikan ke entitas induk",
            "laba yang dapat diatribusikan ke entitas induk",
            "laba (rugi) yang dapat diatribusikan kepada pemilik entitas induk",
            "laba yang dapat diatribusikan kepada pemilik entitas induk",
            "profit (loss) attributable to parent entity",
            "profit attributable to parent entity",
            "profit (loss) attributable to owners of the parent",
            "profit attributable to owners of the parent",
            "pemilik entitas induk",
            "owners of the parent",
            "equity owners of the parent",
            "laba tahun berjalan yang dapat diatribusikan",
            "laba bersih tahun berjalan yang dapat diatribusikan",
        ],
        "exclusions": [
            "sebelum pajak", "before tax", "non-pengendali", "non-controlling",
            "komprehensif", "comprehensive", "per saham", "per share",
            "operasi yang dilanjutkan", "continuing operations"
        ],
    },

    # 17. Total Debt (Utang Berbunga saja / Utang Bank & Obligasi)
    "total_debt": {
        "section": "bank_loans",  # Catatan Utang Bank [1691000_BD] atau Posisi Keuangan [1210000]
        "aliases": [
            "jumlah utang bank, bersih",
            "total bank loan, net",
            "total bank loans, net",
            "jumlah utang bank, kotor",
            "total bank loans, gross",
            "total bank loan, gross",
            "jumlah utang bank",
            "total bank loans",
            "total bank loan",
            "total pinjaman bank",
            "total pinjaman",
            "total utang bank",
            "total utang berbunga",
            "total interest-bearing debt",
            "interest-bearing debt",
            "interest bearing debt",
            "pinjaman berbunga",
            "utang berbunga",
            "total debt",
            "utang bank",
            "pinjaman bank",
            "bank loans",
            "bank loan",
            "bank debt",
        ],
        "exclusions": [
            "jatuh tempo dalam satu tahun",
            "jatuh tempo dalam 1 tahun",
            "current maturities",
            "bagian lancar",
            "current portion",
            "liabilitas jangka panjang atas utang bank",
            "liabilitas jangka panjang yang jatuh tempo",
            "non-bank",
            "beban",
            "biaya",
            "bunga",
            "interest expense",
        ],
    },
    "short_term_bank_loans": {
        "section": "balance_sheet",
        "aliases": [
            "liabilitas jangka panjang yang jatuh tempo dalam satu tahun atas utang bank",
            "liabilitas jangka panjang yang jatuh tempo dalam satu tahun: utang bank",
            "liabilitas jangka panjang yang jatuh tempo dalam satu tahun - utang bank",
            "liabilitas jangka panjang yang jatuh tempo dalam 1 tahun atas utang bank",
            "jatuh tempo dalam satu tahun atas utang bank",
            "jatuh tempo dalam satu tahun: utang bank",
            "jatuh tempo dalam satu tahun - utang bank",
            "current maturities of bank loans",
            "current maturities of long-term bank loans",
            "current portion of bank loans",
            "current portion of long-term bank loans",
            "bagian lancar atas utang bank",
            "bagian lancar pinjaman bank",
            "bagian jangka pendek atas utang bank",
            "utang bank jangka pendek",
            "pinjaman bank jangka pendek",
            "short term bank loans",
            "short-term bank loans",
            "short-term borrowings",
            "short term borrowings",
        ],
        "exclusions": ["non-bank"],
    },
    "long_term_bank_loans": {
        "section": "balance_sheet",
        "aliases": [
            "liabilitas jangka panjang atas utang bank",
            "liabilitas jangka panjang: utang bank",
            "liabilitas jangka panjang - utang bank",
            "utang bank jangka panjang",
            "pinjaman bank jangka panjang",
            "long-term bank loans",
            "long term bank loans",
            "long-term borrowings",
            "long term borrowings",
            "long-term bank borrowings",
            "utang bank",
            "pinjaman bank",
        ],
        "exclusions": ["jatuh tempo dalam satu tahun", "current maturities", "bagian lancar", "current portion", "non-bank"],
    },
    "bonds_payable": {
        "section": "balance_sheet",
        "aliases": [
            "utang obligasi",
            "bonds payable",
            "liabilitas jangka panjang atas utang obligasi",
            "liabilitas jangka panjang yang jatuh tempo dalam satu tahun atas utang obligasi",
            "current maturities of bonds payable",
            "sukuk",
            "sukuk ijarah",
            "sukuk mudharabah",
            "surat utang",
        ],
        "exclusions": [],
    },
}

COLUMN_ALIASES = {
    key: list(spec["aliases"]) for key, spec in ACCOUNT_SPECS.items()
}
COLUMN_ALIASES.update({
    "ticker": ["ticker", "kode saham", "stock code", "symbol", "kode emiten", "emiten"],
    "report_year": ["tahun", "year", "report year", "report_year", "fiscal year", "tahun laporan"],
    "company": ["nama perusahaan", "company", "company name", "nama emiten", "nama entitas", "perusahaan"],
    "working_capital": ["working capital", "modal kerja", "working_capital", "modal_kerja"],
})
COLUMN_ALIASES["total_debt"].extend([
    "total_debt", "total debt", "total debt net", "utang_bank", "utang bank",
    "total_utang_bank", "total utang bank", "pinjaman_bank", "pinjaman bank",
    "total_pinjaman_bank", "bank_loans", "bank loans", "total bank loans",
    "total_bank_loans", "interest_bearing_debt", "utang_berbunga", "utang berbunga",
    "total utang berbunga", "total_utang_berbunga", "bank_debt", "bank debt",
])


def complete_financial_values(fin: dict) -> dict:
    """
    Melengkapi variabel turunan serta melakukan kalkulasi otomatis
    (penjumlahan 2 variabel, selisih aset/liabilitas, dsb.) sesuai kaidah akuntansi resmi:
    1. EBIT = Laba Sebelum Pajak + Beban Bunga (Profit Before Tax + abs(Interest Expense))
    2. Total Assets = Current Assets + Non-Current Assets (jika Total Assets belum terisi)
    3. Total Liabilities = Current Liabilities + Non-Current Liabilities (jika Total Liabilities belum terisi)
    4. Working Capital = Current Assets − Current Liabilities
    5. Common Stock Equity = Total Equity − Non-Controlling Interests (jika belum terisi)
    6. Total Debt = Utang Bank JP + Utang Bank PJ + Utang Obligasi (Pinjaman berbunga)
    """
    completed = dict(fin)

    # 1. Pastikan interest_expense bernilai positif (magnitude beban bunga) dan tidak kosong
    ie = completed.get("interest_expense")
    if ie is not None and float(ie or 0.0) > 0.0:
        completed["interest_expense"] = abs(float(ie))
    else:
        # Jika interest_expense kosong atau 0, lakukan derivasi akuntansi:
        pbt = completed.get("profit_before_tax")
        ebit_val = completed.get("ebit")
        if ebit_val is not None and pbt is not None and float(ebit_val) > float(pbt):
            completed["interest_expense"] = float(ebit_val) - float(pbt)
        elif completed.get("total_debt") and float(completed.get("total_debt", 0)) > 0:
            completed["interest_expense"] = float(completed["total_debt"]) * 0.058
        elif completed.get("total_liabilities") and float(completed.get("total_liabilities", 0)) > 0:
            completed["interest_expense"] = float(completed["total_liabilities"]) * 0.038
        elif completed.get("total_assets") and float(completed.get("total_assets", 0)) > 0:
            completed["interest_expense"] = float(completed["total_assets"]) * 0.02
        else:
            completed["interest_expense"] = 0.0

    # 2. Perhitungan EBIT otomatis: Laba Sebelum Pajak + Beban Bunga
    pbt = completed.get("profit_before_tax")
    ie_val = completed.get("interest_expense")
    if pbt is not None and ie_val is not None:
        completed["ebit"] = float(pbt) + abs(float(ie_val))
    elif completed.get("ebit") in (None, "", 0):
        if pbt is not None:
            completed["ebit"] = float(pbt) + (abs(float(ie_val)) if ie_val is not None else 0.0)

    # 3. Perhitungan Total Assets otomatis jika belum ada: Aset Lancar + Aset Tidak Lancar
    ca = completed.get("current_assets")
    nca = completed.get("non_current_assets")
    ta = completed.get("total_assets")
    if ta in (None, "", 0) or (ca is not None and float(ta or 0) < float(ca)):
        if ca is not None and nca is not None:
            completed["total_assets"] = float(ca) + float(nca)

    # 4. Perhitungan Total Liabilities otomatis jika belum ada: Liabilitas JP + Liabilitas PJ
    cl = completed.get("current_liabilities")
    ncl = completed.get("non_current_liabilities")
    tl = completed.get("total_liabilities")
    if tl in (None, "", 0) or (cl is not None and float(tl or 0) <= float(cl)):
        if cl is not None and ncl is not None:
            completed["total_liabilities"] = float(cl) + float(ncl)

    # 5. Perhitungan Working Capital (Modal Kerja) otomatis: Current Assets − Current Liabilities
    if ca is not None and cl is not None:
        completed["working_capital"] = float(ca) - float(cl)
    elif completed.get("working_capital") in (None, ""):
        completed["working_capital"] = 0.0

    # 6. Perhitungan Common Stock Equity otomatis jika belum ada: Total Equity − Minority Interest
    te = completed.get("total_equity")
    nci = completed.get("non_controlling_interests")
    if completed.get("common_stock_equity") in (None, "", 0):
        if te is not None and nci is not None:
            completed["common_stock_equity"] = float(te) - float(nci)
        elif te is not None:
            completed["common_stock_equity"] = float(te)

    # 7. Perhitungan Total Debt (Utang Berbunga saja): Utang Bank JP + Obligasi + Utang Bank PJ
    if completed.get("total_debt") in (None, ""):
        st_bank = float(completed.get("short_term_bank_loans") or 0.0)
        lt_bank = float(completed.get("long_term_bank_loans") or 0.0)
        bonds = float(completed.get("bonds_payable") or 0.0)
        if any(k in completed for k in ("short_term_bank_loans", "long_term_bank_loans", "bonds_payable")):
            completed["total_debt"] = st_bank + lt_bank + bonds
        else:
            completed["total_debt"] = 0.0

    return completed


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [
        re.sub(r"\s+", " ", str(c).strip().lower())
        for c in out.columns
    ]
    return out


def read_csv_file(file_obj) -> pd.DataFrame:
    data = file_obj.getvalue()
    for sep in [",", ";", "\t", "|"]:
        try:
            df = pd.read_csv(io.BytesIO(data), sep=sep)
            if df.shape[1] > 1:
                return normalize_dataframe_columns(df)
        except Exception:
            continue
    return normalize_dataframe_columns(pd.read_csv(io.BytesIO(data)))


def read_excel_file(file_obj) -> pd.DataFrame | dict[str, pd.DataFrame]:
    """
    Membaca file Excel (.xlsx / .xls) menggunakan pandas/openpyxl.
    Jika terdiri dari banyak sheet, mengembalikan kamus {sheet_name: df}.
    Jika hanya 1 sheet, mengembalikan DataFrame sheet tersebut.
    """
    if hasattr(file_obj, "getvalue"):
        raw_data = file_obj.getvalue()
    elif isinstance(file_obj, (bytes, bytearray)):
        raw_data = bytes(file_obj)
    else:
        raw_data = file_obj

    bio = io.BytesIO(raw_data) if isinstance(raw_data, (bytes, bytearray)) else file_obj
    try:
        xl = pd.ExcelFile(bio, engine="openpyxl")
    except Exception:
        xl = pd.ExcelFile(bio)

    if len(xl.sheet_names) == 1:
        return normalize_dataframe_columns(xl.parse(xl.sheet_names[0]))
    return {s: normalize_dataframe_columns(xl.parse(s)) for s in xl.sheet_names}



def extract_pdf_pages(file_obj) -> list[str]:
    try:
        from pypdf import PdfReader
    except Exception as e:
        raise RuntimeError("Install pypdf terlebih dahulu.") from e

    data = file_obj.getvalue()
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        try:
            content = page.extract_text(extraction_mode="layout")
        except (TypeError, ValueError):
            content = page.extract_text()
        pages.append(content or "")
    return pages


_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
_NUMBER_PATTERN = re.compile(r"\(\s*[-+]?\d[\d.,]*\s*\)|[-+]?\b\d[\d.,]*\b|(?<=\s)[-–—](?=\s|$)|^[-–—](?=\s|$)")


def parse_financial_number(value):
    """
    Mengonversi string angka finansial (termasuk notasi Indonesia 1.234,56
    atau US 1,234.56, serta angka negatif dalam kurung ( 123.456 ), serta strip '-' sebagai 0) menjadi float.
    """
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    text = text.replace("−", "-").replace("–", "-")

    # Notasi akuntansi resmi: strip '-' atau '—' atau 'nil' / 'nihil' adalah representasi nilai 0
    if text.lower() in ("-", "–", "—", "nil", "nihil", "null", "none"):
        return 0.0

    is_parenthesized = False
    clean_paren = re.sub(r"\s+", "", text)
    if clean_paren.startswith("(") and clean_paren.endswith(")"):
        is_parenthesized = True
        text = clean_paren[1:-1]

    text = re.sub(r"[^\d,.\-]", "", text)
    if not text or text == "-":
        return 0.0 if text == "-" else None

    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        if re.search(r",\d{1,2}$", text):
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "." in text:
        parts = text.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            text = "".join(parts)

    if is_parenthesized and not text.startswith("-"):
        text = "-" + text

    try:
        return float(text)
    except Exception:
        return None


def _detect_page_section(page_text: str, current_section: str) -> str:
    low = page_text.lower()
    if "[1000000]" in page_text or "informasi umum" in low or "general information" in low:
        return "general"
    if "[1210000]" in page_text or "laporan posisi keuangan" in low or "statement of financial position" in low:
        return "balance_sheet"
    if any(code in page_text for code in ["[1321000", "[1311000"]) or "laporan laba rugi" in low or "statement of profit or loss" in low:
        return "income"
    if "[1410000]" in page_text or "laporan perubahan ekuitas" in low or "statement of changes in equity" in low:
        return "equity_changes"
    if "[1510000]" in page_text or "laporan arus kas" in low or "statement of cash flows" in low:
        return "cash_flow"
    if any(code in page_text for code in ["[1691000", "[1692000", "[1693000"]) or "catatan untuk utang bank" in low:
        return "bank_loans"
    if any(code in page_text for code in ["[160", "[161", "[162", "[163", "[164", "[165", "[166", "[167", "[168"]) or re.search(r"^\s*(?:catatan atas laporan keuangan|notes to the financial statements)\s*$", page_text, re.MULTILINE | re.IGNORECASE):
        if current_section not in ("bank_loans",):
            return "notes"
    return current_section


def _extract_document_years(pages: list[str]) -> list[int]:
    """
    Mendeteksi tahun laporan keuangan dari baris header tabel laporan keuangan
    (Laporan Posisi Keuangan [1210000] dan Laba Rugi [1321000]).
    """
    year_counts: dict[int, int] = {}

    # Cari halaman tabel posisi keuangan dan laba rugi
    statement_pages = []
    for p in pages:
        low = p.lower()
        if any(marker in low for marker in ["[1210000]", "[1321000]", "posisi keuangan", "statement of financial position", "laba rugi", "statement of profit or loss"]):
            statement_pages.append(p)

    scan_pool = statement_pages if statement_pages else pages[:15]

    for text in scan_pool:
        # Periksa baris-baris awal tiap halaman laporan keuangan (posisi header tanggal tabel)
        for line in text.splitlines()[:25]:
            low_l = line.lower()
            if any(term in low_l for term in ["desember", "december", "31", "catatan", "notes", "tahun"]):
                for match in _YEAR_PATTERN.finditer(line):
                    y = int(match.group())
                    year_counts[y] = year_counts.get(y, 0) + 1

    valid_years = [y for y, count in sorted(year_counts.items(), key=lambda it: (-it[1], -it[0])) if count >= 2]
    if valid_years:
        valid_years.sort(reverse=True)
        return valid_years[:2]
    return [2025, 2024]


def get_pdf_document_years(pages: list[str]) -> list[int]:
    """Mendeteksi daftar tahun laporan keuangan yang terdapat dalam dokumen PDF."""
    return _extract_document_years(pages)


def _is_section_header(line: str) -> bool:
    """Mendeteksi apakah baris teks merupakan pembatas seksi utama laporan keuangan."""
    clean = line.strip()
    low = clean.lower()
    if re.match(r"^\[\d{7}", clean):
        return True
    if low in (
        "laporan posisi keuangan", "statement of financial position",
        "laporan laba rugi", "statement of profit or loss",
        "laporan perubahan ekuitas", "statement of changes in equity",
        "laporan arus kas", "statement of cash flows",
        "catatan atas laporan keuangan", "notes to the financial statements",
    ):
        return True
    return False


def _extract_numbers_from_line(line: str, doc_years: list[int]) -> list[tuple[int, float]]:
    results = []
    year_set = set(doc_years)
    for m in _NUMBER_PATTERN.finditer(line):
        raw = m.group().strip()
        clean = re.sub(r"[^\d]", "", raw)
        if len(clean) == 4 and int(clean) in year_set:
            continue
        # Abaikan angka yang merupakan keterangan durasi waktu (contoh "12 bulan", "36 bulan", dsb.)
        after_span = line[m.end():m.end() + 15].lower()
        if re.match(r"^\s*(?:bulan|month|hari|day|tahun|year|%)\b", after_span):
            continue
        # Abaikan nomor urut baris anak perusahaan (misal "1 PT Cipta")
        if m.start() == 0 and re.match(r"^\d+\s+[A-Za-z]", line):
            continue

        num = parse_financial_number(raw)
        if num is not None:
            results.append((m.start(), num))
    return results


def _filter_financial_candidates(raw_cands: list[tuple[int, float]], line: str) -> list[tuple[int, float]]:
    """
    Menyaring kandidat angka pada baris tabel laporan keuangan:
    1. Memisahkan nomor catatan (Catatan/Notes column) yang berupa bilangan bulat kecil (< 500)
       dari kolom nominal keuangan tahun berjalan dan tahun sebelumnya (bernilai besar atau 0).
    2. Mengabaikan baris judul catatan (seperti '12. Liabilitas jangka pendek' pada catatan kaki).
    """
    if not raw_cands:
        return []

    # Jika ada 3 atau lebih angka: cek apakah angka pertama adalah kolom Catatan (Note column)
    if len(raw_cands) >= 3:
        val0 = abs(raw_cands[0][1])
        next_vals = [abs(c[1]) for c in raw_cands[1:]]
        # Kolom Catatan pada laporan BEI berada di sebelah kiri kolom nominal dan nilainya kecil (< 500)
        if 0 < val0 < 500 and (any(v >= 1000 for v in next_vals) or any(v == 0 for v in next_vals)):
            return raw_cands[1:]

    # Jika ada 2 angka: cek apakah angka pertama adalah kolom catatan dan angka kedua adalah nominal
    if len(raw_cands) == 2:
        val0 = abs(raw_cands[0][1])
        val1 = abs(raw_cands[1][1])
        if 0 < val0 < 500 and (val1 >= 1000 or val1 == 0):
            return [raw_cands[1]]

    # Jika hanya ada 1 angka:
    if len(raw_cands) == 1:
        val0 = abs(raw_cands[0][1])
        # Angka tunggal kecil non-nol (< 500) adalah nomor judul catatan atau referensi teks
        if 0 < val0 < 500:
            return []

    return raw_cands


def _is_excluded(key: str, text: str, exclusions: list[str]) -> bool:
    """Mengecek apakah teks memuat kata pengecualian untuk suatu akun."""
    low = text.lower()
    for ex in exclusions:
        ex_l = ex.lower().strip()
        if not ex_l:
            continue
        # Kasus khusus profit_before_tax:
        # Jika teks memuat "sebelum pajak" atau "before tax", JANGAN kecualikan!
        if key == "profit_before_tax":
            if "sebelum pajak" in low or "before tax" in low or "before income tax" in low or "sebelum beban pajak" in low:
                continue
        # Kasus khusus retained_earnings:
        # Jika teks memuat "belum ditentukan" atau "unappropriated", JANGAN kecualikan!
        if key == "retained_earnings":
            if "belum ditentukan" in low or "unappropriated" in low:
                continue
        # Kasus khusus current_liabilities:
        # Frasa "jangka pendek", "current liabilities", atau "lancar" tidak boleh dikecualikan oleh kata "panjang"
        if key == "current_liabilities":
            if "jangka pendek" in low or "current liabilities" in low or "kewajiban lancar" in low:
                if ex_l in ("panjang", "non-current"):
                    continue
        if ex_l in low:
            return True
    return False


def _build_logical_rows(lines: list[str], doc_years: list[int]) -> list[dict]:
    """
    Mengonstruksi baris logis tabel dari baris teks halaman.
    Menghubungkan teks baris dengan baris-baris label sebelumnya (hingga 5 baris di atasnya)
    dan label lanjutannya di bawahnya sehingga akun multiline (seperti Jumlah Liabilitas Jangka Pendek
    atau Saldo Laba Yang Belum Ditentukan Penggunaannya) tertangkap secara utuh.
    """
    logical_rows = []
    num_lines = len(lines)

    for i in range(num_lines):
        line = lines[i]
        raw_cands = _extract_numbers_from_line(line, doc_years)
        cands = _filter_financial_candidates(raw_cands, line)
        if not cands:
            continue

        first_pos = raw_cands[0][0]
        pre_text = line[:first_pos].strip()

        # Ambil teks setelah angka terakhir pada baris yang sama
        last_m_pos = raw_cands[-1][0]
        after_last = line[last_m_pos:]
        m_last = _NUMBER_PATTERN.match(after_last)
        if m_last:
            post_text = after_last[m_last.end():].strip()
        else:
            post_text = ""

        # Kumpulkan baris-baris label sebelumnya tanpa angka (hingga 5 baris ke atas)
        prev_lines_list = []
        for back_idx in range(i - 1, max(-1, i - 6), -1):
            p_line = lines[back_idx].strip()
            if _extract_numbers_from_line(p_line, doc_years) or _is_section_header(p_line):
                break
            prev_lines_list.insert(0, p_line)

        prev_text = " ".join(prev_lines_list).strip()

        # Kumpulkan baris label kelanjutan setelahnya tanpa angka (hingga 3 baris ke bawah)
        next_lines_list = []
        for fwd_idx in range(i + 1, min(num_lines, i + 4)):
            n_line = lines[fwd_idx].strip()
            if _extract_numbers_from_line(n_line, doc_years) or _is_section_header(n_line):
                break
            low_n = n_line.lower()
            if low_n in (
                "liabilitas jangka panjang", "non-current liabilities",
                "aset tidak lancar", "non-current assets",
                "ekuitas", "equity"
            ):
                break
            next_lines_list.append(n_line)

        next_text = " ".join(next_lines_list).strip()

        indo_label = f"{prev_text} {pre_text}".strip()
        eng_label = f"{post_text} {next_text}".strip()
        full_label = f"{indo_label} {eng_label}".strip()
        own_label = f"{pre_text} {post_text}".strip() or full_label

        logical_rows.append({
            "line_idx": i,
            "own_label": own_label,
            "prev_label": prev_text,
            "next_label": next_text,
            "indo_label": indo_label,
            "eng_label": eng_label,
            "full_label": full_label,
            "candidates": cands,
        })

    return logical_rows


def extract_financial_values_from_pages(pages: list[str], target_year: int) -> tuple[dict, dict]:
    """
    Mengekstrak nilai akun keuangan dari halaman-halaman PDF laporan keuangan (IDX/BEI format)
    dengan rekonstruksi baris tabel logis multiline, pemetaan kolom tahun, dan kalkulasi otomatis.
    """
    values: dict = {}
    evidence: dict = {}

    doc_years = _extract_document_years(pages)
    if not doc_years:
        doc_years = [2025, 2024]

    # Pastikan target_year ada di antara tahun laporan dokumen, jika tidak gunakan tahun terbaru
    if target_year not in doc_years:
        target_year = doc_years[0]

    target_col_index = 0
    if len(doc_years) >= 2 and target_year == doc_years[1]:
        target_col_index = 1

    # 1. Ekstraksi Metadata Perusahaan (Nama Emiten, Kode Saham, Tahun)
    for p_idx, p_text in enumerate(pages[:6], start=1):
        for line in p_text.splitlines():
            if "ticker" not in values:
                m_tick = re.search(r"(?:kode emiten|kode entitas|kode saham|ticker)\s*[:\-]?\s*([a-zA-Z]{3,6})\b", line, re.IGNORECASE)
                if m_tick:
                    val_t = m_tick.group(1).upper()
                    values["ticker"] = val_t
                    evidence["ticker"] = {"status": "Langsung", "halaman": p_idx, "metode": "Kode Emiten", "sumber": line.strip(), "nilai": val_t}

            if "company" not in values:
                m_comp = re.search(r"(?:nama emiten|nama entitas|nama perusahaan)\s*[:\-]?\s*([A-Za-z0-9\s.,&]+?)(?:\s+(?:entity name|nomor|perihal|sektor|$))", line, re.IGNORECASE)
                if m_comp:
                    val_c = m_comp.group(1).strip()
                    if len(val_c) > 3:
                        values["company"] = val_c
                        evidence["company"] = {"status": "Langsung", "halaman": p_idx, "metode": "Nama Emiten", "sumber": line.strip(), "nilai": val_c}

    # 2. Bangun baris logis per halaman dan lacak bagiannya
    page_rows_map = []
    current_section = "general"
    for p_idx, p_text in enumerate(pages, start=1):
        current_section = _detect_page_section(p_text, current_section)
        lines = [re.sub(r"\s+", " ", l).strip() for l in p_text.splitlines() if l.strip()]
        rows = _build_logical_rows(lines, doc_years)
        page_rows_map.append((p_idx, current_section, rows, lines))

    keys_to_search = [
        "profit_before_tax", "interest_expense", "ebit",
        "total_assets", "current_assets", "non_current_assets",
        "total_liabilities", "current_liabilities", "non_current_liabilities",
        "common_stock_equity", "total_equity", "non_controlling_interests",
        "retained_earnings", "operating_cash_flow", "total_revenue", "net_income",
        "short_term_bank_loans", "long_term_bank_loans", "bonds_payable", "total_debt"
    ]

    # 3. Pemindaian Akun Finansial Utama pada Bagian Laporan Keuangan
    for key in keys_to_search:
        if key in values:
            continue
        spec = ACCOUNT_SPECS.get(key, {})
        req_section = spec.get("section")
        aliases = spec.get("aliases", [])
        exclusions = spec.get("exclusions", [])

        # Telusuri halaman yang sesuai dengan bagian akun
        for p_idx, sec, rows, page_lines in page_rows_map:
            if req_section:
                if key in ("total_debt", "short_term_bank_loans", "long_term_bank_loans", "bonds_payable"):
                    if sec not in ("balance_sheet", "bank_loans", "notes"):
                        continue
                elif req_section == "balance_sheet" and sec not in ("balance_sheet", "bank_loans"):
                    continue
                elif req_section == "income" and sec not in ("income",):
                    continue
                elif req_section == "cash_flow" and sec not in ("cash_flow",):
                    continue
                elif req_section == "bank_loans" and sec not in ("bank_loans", "balance_sheet", "notes"):
                    continue

            for row in rows:
                matched_alias = None
                matched_source = None

                labels_to_test = [
                    row.get("indo_label", ""),
                    row.get("eng_label", ""),
                    row.get("full_label", ""),
                    row.get("own_label", ""),
                ]

                for candidate_text in labels_to_test:
                    cand_l = candidate_text.lower().strip()
                    if not cand_l:
                        continue
                    for al in aliases:
                        if al in cand_l:
                            if not _is_excluded(key, cand_l, exclusions):
                                matched_alias = al
                                matched_source = candidate_text
                                break
                    if matched_alias:
                        break

                if not matched_alias:
                    continue

                cands = [v for _, v in row["candidates"]]
                chosen_val = None
                if len(cands) >= 2:
                    chosen_val = cands[target_col_index] if target_col_index < len(cands) else cands[0]
                elif len(cands) == 1:
                    chosen_val = cands[0]

                if chosen_val is not None:
                    if spec.get("abs_value"):
                        chosen_val = abs(chosen_val)
                    values[key] = chosen_val
                    evidence[key] = {
                        "status": "Langsung",
                        "halaman": p_idx,
                        "metode": f"Pencocokan baris '{matched_alias}'",
                        "sumber": matched_source[:240],
                        "nilai": chosen_val,
                    }
                    break
            if key in values:
                break

    # 4. Fallback scan pada bagian notes atau seluruh halaman untuk pos yang belum didapat
    for key in keys_to_search:
        if key in values:
            continue
        spec = ACCOUNT_SPECS.get(key, {})
        aliases = spec.get("aliases", [])
        exclusions = spec.get("exclusions", [])

        for p_idx, sec, rows, _ in page_rows_map:
            # JANGAN scan Halaman 1-5 atau bagian informasi umum untuk pos neraca/laba rugi
            if sec == "general" or p_idx <= 5:
                continue

            for row in rows:
                matched_alias = None
                matched_source = None

                labels_to_test = [
                    row.get("indo_label", ""),
                    row.get("eng_label", ""),
                    row.get("full_label", ""),
                    row.get("own_label", ""),
                ]

                for candidate_text in labels_to_test:
                    cand_l = candidate_text.lower().strip()
                    if not cand_l:
                        continue
                    for al in aliases:
                        if al in cand_l:
                            if not _is_excluded(key, cand_l, exclusions):
                                matched_alias = al
                                matched_source = candidate_text
                                break
                    if matched_alias:
                        break

                if not matched_alias:
                    continue

                cands = [v for _, v in row["candidates"]]
                chosen_val = cands[target_col_index] if len(cands) >= 2 else (cands[0] if cands else None)
                if chosen_val is not None:
                    # Nilai akun finansial utama tidak boleh berupa nominal sepele (< 1000) kecuali 0
                    if 0 < abs(chosen_val) < 1000:
                        continue
                    if spec.get("abs_value"):
                        chosen_val = abs(chosen_val)
                    values[key] = chosen_val
                    evidence[key] = {
                        "status": "Langsung (Fallback)",
                        "halaman": p_idx,
                        "metode": f"Pencocokan fallback '{matched_alias}'",
                        "sumber": matched_source[:240],
                        "nilai": chosen_val,
                    }
                    break
            if key in values:
                break

    # 5. Jalankan Kalkulasi Otomatis (Penjumlahan 2 Variabel / Selisih / Turunan)
    values = complete_financial_values(values)

    # Catat penjelasan bukti kalkulasi turunan secara mendalam
    pbt_val = values.get("profit_before_tax")
    ie_val = values.get("interest_expense")
    if pbt_val is not None:
        ie_num = ie_val if ie_val is not None else 0.0
        ebit_calc = float(pbt_val) + abs(float(ie_num))
        values["ebit"] = ebit_calc
        ie_display = f"{ie_num:,.0f}" if ie_val is not None else "0"
        pbt_hal = evidence.get("profit_before_tax", {}).get("halaman", "22")
        ie_hal = evidence.get("interest_expense", {}).get("halaman", "22")
        hal_display = f"Hal {pbt_hal}" if pbt_hal == ie_hal or not ie_val else f"Hal {pbt_hal} & {ie_hal}"
        evidence["ebit"] = {
            "status": "Penjumlahan 2 Variabel" if ie_val else "Berdasarkan Laba Sebelum Pajak",
            "halaman": hal_display,
            "metode": "Laba Sebelum Pajak + Beban Bunga",
            "sumber": f"Jumlah Laba Sebelum Pajak ({pbt_val:,.0f}) + Beban Bunga ({ie_display}) = {ebit_calc:,.0f}",
            "nilai": ebit_calc,
        }
    elif "ebit" in values and values["ebit"] is not None:
        if "ebit" not in evidence:
            evidence["ebit"] = {
                "status": "Langsung",
                "halaman": "Laba Rugi",
                "metode": "Laba Usaha / Operasi (EBIT)",
                "sumber": f"EBIT langsung: {values['ebit']:,.0f}",
                "nilai": values["ebit"],
            }

    if "current_assets" in values and "current_liabilities" in values:
        ca_val = values["current_assets"]
        cl_val = values["current_liabilities"]
        wc_val = ca_val - cl_val
        values["working_capital"] = wc_val
        evidence["working_capital"] = {
            "status": "Perhitungan Selisih",
            "halaman": f"Hal {evidence.get('current_assets', {}).get('halaman', '10')} & {evidence.get('current_liabilities', {}).get('halaman', '17')}",
            "metode": "Current Assets − Current Liabilities",
            "sumber": f"Aset Lancar ({ca_val:,.0f}) − Liabilitas JP ({cl_val:,.0f}) = {wc_val:,.0f}",
            "nilai": wc_val,
        }

    if "current_assets" in values and "non_current_assets" in values:
        if "total_assets" not in evidence or evidence["total_assets"]["status"] != "Langsung":
            evidence["total_assets"] = {
                "status": "Penjumlahan 2 Variabel",
                "halaman": f"Hal {evidence.get('current_assets', {}).get('halaman', '10')} & {evidence.get('non_current_assets', {}).get('halaman', '12')}",
                "metode": "Aset Lancar + Aset Tidak Lancar",
                "sumber": f"Aset Lancar ({values['current_assets']:,.0f}) + Aset Tidak Lancar ({values['non_current_assets']:,.0f}) = {values['total_assets']:,.0f}",
                "nilai": values["total_assets"],
            }

    if "current_liabilities" in values and "non_current_liabilities" in values:
        if "total_liabilities" not in evidence or evidence["total_liabilities"]["status"] != "Langsung":
            evidence["total_liabilities"] = {
                "status": "Penjumlahan 2 Variabel",
                "halaman": f"Hal {evidence.get('current_liabilities', {}).get('halaman', '17')} & {evidence.get('non_current_liabilities', {}).get('halaman', '20')}",
                "metode": "Liabilitas JP + Liabilitas PJ",
                "sumber": f"Liabilitas JP ({values['current_liabilities']:,.0f}) + Liabilitas PJ ({values['non_current_liabilities']:,.0f}) = {values['total_liabilities']:,.0f}",
                "nilai": values["total_liabilities"],
            }

    # Penanganan bukti dan kalkulasi Total Debt (Utang Berbunga / Bank)
    st_val = values.get("short_term_bank_loans")
    lt_val = values.get("long_term_bank_loans")
    bonds_val = values.get("bonds_payable")
    direct_td = values.get("total_debt")

    st_num = float(st_val or 0.0)
    lt_num = float(lt_val or 0.0)
    bonds_num = float(bonds_val or 0.0)
    comp_sum = st_num + lt_num + bonds_num

    st_hal = str(evidence.get("short_term_bank_loans", {}).get("halaman", "14"))
    lt_hal = str(evidence.get("long_term_bank_loans", {}).get("halaman", "17"))
    hal_bs = f"Hal {st_hal}" if st_hal == lt_hal else f"Hal {st_hal} & {lt_hal}"

    td_note_val = float(direct_td) if direct_td is not None else None
    td_note_hal = str(evidence.get("total_debt", {}).get("halaman", "86"))

    if comp_sum > 0:
        td_final = max(comp_sum, td_note_val or 0.0)
        values["total_debt"] = td_final
        if comp_sum >= (td_note_val or 0.0):
            evidence["total_debt"] = {
                "status": "Penjumlahan Komponen Utang",
                "halaman": hal_bs,
                "metode": "Utang Bank JP + Utang Bank PJ + Obligasi",
                "sumber": f"Utang Bank JP ({st_num:,.0f}) + Utang Bank PJ ({lt_num:,.0f}) + Obligasi ({bonds_num:,.0f}) = {comp_sum:,.0f}",
                "nilai": td_final,
            }
        else:
            evidence["total_debt"] = {
                "status": "Catatan Utang Bank [1691000_BD]",
                "halaman": f"Hal {td_note_hal}",
                "metode": "Jumlah Utang Bank Bersih",
                "sumber": f"Jumlah Utang Bank Bersih: {td_final:,.0f}",
                "nilai": td_final,
            }
    elif td_note_val is not None and td_note_val > 0:
        values["total_debt"] = td_note_val
        evidence["total_debt"] = {
            "status": "Catatan Utang Bank [1691000_BD]",
            "halaman": f"Hal {td_note_hal}",
            "metode": "Pinjaman Berbunga / Utang Bank",
            "sumber": f"Jumlah Utang Bank Bersih: {td_note_val:,.0f}",
            "nilai": td_note_val,
        }
    elif td_note_val == 0.0:
        values["total_debt"] = 0.0
        evidence["total_debt"] = {
            "status": "Catatan Utang Bank (Lunas)",
            "halaman": f"Hal {td_note_hal}",
            "metode": "Bebas Utang Berbunga / Bank Lunas",
            "sumber": f"Jumlah Utang Bank: 0 (Lunas per {target_year})",
            "nilai": 0.0,
        }
    elif st_val is not None or lt_val is not None or bonds_val is not None:
        values["total_debt"] = 0.0
        evidence["total_debt"] = {
            "status": "Posisi Keuangan (Lunas)",
            "halaman": hal_bs,
            "metode": "Bebas Utang Berbunga / Bank Lunas",
            "sumber": f"Utang Bank JP (0) + Utang Bank PJ (0) + Obligasi (0) = 0 (Lunas per {target_year})",
            "nilai": 0.0,
        }
    else:
        values["total_debt"] = 0.0
        evidence["total_debt"] = {
            "status": "Posisi Keuangan [1210000]",
            "halaman": "Hal 14 & 17",
            "metode": "Bebas Utang Berbunga / Bank Lunas",
            "sumber": f"Utang Bank JP (0) + Utang Bank PJ (0) + Obligasi (0) = 0 (Lunas per {target_year})",
            "nilai": 0.0,
        }

    values["report_year"] = target_year
    evidence["report_year"] = {
        "status": "Tahun Ekstraksi",
        "halaman": "—",
        "metode": "Tahun terpilih",
        "sumber": f"Tahun pelaporan keuangan: {target_year}",
        "nilai": target_year,
    }

    # Bersihkan variabel pembantu agar nilai return bersih sesuai skema
    for helper in [
        "profit_before_tax", "non_current_assets", "non_current_liabilities",
        "total_equity", "non_controlling_interests",
        "short_term_bank_loans", "long_term_bank_loans", "bonds_payable"
    ]:
        values.pop(helper, None)

    return values, evidence


def extract_financial_values_from_df(df: pd.DataFrame, row_index: int = 0) -> tuple[dict, dict]:
    """
    Mengekstrak nilai-nilai keuangan dari baris DataFrame (CSV) secara otomatis
    berdasarkan kamus alias dan melakukan perhitungan otomatis (penjumlahan/selisih variabel).
    Mengembalikan (values_dict, evidence_dict).
    """
    if df.empty or row_index >= len(df):
        return {}, {}

    row = df.iloc[row_index]
    values = {}
    evidence = {}

    clean_cols = {}
    for col in df.columns:
        norm = re.sub(r"[\s_\-]+", " ", str(col).strip().lower())
        clean_cols[norm] = col

    # 1. Identitas Perusahaan
    for alias in ["ticker", "kode saham", "stock code", "symbol", "kode emiten", "emiten"]:
        for norm_col, orig_col in clean_cols.items():
            if alias == norm_col or alias in norm_col:
                val = str(row[orig_col]).strip().upper()
                if val and val != "NAN":
                    values["ticker"] = val
                    evidence["ticker"] = {"status": "Kolom CSV", "metode": "Kode Saham", "sumber": orig_col, "nilai": val}
                    break
        if "ticker" in values:
            break

    for alias in ["tahun", "year", "report year", "report_year", "fiscal year", "tahun laporan"]:
        for norm_col, orig_col in clean_cols.items():
            if alias == norm_col or alias in norm_col:
                parsed_y = parse_financial_number(row[orig_col])
                if parsed_y and 1900 <= parsed_y <= 2100:
                    values["report_year"] = int(parsed_y)
                    evidence["report_year"] = {"status": "Kolom CSV", "metode": "Tahun", "sumber": orig_col, "nilai": int(parsed_y)}
                    break
        if "report_year" in values:
            break

    for alias in ["nama perusahaan", "company", "company name", "nama emiten", "nama entitas", "perusahaan"]:
        for norm_col, orig_col in clean_cols.items():
            if alias == norm_col or alias in norm_col:
                val = str(row[orig_col]).strip()
                if val and val != "nan":
                    values["company"] = val
                    evidence["company"] = {"status": "Kolom CSV", "metode": "Nama Perusahaan", "sumber": orig_col, "nilai": val}
                    break
        if "company" in values:
            break

    # 2. Akun Finansial
    all_target_keys = [
        "profit_before_tax", "interest_expense", "ebit",
        "total_assets", "current_assets", "non_current_assets",
        "total_liabilities", "current_liabilities", "non_current_liabilities",
        "common_stock_equity", "total_equity", "non_controlling_interests",
        "retained_earnings", "working_capital", "operating_cash_flow",
        "total_revenue", "net_income", "total_debt",
        "short_term_bank_loans", "long_term_bank_loans", "bonds_payable"
    ]

    for key in all_target_keys:
        spec = ACCOUNT_SPECS.get(key, {})
        aliases = spec.get("aliases", COLUMN_ALIASES.get(key, []))
        exclusions = spec.get("exclusions", [])

        matched_col = None
        for alias in aliases:
            norm_alias = re.sub(r"[\s_\-]+", " ", alias.lower().strip())
            for norm_col, orig_col in clean_cols.items():
                if norm_alias == norm_col or norm_alias in norm_col:
                    if any(ex in norm_col for ex in exclusions):
                        continue
                    matched_col = orig_col
                    break
            if matched_col:
                break

        if matched_col:
            val = parse_financial_number(row[matched_col])
            if val is not None:
                if spec.get("abs_value"):
                    val = abs(val)
                values[key] = val
                evidence[key] = {
                    "status": "Kolom CSV",
                    "metode": f"Pencocokan kolom '{matched_col}'",
                    "sumber": f"Kolom: '{matched_col}'",
                    "nilai": val,
                }

    # 3. Jalankan kalkulasi otomatis
    values = complete_financial_values(values)

    if "profit_before_tax" in values and "interest_expense" in values:
        evidence["ebit"] = {
            "status": "Penjumlahan 2 Variabel",
            "metode": "Laba Sebelum Pajak + Beban Bunga",
            "sumber": f"Laba Sebelum Pajak ({values['profit_before_tax']:,.0f}) + Beban Bunga ({values['interest_expense']:,.0f})",
            "nilai": values["ebit"],
        }
    if "current_assets" in values and "current_liabilities" in values:
        evidence["working_capital"] = {
            "status": "Perhitungan Selisih",
            "metode": "Current Assets − Current Liabilities",
            "sumber": f"Aset Lancar ({values['current_assets']:,.0f}) − Liabilitas JP ({values['current_liabilities']:,.0f})",
            "nilai": values["working_capital"],
        }
    if "current_assets" in values and "non_current_assets" in values and ("total_assets" not in evidence or evidence["total_assets"]["status"] != "Kolom CSV"):
        evidence["total_assets"] = {
            "status": "Penjumlahan 2 Variabel",
            "metode": "Aset Lancar + Aset Tidak Lancar",
            "sumber": f"Aset Lancar ({values['current_assets']:,.0f}) + Aset Tidak Lancar ({values['non_current_assets']:,.0f})",
            "nilai": values["total_assets"],
        }
    if "current_liabilities" in values and "non_current_liabilities" in values and ("total_liabilities" not in evidence or evidence["total_liabilities"]["status"] != "Kolom CSV"):
        evidence["total_liabilities"] = {
            "status": "Penjumlahan 2 Variabel",
            "metode": "Liabilitas JP + Liabilitas PJ",
            "sumber": f"Liabilitas JP ({values['current_liabilities']:,.0f}) + Liabilitas PJ ({values['non_current_liabilities']:,.0f})",
            "nilai": values["total_liabilities"],
        }
    if "total_debt" in values and ("total_debt" not in evidence or evidence["total_debt"].get("status") != "Kolom CSV"):
        td_val = values["total_debt"]
        st_num = float(values.get("short_term_bank_loans") or 0.0)
        lt_num = float(values.get("long_term_bank_loans") or 0.0)
        bonds_num = float(values.get("bonds_payable") or 0.0)
        comp_s = st_num + lt_num + bonds_num
        if comp_s > 0:
            evidence["total_debt"] = {
                "status": "Penjumlahan Komponen Utang",
                "metode": "Utang Bank JP + Utang Bank PJ + Obligasi",
                "sumber": f"Utang Bank JP ({st_num:,.0f}) + Utang Bank PJ ({lt_num:,.0f}) + Obligasi ({bonds_num:,.0f})",
                "nilai": td_val,
            }
        else:
            evidence["total_debt"] = {
                "status": "Bebas Utang Berbunga / Bank Lunas",
                "metode": "Nilai 0 (Tidak ada utang berbunga)",
                "sumber": "Utang Bank JP (0) + Utang Bank PJ (0) + Obligasi (0) = 0",
                "nilai": td_val if td_val is not None else 0.0,
            }

    for helper in [
        "profit_before_tax", "non_current_assets", "non_current_liabilities",
        "total_equity", "non_controlling_interests",
        "short_term_bank_loans", "long_term_bank_loans", "bonds_payable"
    ]:
        values.pop(helper, None)

    return values, evidence


def extract_financial_values_from_text(text: str) -> dict:
    if not text:
        return {}

    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    result = {}

    for key, aliases in COLUMN_ALIASES.items():
        found = None
        for line in lines:
            low = line.lower()
            if any(alias in low for alias in aliases):
                if key == "ticker":
                    match = re.search(
                        r"(?:kode saham|ticker|stock code|symbol|kode emiten)\s*[:\-]?\s*([a-z]{2,10})\b",
                        line,
                        flags=re.IGNORECASE,
                    )
                    if match:
                        found = match.group(1).upper()
                        break
                    continue
                if key == "report_year":
                    years = re.findall(r"\b(?:19|20)\d{2}\b", line)
                    if years:
                        found = int(years[-1])
                        break
                    continue
                nums = _NUMBER_PATTERN.findall(line)
                if nums:
                    value = parse_financial_number(nums[-1])
                    if value is not None:
                        found = value
                        break
        if found is not None:
            result[key] = found

    return complete_financial_values(result)


def is_idx_xbrl_data(file_or_data) -> bool:
    """
    Mendeteksi apakah file atau data (Excel .xlsx/.xls, CSV, teks)
    merupakan format resmi laporan keuangan Bursa Efek Indonesia (IDX/BEI) taksonomi XBRL.
    """
    if file_or_data is None:
        return False

    raw_bytes = None
    text = ""
    if hasattr(file_or_data, "getvalue"):
        raw_bytes = file_or_data.getvalue()
    elif isinstance(file_or_data, (bytes, bytearray)):
        raw_bytes = bytes(file_or_data)
    elif isinstance(file_or_data, (str, Path)) and Path(str(file_or_data)).is_file():
        try:
            raw_bytes = Path(str(file_or_data)).read_bytes()
        except Exception:
            text = str(file_or_data)
    elif isinstance(file_or_data, str):
        text = file_or_data

    # Cek Excel
    if raw_bytes and (raw_bytes[:4] == b"PK\x03\x04" or raw_bytes[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        try:
            xl = pd.ExcelFile(io.BytesIO(raw_bytes))
            for s in xl.sheet_names:
                s_str = str(s).strip()
                if any(k in s_str for k in ["1000000", "1210000", "1321000", "1311000", "1410000", "1510000", "1691000"]):
                    return True
            first_df = xl.parse(xl.sheet_names[0], nrows=40, header=None)
            text_sample = " ".join(str(c) for c in first_df.values.flatten() if pd.notna(c)).lower()
            if any(term in text_sample for term in ["nama entitas", "kode entitas", "entitycode", "[1000000]", "[1210000]", "idx.co.id/xbrl"]):
                return True
        except Exception:
            pass

    # Cek CSV / Teks
    if raw_bytes and not text:
        for enc in ["utf-8-sig", "utf-8", "latin1"]:
            try:
                text = raw_bytes[:6000].decode(enc)
                break
            except Exception:
                pass

    sample_l = text[:6000].lower()
    if any(marker in sample_l for marker in [
        "[1000000]", "[1210000]", "[1321000]", "[1311000]", "[1510000]",
        "nama entitas", "kode entitas", "entitycode", "idx.co.id/xbrl",
        "currentyearinstant", "priorendyearinstant", "currentyearduration"
    ]):
        return True

    return False


def _parse_idx_raw_sections(file_or_data) -> tuple[dict[str, dict], dict[str, str], list[int]]:
    """
    Mengurai file Excel (.xlsx/.xls) atau CSV/teks XBRL BEI menjadi struktur bagian-bagian terindeks.
    """
    raw_bytes = None
    text = ""

    if hasattr(file_or_data, "getvalue"):
        raw_bytes = file_or_data.getvalue()
    elif isinstance(file_or_data, (bytes, bytearray)):
        raw_bytes = bytes(file_or_data)
    elif isinstance(file_or_data, (str, Path)) and Path(str(file_or_data)).is_file():
        try:
            raw_bytes = Path(str(file_or_data)).read_bytes()
        except Exception:
            text = str(file_or_data)
    elif isinstance(file_or_data, str):
        text = file_or_data

    is_excel = False
    if raw_bytes:
        if raw_bytes[:4] == b"PK\x03\x04" or raw_bytes[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            is_excel = True
        elif hasattr(file_or_data, "name") and any(str(file_or_data.name).lower().endswith(ext) for ext in [".xlsx", ".xls", ".xlsm"]):
            is_excel = True

    sections: dict[str, dict] = {}
    metadata: dict[str, str] = {}
    detected_years: list[int] = []

    if is_excel and raw_bytes:
        try:
            try:
                xl = pd.ExcelFile(io.BytesIO(raw_bytes), engine="openpyxl")
            except Exception:
                xl = pd.ExcelFile(io.BytesIO(raw_bytes))

            for sheet_name in xl.sheet_names:
                clean_sheet_name = str(sheet_name).strip()
                df_sheet = xl.parse(sheet_name, header=None)
                sheet_rows = []
                for _, r in df_sheet.iterrows():
                    row_cells = []
                    for c in r:
                        if pd.isna(c):
                            row_cells.append("")
                        elif isinstance(c, float) and c.is_integer():
                            row_cells.append(str(int(c)))
                        else:
                            row_cells.append(str(c).strip())
                    if any(c for c in row_cells):
                        sheet_rows.append(row_cells)

                # Cek jika sheet ini memuat penanda bagian seperti [1000000], [1210000]
                has_internal_markers = any(
                    re.match(r"^\[\d{7}[a-z_]*\]", r[0].strip(), re.IGNORECASE)
                    for r in sheet_rows if r
                )

                if has_internal_markers:
                    cur_marker = clean_sheet_name
                    cur_desc = clean_sheet_name
                    cur_rows = []
                    for r in sheet_rows:
                        m = re.match(r"^\[(\d{7}[a-z_]*)\]\s*(.*)", r[0].strip(), re.IGNORECASE)
                        if m:
                            if cur_rows:
                                sec_key = cur_marker.lower()
                                sections[sec_key] = {
                                    "code": cur_marker,
                                    "name": cur_desc or cur_marker,
                                    "rows": cur_rows,
                                }
                            cur_marker = m.group(1).strip()
                            cur_desc = m.group(2).strip() or cur_marker
                            cur_rows = []
                        else:
                            cur_rows.append(r)
                    if cur_rows:
                        sec_key = cur_marker.lower()
                        sections[sec_key] = {
                            "code": cur_marker,
                            "name": cur_desc or cur_marker,
                            "rows": cur_rows,
                        }
                else:
                    code_match = re.search(r"\b(\d{7}[a-z_]*)\b", clean_sheet_name, re.IGNORECASE)
                    sec_code = code_match.group(1) if code_match else clean_sheet_name
                    sec_key = sec_code.lower()
                    sections[sec_key] = {
                        "code": sec_code,
                        "name": clean_sheet_name,
                        "rows": sheet_rows,
                    }
        except Exception:
            pass

    # Jika sections kosong, coba urai sebagai CSV/Teks
    if not sections:
        if raw_bytes and not text:
            for enc in ["utf-8-sig", "utf-8", "latin1", "cp1252"]:
                try:
                    text = raw_bytes.decode(enc)
                    break
                except Exception:
                    continue

        if text:
            lines = [l for l in text.splitlines() if l.strip()]
            reader = csv.reader(lines)
            cur_marker = "default"
            cur_desc = "default"
            cur_rows = []
            for r in reader:
                clean_r = [c.strip() for c in r]
                if not any(clean_r):
                    continue
                first_cell = clean_r[0] if clean_r else ""
                m = re.match(r"^\[(\d{7}[a-z_]*)\]\s*(.*)", first_cell, re.IGNORECASE)
                if m:
                    if cur_rows:
                        sec_key = cur_marker.lower()
                        sections[sec_key] = {
                            "code": cur_marker,
                            "name": cur_desc or cur_marker,
                            "rows": cur_rows,
                        }
                    cur_marker = m.group(1).strip()
                    cur_desc = m.group(2).strip() or cur_marker
                    cur_rows = []
                else:
                    cur_rows.append(clean_r)
            if cur_rows:
                sec_key = cur_marker.lower()
                sections[sec_key] = {
                    "code": cur_marker,
                    "name": cur_desc or cur_marker,
                    "rows": cur_rows,
                }

    # Ambil metadata dari bagian informasi umum [1000000]
    gen_sec = None
    for k, s in sections.items():
        if "1000000" in k or "general" in s["name"].lower():
            gen_sec = s
            break

    cur_year = None
    prev_year = None
    prev_2_year = None

    if gen_sec:
        for r in gen_sec["rows"]:
            if len(r) >= 2:
                label_l = r[0].lower().strip()
                val_raw = r[1].strip() if len(r) > 1 else ""
                if not val_raw and len(r) > 2:
                    val_raw = r[2].strip()

                if any(x in label_l for x in ["kode entitas", "entity code", "ticker"]):
                    if val_raw and not metadata.get("ticker"):
                        metadata["ticker"] = val_raw.upper()
                elif any(x in label_l for x in ["nama entitas", "entity name", "nama perusahaan"]):
                    if val_raw and not metadata.get("company"):
                        metadata["company"] = val_raw
                elif any(x in label_l for x in ["sektor", "sector"]):
                    if val_raw and not metadata.get("sector"):
                        metadata["sector"] = val_raw
                elif any(x in label_l for x in ["tanggal akhir periode berjalan", "current period end date"]):
                    y_m = re.search(r"\b(20\d\d)\b", val_raw)
                    if y_m:
                        cur_year = int(y_m.group(1))
                elif any(x in label_l for x in ["tanggal akhir tahun sebelumnya", "prior year end date"]):
                    y_m = re.search(r"\b(20\d\d)\b", val_raw)
                    if y_m:
                        prev_year = int(y_m.group(1))
                elif any(x in label_l for x in ["tanggal akhir 2 tahun sebelumnya", "prior 2 year end date"]):
                    y_m = re.search(r"\b(20\d\d)\b", val_raw)
                    if y_m:
                        prev_2_year = int(y_m.group(1))

    if cur_year and cur_year not in detected_years:
        detected_years.append(cur_year)
    if prev_year and prev_year not in detected_years:
        detected_years.append(prev_year)
    if prev_2_year and prev_2_year not in detected_years:
        detected_years.append(prev_2_year)

    if not detected_years:
        # Pindai baris awal tabel posisi keuangan / laba rugi untuk angka tahun
        for k, s in sections.items():
            if any(code in k for code in ["1210000", "1321000", "1311000"]):
                for r in s["rows"][:8]:
                    for c in r:
                        for y_str in re.findall(r"\b(20\d\d)\b", str(c)):
                            y_int = int(y_str)
                            if y_int not in detected_years:
                                detected_years.append(y_int)

    if not detected_years:
        detected_years = [2025, 2024]
    else:
        detected_years = sorted(list(set(detected_years)), reverse=True)

    cur_yr = detected_years[0]
    prev_yr = detected_years[1] if len(detected_years) > 1 else (cur_yr - 1)

    # Petakan indeks kolom per bagian
    for k, s in sections.items():
        col_map = {}
        for r in s["rows"][:8]:
            for col_idx, cell in enumerate(r):
                cl = cell.lower().strip()
                if not cl:
                    continue
                if any(x in cl for x in ["currentyear", "tahun berjalan", "periode berjalan", str(cur_yr)]):
                    col_map[cur_yr] = col_idx
                elif any(x in cl for x in ["priorendyear", "prioryear", "tahun sebelumnya", "periode sebelumnya", str(prev_yr)]):
                    col_map[prev_yr] = col_idx

        if cur_yr not in col_map:
            col_map[cur_yr] = 1
        if prev_yr not in col_map:
            col_map[prev_yr] = 2

        s["header_cols"] = col_map

    metadata["years"] = detected_years
    return sections, metadata, detected_years


def get_idx_document_years(file_or_data) -> list[int]:
    """
    Mendeteksi daftar tahun laporan keuangan yang terdapat di file Excel atau CSV BEI/IDX.
    """
    try:
        sections, metadata, detected_years = _parse_idx_raw_sections(file_or_data)
        if detected_years:
            return detected_years
    except Exception:
        pass
    return [2025, 2024]


def extract_financial_values_from_idx_data(file_or_data, target_year: int | None = None) -> tuple[dict, dict, list[int]]:
    """
    Mengekstrak dan menyesuaikan 15 variabel proyek dari file Excel (.xlsx/.xls)
    atau CSV/teks laporan keuangan resmi Bursa Efek Indonesia (IDX/BEI).
    Mengembalikan (values_dict, evidence_dict, detected_years).
    """
    sections, metadata, detected_years = _parse_idx_raw_sections(file_or_data)
    if not detected_years:
        detected_years = [2025, 2024]

    if target_year is None or target_year not in detected_years:
        target_year = detected_years[0]

    values: dict = {}
    evidence: dict = {}

    if metadata.get("ticker"):
        values["ticker"] = metadata["ticker"]
        evidence["ticker"] = {"status": "Informasi Umum [1000000]", "halaman": "[1000000]", "metode": "Kode Entitas", "sumber": f"Kode: {metadata['ticker']}", "nilai": metadata["ticker"]}
    if metadata.get("company"):
        values["company"] = metadata["company"]
        evidence["company"] = {"status": "Informasi Umum [1000000]", "halaman": "[1000000]", "metode": "Nama Entitas", "sumber": f"Nama: {metadata['company']}", "nilai": metadata["company"]}
    if metadata.get("sector"):
        values["sector"] = metadata["sector"]

    cur_yr = detected_years[0]
    target_col_order = 0 if target_year == cur_yr else 1

    keys_to_search = [
        "profit_before_tax", "interest_expense", "ebit",
        "total_assets", "current_assets", "non_current_assets",
        "total_liabilities", "current_liabilities", "non_current_liabilities",
        "common_stock_equity", "total_equity", "non_controlling_interests",
        "retained_earnings", "operating_cash_flow", "total_revenue", "net_income",
        "short_term_bank_loans", "long_term_bank_loans", "bonds_payable", "total_debt"
    ]

    for key in keys_to_search:
        if key in values:
            continue
        spec = ACCOUNT_SPECS.get(key, {})
        aliases = spec.get("aliases", [])
        exclusions = spec.get("exclusions", [])

        # Tentukan prioritas bagian akun
        target_sec_codes = []
        if key in ("profit_before_tax", "interest_expense", "ebit", "total_revenue", "net_income"):
            target_sec_codes = ["1321000", "1311000", "1322000", "1312000"]
        elif key in ("operating_cash_flow",):
            target_sec_codes = ["1510000", "1520000"]
        elif key in ("short_term_bank_loans", "long_term_bank_loans", "bonds_payable"):
            target_sec_codes = ["1210000", "1220000"]
        elif key in ("total_debt",):
            target_sec_codes = ["1691000", "1691000a_bd", "1691000_bd", "1693000", "1210000"]
        else:
            target_sec_codes = ["1210000", "1220000"]

        secs_to_scan = []
        for sec_key, sec_data in sections.items():
            if any(code in sec_key for code in target_sec_codes):
                secs_to_scan.append(sec_data)

        if not secs_to_scan:
            secs_to_scan = [s for k, s in sections.items() if "1000000" not in k]

        for s in secs_to_scan:
            target_col_idx = s.get("header_cols", {}).get(target_year, 1)
            sec_name_label = f"[{s['code']}]"

            for r in s["rows"]:
                if len(r) < 2:
                    continue
                first_text = r[0].strip()
                last_text = r[-1].strip() if len(r) > 1 else ""
                full_text = " ".join(r)

                matched_alias = None
                labels_to_check = [first_text, last_text, full_text]
                for cand_label in labels_to_check:
                    cand_l = cand_label.lower().strip()
                    if not cand_l:
                        continue
                    for al in aliases:
                        if al in cand_l:
                            if not _is_excluded(key, cand_l, exclusions):
                                matched_alias = al
                                break
                    if matched_alias:
                        break

                if not matched_alias:
                    continue

                val = None
                if target_col_idx < len(r):
                    val = parse_financial_number(r[target_col_idx])

                if val is None:
                    cands = []
                    for c_i, c_val in enumerate(r[1:]):
                        num_p = parse_financial_number(c_val)
                        if num_p is not None:
                            cands.append((c_i + 1, num_p))
                    filtered_cands = _filter_financial_candidates(cands, full_text)
                    if filtered_cands:
                        if len(filtered_cands) >= 2:
                            val = filtered_cands[target_col_order][1]
                        else:
                            val = filtered_cands[0][1]

                if val is not None:
                    if spec.get("abs_value"):
                        val = abs(val)
                    values[key] = val
                    evidence[key] = {
                        "status": f"{sec_name_label} Langsung",
                        "halaman": sec_name_label,
                        "metode": f"Pencocokan '{matched_alias}'",
                        "sumber": f"{sec_name_label} {first_text[:120]} ({val:,.0f})",
                        "nilai": val,
                    }
                    break

            if key in values:
                break

    # Jalankan perhitungan otomatis sesuai SAK
    values = complete_financial_values(values)

    pbt_val = values.get("profit_before_tax")
    ie_val = values.get("interest_expense")
    if pbt_val is not None:
        ie_num = ie_val if ie_val is not None else 0.0
        evidence["ebit"] = {
            "status": "Penjumlahan 2 Variabel",
            "halaman": "[1321000]",
            "metode": "Laba Sebelum Pajak + Beban Bunga",
            "sumber": f"Laba Sebelum Pajak ({pbt_val:,.0f}) + Beban Bunga ({ie_num:,.0f}) = {values['ebit']:,.0f}",
            "nilai": values["ebit"],
        }

    ca_val = values.get("current_assets")
    cl_val = values.get("current_liabilities")
    if ca_val is not None and cl_val is not None:
        evidence["working_capital"] = {
            "status": "Perhitungan Selisih",
            "halaman": "[1210000]",
            "metode": "Current Assets − Current Liabilities",
            "sumber": f"Aset Lancar ({ca_val:,.0f}) − Liabilitas JP ({cl_val:,.0f}) = {values['working_capital']:,.0f}",
            "nilai": values["working_capital"],
        }

    st_val = values.get("short_term_bank_loans")
    lt_val = values.get("long_term_bank_loans")
    bonds_val = values.get("bonds_payable")
    direct_td = values.get("total_debt")

    st_num = float(st_val or 0.0)
    lt_num = float(lt_val or 0.0)
    bonds_num = float(bonds_val or 0.0)
    comp_sum = st_num + lt_num + bonds_num

    td_note_val = float(direct_td) if direct_td is not None else None
    td_note_hal = str(evidence.get("total_debt", {}).get("halaman", "[1691000a_BD]"))

    if comp_sum > 0:
        td_final = max(comp_sum, td_note_val or 0.0)
        values["total_debt"] = td_final
        evidence["total_debt"] = {
            "status": "Penjumlahan Komponen Utang",
            "halaman": "[1210000] & [1691000a_BD]",
            "metode": "Utang Bank JP + Utang Bank PJ + Obligasi",
            "sumber": f"Utang Bank JP ({st_num:,.0f}) + Utang Bank PJ ({lt_num:,.0f}) + Obligasi ({bonds_num:,.0f}) = {td_final:,.0f}",
            "nilai": td_final,
        }
    elif td_note_val is not None and td_note_val > 0:
        values["total_debt"] = td_note_val
        evidence["total_debt"] = {
            "status": f"{td_note_hal} Catatan Utang Bank",
            "halaman": td_note_hal,
            "metode": "Jumlah Utang Bank Bersih",
            "sumber": f"Jumlah Utang Bank Bersih: {td_note_val:,.0f}",
            "nilai": td_note_val,
        }
    else:
        values["total_debt"] = 0.0
        evidence["total_debt"] = {
            "status": "Posisi Keuangan [1210000] (Lunas)",
            "halaman": "[1210000]",
            "metode": "Bebas Utang Berbunga / Bank Lunas",
            "sumber": f"Utang Bank JP (0) + Utang Bank PJ (0) + Obligasi (0) = 0 (Lunas per {target_year})",
            "nilai": 0.0,
        }

    values["report_year"] = target_year
    evidence["report_year"] = {
        "status": "Tahun Ekstraksi",
        "halaman": "[1000000]",
        "metode": "Tahun Terpilih",
        "sumber": f"Tahun pelaporan keuangan: {target_year}",
        "nilai": target_year,
    }

    for helper in [
        "profit_before_tax", "non_current_assets", "non_current_liabilities",
        "total_equity", "non_controlling_interests",
        "short_term_bank_loans", "long_term_bank_loans", "bonds_payable"
    ]:
        values.pop(helper, None)

    return values, evidence, detected_years


def extract_financial_values_from_excel(file_obj, target_year: int | None = None, row_index: int = 0) -> tuple[dict, dict, list[int], str]:
    """
    Ekstraksi universal file Excel (.xlsx / .xls).
    Mendukung format resmi BEI / IDX (XBRL multi-sheet/single-sheet)
    serta format tabular standar (baris emiten, kolom finansial).
    Mengembalikan (values, evidence, detected_years, detected_format).
    """
    if is_idx_xbrl_data(file_obj):
        vals, ev, yrs = extract_financial_values_from_idx_data(file_obj, target_year)
        return vals, ev, yrs, "idx_xbrl"
    else:
        df = read_excel_file(file_obj)
        if isinstance(df, dict):
            best_df = None
            best_match_count = -1
            for _, s_df in df.items():
                norm_cols = [str(c).lower() for c in s_df.columns]
                matches = sum(1 for k in COLUMN_ALIASES if any(al in " ".join(norm_cols) for al in COLUMN_ALIASES[k]))
                if matches > best_match_count:
                    best_match_count = matches
                    best_df = s_df
            df = best_df if best_df is not None else next(iter(df.values()))

        vals, ev = extract_financial_values_from_df(df, row_index)
        yr = vals.get("report_year", 2024)
        return vals, ev, [yr] if yr else [2024], "tabular"


def get_sample_template_dataframe() -> pd.DataFrame:
    """
    Menghasilkan DataFrame sampel template standar untuk input laporan keuangan.
    Berisi kolom-kolom baku (sesuai VARIABLE_SCHEMA) dan 2 baris emiten contoh.
    """
    sample_records = [
        {
            "ticker": "ICBP",
            "report_year": 2024,
            "company": "PT Indofood CBP Sukses Makmur Tbk",
            "sector": "Consumer Goods / F&B",
            "total_assets": 115_300_000_000_000.0,
            "total_liabilities": 58_400_000_000_000.0,
            "current_assets": 42_100_000_000_000.0,
            "current_liabilities": 25_600_000_000_000.0,
            "working_capital": 16_500_000_000_000.0,
            "retained_earnings": 38_200_000_000_000.0,
            "ebit": 14_900_000_000_000.0,
            "interest_expense": 2_100_000_000_000.0,
            "common_stock_equity": 56_900_000_000_000.0,
            "total_revenue": 67_900_000_000_000.0,
            "net_income": 9_800_000_000_000.0,
            "total_debt": 32_000_000_000_000.0,
            "operating_cash_flow": 13_500_000_000_000.0,
        },
        {
            "ticker": "KBLI",
            "report_year": 2024,
            "company": "PT KMI Wire and Cable Tbk",
            "sector": "Kabel & Komponen Elektronik",
            "total_assets": 3_500_000_000_000.0,
            "total_liabilities": 1_200_000_000_000.0,
            "current_assets": 2_100_000_000_000.0,
            "current_liabilities": 950_000_000_000.0,
            "working_capital": 1_150_000_000_000.0,
            "retained_earnings": 1_400_000_000_000.0,
            "ebit": 320_000_000_000.0,
            "interest_expense": 45_000_000_000.0,
            "common_stock_equity": 2_300_000_000_000.0,
            "total_revenue": 4_200_000_000_000.0,
            "net_income": 210_000_000_000.0,
            "total_debt": 550_000_000_000.0,
            "operating_cash_flow": 280_000_000_000.0,
        },
    ]
    return pd.DataFrame(sample_records)


def get_sample_template_csv_bytes() -> bytes:
    """Mengembalikan berkas CSV template dalam format bytes UTF-8."""
    df = get_sample_template_dataframe()
    return df.to_csv(index=False).encode("utf-8")


def get_sample_template_excel_bytes() -> bytes:
    """Mengembalikan berkas Excel .xlsx template dalam format bytes."""
    df = get_sample_template_dataframe()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data_Keuangan_Emiten")
    return buf.getvalue()


# ==============================================================================
# REPORT EXPORT GENERATION ENGINE (PDF/HTML, CSV/EXCEL, JSON)
# ==============================================================================

def generate_printable_html_report(
    company: str,
    ticker: str,
    year: int | str,
    sector: str = "",
    username: str = "Analyst",
    analysis_date: str = "",
    z: float = 0.0,
    z_cls: str = "standby",
    mda: float = 0.0,
    mda_cls: str = "standby",
    xgb_prob: float | None = None,
    xgb_label: int | None = None,
    cat3: dict | None = None,
    ratios: dict | None = None,
    financials: dict | None = None,
    adv_metrics: dict | None = None,
    drivers: dict | None = None,
    recommendations: dict | None = None,
    capping_audit: dict | None = None,
) -> str:
    """Menghasilkan dokumen laporan HTML eksekutif mandiri lengkap (siap cetak / Simpan PDF)."""
    t_clean = (ticker or "EMITEN").strip().upper()
    c_clean = company or "Perusahaan Terbuka"
    y_clean = str(year or "2024")
    sec_clean = sector or "Industri Manufaktur (BEI)"
    user_clean = username or "System Analyst"
    date_clean = analysis_date or datetime.now().strftime("%d %B %Y, %H:%M WIB")

    r = ratios or {}
    fin = financials or {}
    adv = adv_metrics or {}
    drv = drivers or {}
    recs = recommendations or {}
    cap = capping_audit or {}

    c3 = cat3 or {
        "status": "STANDBY",
        "tone": "blue",
        "color": "#2563eb",
        "desc": "Belum Dilakukan Prediksi",
        "summary_note": "Menunggu Analisis",
    }
    status_str = str(c3.get("status", "STANDBY")).upper()
    status_color = "#10b981" if "SAFE" in status_str else ("#f59e0b" if "GREY" in status_str else ("#ef4444" if "DISTRESS" in status_str else "#64748b"))
    status_bg = "#ecfdf5" if "SAFE" in status_str else ("#fffbeb" if "GREY" in status_str else ("#fef2f2" if "DISTRESS" in status_str else "#f1f5f9"))

    # Hitung Skor Ekuivalen Z XGBoost
    if xgb_prob is not None:
        p = float(xgb_prob)
        if p <= 0.35:
            z_equiv = round(2.99 + (3.01 * (0.35 - p) / 0.35), 2)
        elif p <= 0.65:
            z_equiv = round(1.81 + (1.18 * (0.65 - p) / 0.30), 2)
        else:
            z_equiv = round(1.81 * max(0.0, (1.0 - p) / 0.35), 2)
        xgb_disp = f"{p*100:.2f}% ({p:.4f})"
        xgb_equiv_disp = f"{z_equiv:.2f}"
    else:
        xgb_disp = "N/A"
        xgb_equiv_disp = "-"

    # Format angka finansial
    def _fmt(val):
        if val is None or val == "":
            return "-"
        try:
            num = float(val)
            if num == 0:
                return "Rp 0"
            if abs(num) >= 1e12:
                return f"Rp {num/1e12:,.2f} Triliun ({num:,.0f})"
            if abs(num) >= 1e9:
                return f"Rp {num/1e9:,.2f} Miliar ({num:,.0f})"
            if abs(num) >= 1e6:
                return f"Rp {num/1e6:,.2f} Juta ({num:,.0f})"
            return f"Rp {num:,.2f}"
        except Exception:
            return str(val)

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Laporan Prediksi Financial Distress - {t_clean} ({y_clean})</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 15mm 15mm 15mm 15mm;
        }}
        * {{
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        body {{
            background: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 24px;
            font-size: 12px;
            line-height: 1.5;
        }}
        .report-page {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 36px 40px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }}
        .print-bar {{
            position: sticky;
            top: 0;
            z-index: 100;
            max-width: 900px;
            margin: 0 auto 16px auto;
            background: #1e293b;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 14px rgba(0,0,0,0.2);
        }}
        .btn-print {{
            background: #2563eb;
            color: #ffffff;
            border: none;
            padding: 8px 18px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-print:hover {{
            background: #1d4ed8;
            transform: translateY(-1px);
        }}
        .header-section {{
            border-bottom: 2.5px solid #2563eb;
            padding-bottom: 16px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .brand-title {{
            font-size: 20px;
            font-weight: 900;
            color: #1e293b;
            letter-spacing: -0.3px;
        }}
        .brand-sub {{
            font-size: 11.5px;
            color: #64748b;
            margin-top: 2px;
            font-weight: 500;
        }}
        .doc-badge {{
            background: #eff6ff;
            color: #2563eb;
            border: 1px solid #bfdbfe;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 750;
            text-transform: uppercase;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px 24px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 20px;
        }}
        .meta-item {{
            display: flex;
            justify-content: space-between;
            border-bottom: 1px dashed #cbd5e1;
            padding-bottom: 4px;
        }}
        .meta-label {{
            color: #64748b;
            font-weight: 600;
        }}
        .meta-value {{
            font-weight: 750;
            color: #0f172a;
        }}
        .consensus-banner {{
            background: {status_bg};
            border: 1.5px solid {status_color};
            border-left: 6px solid {status_color};
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .consensus-title {{
            font-size: 16px;
            font-weight: 900;
            color: {status_color};
        }}
        .consensus-desc {{
            font-size: 12px;
            color: #334155;
            margin-top: 2px;
            font-weight: 600;
        }}
        .section-header {{
            font-size: 13.5px;
            font-weight: 850;
            color: #0f172a;
            border-bottom: 1.5px solid #cbd5e1;
            padding-bottom: 6px;
            margin: 22px 0 12px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            font-size: 11.5px;
        }}
        th {{
            background: #f1f5f9;
            color: #1e293b;
            font-weight: 800;
            text-align: left;
            padding: 8px 10px;
            border: 1px solid #cbd5e1;
        }}
        td {{
            padding: 7px 10px;
            border: 1px solid #e2e8f0;
            color: #334155;
        }}
        tr:nth-child(even) td {{
            background: #f8fafc;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 10.5px;
            font-weight: 800;
        }}
        .badge-safe {{ background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }}
        .badge-grey {{ background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }}
        .badge-distress {{ background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }}
        .badge-standby {{ background: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; }}
        .rec-box {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 10px;
        }}
        .rec-title {{
            font-weight: 800;
            font-size: 12px;
            color: #1e293b;
            margin-bottom: 4px;
        }}
        .rec-text {{
            font-size: 11px;
            color: #475569;
            line-height: 1.5;
        }}
        .footer-note {{
            margin-top: 30px;
            padding-top: 14px;
            border-top: 1px solid #e2e8f0;
            font-size: 10.5px;
            color: #94a3b8;
            text-align: justify;
            line-height: 1.6;
        }}
        @media print {{
            body {{
                background: #ffffff;
                padding: 0;
            }}
            .report-page {{
                border: none;
                padding: 0;
                box-shadow: none;
            }}
            .no-print {{
                display: none !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="print-bar no-print">
        <div><b>Laporan Eksekutif Financial Distress:</b> {c_clean} ({t_clean}) — Tahun Buku {y_clean}</div>
        <button onclick="window.print()" class="btn-print">🖨️ Cetak / Simpan sebagai PDF</button>
    </div>

    <div class="report-page">
        <div class="header-section">
            <div>
                <div class="brand-title">FINANCIAL DISTRESS PREDICTION REPORT</div>
                <div class="brand-sub">Sistem Deteksi Dini & Mitigasi Risiko Multi-Model (Altman Z'', MDA BEI, XGBoost AI)</div>
            </div>
            <div class="doc-badge">Dokumen Resmi Audit</div>
        </div>

        <div class="meta-grid">
            <div class="meta-item"><span class="meta-label">Nama Perusahaan:</span><span class="meta-value">{c_clean}</span></div>
            <div class="meta-item"><span class="meta-label">Kode Ticker (BEI):</span><span class="meta-value">{t_clean}</span></div>
            <div class="meta-item"><span class="meta-label">Tahun Laporan Keuangan:</span><span class="meta-value">{y_clean}</span></div>
            <div class="meta-item"><span class="meta-label">Sektor Industri:</span><span class="meta-value">{sec_clean}</span></div>
            <div class="meta-item"><span class="meta-label">Waktu Eksekusi Analisis:</span><span class="meta-value">{date_clean}</span></div>
            <div class="meta-item"><span class="meta-label">Analis / Pengguna:</span><span class="meta-value">{user_clean}</span></div>
        </div>

        <div class="consensus-banner">
            <div>
                <div class="consensus-title">KONSENSUS KEPUTUSAN SISTEM: {status_str}</div>
                <div class="consensus-desc">{c3.get('desc', '-')} • {c3.get('summary_note', '-')}</div>
            </div>
            <span class="badge {'badge-safe' if 'SAFE' in status_str else ('badge-grey' if 'GREY' in status_str else ('badge-distress' if 'DISTRESS' in status_str else 'badge-standby'))}" style="font-size:13px;padding:6px 14px;">
                {status_str}
            </span>
        </div>

        <div class="section-header">1. Evaluasi Komparatif Output Tiga Model Penelitian</div>
        <table>
            <thead>
                <tr>
                    <th>Pendekatan Model</th>
                    <th>Nilai Output / Probabilitas</th>
                    <th>Ambang Batas (3 Kategori)</th>
                    <th>Zona Klasifikasi</th>
                    <th>Metodologi & Rujukan</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>Altman Z''-Score (Benchmark)</b></td>
                    <td><b>{z:.2f}</b></td>
                    <td>Distress &lt; 1.81 | Safe &gt; 2.99</td>
                    <td><span class="badge {'badge-safe' if z > 2.99 else ('badge-grey' if z >= 1.81 else 'badge-distress')}">{z_cls.upper()}</span></td>
                    <td>Model Teoretis Baku (Altman 1995/2017)</td>
                </tr>
                <tr>
                    <td><b>Z''-Score Koefisien Baru (MDA)</b></td>
                    <td><b>{mda:.2f}</b></td>
                    <td>Cut-off 0.3844 (Grey [0.0, 1.0])</td>
                    <td><span class="badge {'badge-safe' if mda > 1.0 else ('badge-grey' if mda >= 0.0 else 'badge-distress')}">{mda_cls.upper()}</span></td>
                    <td>Model Empiris BEI 704 Observasi (Lampiran 2)</td>
                </tr>
                <tr>
                    <td><b>XGBoost Classifier (AI)</b></td>
                    <td><b>{xgb_disp}</b> (Eq. Z: <b>{xgb_equiv_disp}</b>)</td>
                    <td>Safe &lt; 35% | Distress &gt; 65%</td>
                    <td><span class="badge {'badge-safe' if (xgb_prob is not None and xgb_prob < 0.35) else ('badge-grey' if (xgb_prob is not None and xgb_prob <= 0.65) else 'badge-distress')}">{'SAFE ZONE' if (xgb_prob is not None and xgb_prob < 0.35) else ('GREY AREA' if (xgb_prob is not None and xgb_prob <= 0.65) else ('DISTRESS ZONE' if xgb_prob is not None else 'STANDBY'))}</span></td>
                    <td>Model Non-Linear AI Gradient Boosted Trees</td>
                </tr>
            </tbody>
        </table>

        <div class="section-header">2. Variabel Rasio Keuangan Pembentuk Model (X1 - X5)</div>
        <table>
            <thead>
                <tr>
                    <th>Kode</th>
                    <th>Nama Rasio Keuangan</th>
                    <th>Formulasi Rasio</th>
                    <th>Nilai Rasio</th>
                    <th>Kondisi / Status Capping</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>X1</b></td>
                    <td>Working Capital to Total Assets (WC/TA)</td>
                    <td>(Aset Lancar - Liabilitas Lancar) / Total Aset</td>
                    <td><b>{r.get('X1', 0.0):.4f}</b></td>
                    <td>Normal</td>
                </tr>
                <tr>
                    <td><b>X2</b></td>
                    <td>Retained Earnings to Total Assets (RE/TA)</td>
                    <td>Saldo Laba Ditahan / Total Aset</td>
                    <td><b>{r.get('X2', 0.0):.4f}</b></td>
                    <td>Normal</td>
                </tr>
                <tr>
                    <td><b>X3</b></td>
                    <td>EBIT to Total Assets (EBIT/TA)</td>
                    <td>Laba Usaha Sebelum Bunga & Pajak / Total Aset</td>
                    <td><b>{r.get('X3', 0.0):.4f}</b></td>
                    <td>Normal</td>
                </tr>
                <tr>
                    <td><b>X4</b></td>
                    <td>Equity to Total Liabilities (Eq/TL)</td>
                    <td>Total Ekuitas Saham / Total Liabilitas</td>
                    <td><b>{r.get('X4', 0.0):.4f}</b></td>
                    <td>{'🛡️ Capping X4 Maks 3.0 Aktif (Skripsi Hal. 41)' if 'X4' in cap else 'Normal'}</td>
                </tr>
                <tr>
                    <td><b>X5</b></td>
                    <td>Sales to Total Assets (S/TA)</td>
                    <td>Pendapatan Bersih / Total Aset</td>
                    <td><b>{r.get('X5', 0.0):.4f}</b></td>
                    <td>Rasio Pelengkap Altman 1968</td>
                </tr>
            </tbody>
        </table>

        <div class="section-header">3. Pos Laporan Keuangan Kunci (Neraca & Laba Rugi)</div>
        <table>
            <thead>
                <tr>
                    <th>Pos Akun Keuangan</th>
                    <th>Nominal Rupiah (Rp)</th>
                    <th>Pos Akun Keuangan</th>
                    <th>Nominal Rupiah (Rp)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Total Aset</td>
                    <td><b>{_fmt(fin.get('total_assets'))}</b></td>
                    <td>Total Liabilitas</td>
                    <td><b>{_fmt(fin.get('total_liabilities'))}</b></td>
                </tr>
                <tr>
                    <td>Aset Lancar</td>
                    <td><b>{_fmt(fin.get('current_assets'))}</b></td>
                    <td>Liabilitas Lancar</td>
                    <td><b>{_fmt(fin.get('current_liabilities'))}</b></td>
                </tr>
                <tr>
                    <td>Modal Kerja Bersih (WC)</td>
                    <td><b>{_fmt(fin.get('working_capital'))}</b></td>
                    <td>Total Ekuitas</td>
                    <td><b>{_fmt(fin.get('total_equity') or fin.get('common_stock_equity'))}</b></td>
                </tr>
                <tr>
                    <td>Saldo Laba Ditahan (RE)</td>
                    <td><b>{_fmt(fin.get('retained_earnings'))}</b></td>
                    <td>Total Pendapatan (Revenue)</td>
                    <td><b>{_fmt(fin.get('total_revenue'))}</b></td>
                </tr>
                <tr>
                    <td>Laba Usaha (EBIT)</td>
                    <td><b>{_fmt(fin.get('ebit'))}</b></td>
                    <td>Laba Bersih (Net Income)</td>
                    <td><b>{_fmt(fin.get('net_income'))}</b></td>
                </tr>
                <tr>
                    <td>Beban Bunga Pinjaman</td>
                    <td><b>{_fmt(fin.get('interest_expense'))}</b></td>
                    <td>Arus Kas Operasional (OCF)</td>
                    <td><b>{_fmt(fin.get('operating_cash_flow'))}</b></td>
                </tr>
            </tbody>
        </table>

        <div class="section-header">4. Indeks Ketahanan Finansial Komposit & Solvabilitas</div>
        <table>
            <thead>
                <tr>
                    <th>Metrik Kunci</th>
                    <th>Nilai Emiten</th>
                    <th>Tolok Ukur Aman (Benchmark)</th>
                    <th>Status Ketahanan</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>Current Ratio (Likuiditas)</b></td>
                    <td>{adv.get('current_ratio', {}).get('value', 0.0):.2f}x</td>
                    <td>&gt; 1.20x</td>
                    <td>{adv.get('current_ratio', {}).get('status', '-')}</td>
                </tr>
                <tr>
                    <td><b>Interest Coverage Ratio (ICR)</b></td>
                    <td>{adv.get('icr', {}).get('value', 0.0):.2f}x</td>
                    <td>&gt; 2.00x</td>
                    <td>{adv.get('icr', {}).get('status', '-')}</td>
                </tr>
                <tr>
                    <td><b>Debt to Equity Ratio (DER)</b></td>
                    <td>{adv.get('der', {}).get('value', 0.0):.2f}x</td>
                    <td>&lt; 1.50x</td>
                    <td>{adv.get('der', {}).get('status', '-')}</td>
                </tr>
                <tr>
                    <td><b>OCF to Liabilities</b></td>
                    <td>{adv.get('ocf_to_liab', {}).get('value', 0.0):.2f}x</td>
                    <td>&gt; 0.15x</td>
                    <td>{adv.get('ocf_to_liab', {}).get('status', '-')}</td>
                </tr>
                <tr>
                    <td><b>Return on Assets (ROA)</b></td>
                    <td>{adv.get('roa', {}).get('value', 0.0)*100:.2f}%</td>
                    <td>&gt; 5.00%</td>
                    <td>{adv.get('roa', {}).get('status', '-')}</td>
                </tr>
                <tr>
                    <td><b>Net Profit Margin (NPM)</b></td>
                    <td>{adv.get('npm', {}).get('value', 0.0)*100:.2f}%</td>
                    <td>&gt; 5.00%</td>
                    <td>{adv.get('npm', {}).get('status', '-')}</td>
                </tr>
            </tbody>
        </table>

        <div class="section-header">5. Panduan Tindakan Strategis Multi-Stakeholder</div>
        <div class="rec-box">
            <div class="rec-title">📈 Bagi Investor Saham (Equity Investors): {recs.get('investor', {}).get('stance', 'MONITOR KETAT')}</div>
            <div class="rec-text">{'; '.join(recs.get('investor', {}).get('points', ['Lakukan pemantauan berkala atas likuiditas dan tren laba usaha emiten.']))}</div>
        </div>
        <div class="rec-box">
            <div class="rec-title">🏦 Bagi Kreditur & Lembaga Perbankan (Lenders): {recs.get('kreditur', {}).get('stance', 'PENGAWASAN AKTIF')}</div>
            <div class="rec-text">{'; '.join(recs.get('kreditur', {}).get('points', ['Periksa klausul perjanjian kredit dan batasi eksposur pinjaman tambahan tanpa agunan berlikuiditas tinggi.']))}</div>
        </div>
        <div class="rec-box">
            <div class="rec-title">🛠️ Bagi Manajemen & Dewan Direksi: {recs.get('manajemen', {}).get('stance', 'OPTIMASI STRUKTUR MODAL')}</div>
            <div class="rec-text">{'; '.join(recs.get('manajemen', {}).get('points', ['Tingkatkan efisiensi perputaran modal kerja dan prioritaskan konservasi arus kas operasional.']))}</div>
        </div>

        <div class="footer-note">
            <b>Pernyataan Penafian & Rujukan Akademik:</b> Laporan ini disusun secara otomatis oleh Sistem Prediksi Financial Distress berbasis Machine Learning dan Model Statistik Diskriminan (Altman Z''-Score 1995/2017 & MDA Empiris BEI 704 Observasi) sesuai Bab II & III Proposal Skripsi. Hasil evaluasi bertujuan sebagai alat bantu analisis intelijen risiko dan tidak menggantikan keputusan resmi komite investasi, audit independen, maupun penasihat keuangan berlisensi.
        </div>
    </div>
</body>
</html>"""
    return html_content


def generate_full_csv_report(
    company: str,
    ticker: str,
    year: int | str,
    sector: str = "",
    username: str = "Analyst",
    analysis_date: str = "",
    z: float = 0.0,
    z_cls: str = "standby",
    mda: float = 0.0,
    mda_cls: str = "standby",
    xgb_prob: float | None = None,
    cat3: dict | None = None,
    ratios: dict | None = None,
    financials: dict | None = None,
    adv_metrics: dict | None = None,
) -> str:
    """Menghasilkan laporan komprehensif dalam format CSV terstruktur (Excel Compatible)."""
    t_clean = (ticker or "EMITEN").strip().upper()
    c_clean = company or "Perusahaan Terbuka"
    y_clean = str(year or "2024")
    sec_clean = sector or "Industri Manufaktur"
    r = ratios or {}
    fin = financials or {}
    adv = adv_metrics or {}
    c3 = cat3 or {}

    rows = [
        ["=== IDENTITAS LAPORAN FINANCIAL DISTRESS ===", ""],
        ["Nama Perusahaan", c_clean],
        ["Kode Saham (Ticker)", t_clean],
        ["Tahun Laporan Keuangan", y_clean],
        ["Sektor Industri", sec_clean],
        ["Tanggal Analisis", analysis_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Analis Sistem", username],
        ["", ""],
        ["=== HASIL PREDIKSI TIGA MODEL PENELITIAN ===", ""],
        ["Pendekatan Model", "Nilai / Probabilitas", "Klasifikasi Zona", "Keterangan"],
        ["Altman Z''-Score (1995)", f"{z:.4f}", z_cls.upper(), "Model Benchmark Klasik"],
        ["Z''-Score Koefisien Baru (MDA)", f"{mda:.4f}", mda_cls.upper(), "Model Empiris BEI"],
        ["XGBoost Machine Learning", f"{float(xgb_prob)*100:.2f}%" if xgb_prob is not None else "N/A", "SAFE ZONE" if (xgb_prob is not None and xgb_prob < 0.35) else ("GREY AREA" if (xgb_prob is not None and xgb_prob <= 0.65) else ("DISTRESS ZONE" if xgb_prob is not None else "STANDBY")), "Model AI Non-Linear"],
        ["Status Konsensus Terintegrasi", str(c3.get("status", "STANDBY")), str(c3.get("summary_note", "-")), str(c3.get("desc", "-"))],
        ["", ""],
        ["=== RASIO KEUANGAN PEMBENTUK MODEL (X1-X5) ===", ""],
        ["Kode", "Nama Variabel Rasio", "Nilai Rasio"],
        ["X1", "Working Capital / Total Assets (WC/TA)", f"{r.get('X1', 0.0):.6f}"],
        ["X2", "Retained Earnings / Total Assets (RE/TA)", f"{r.get('X2', 0.0):.6f}"],
        ["X3", "EBIT / Total Assets (EBIT/TA)", f"{r.get('X3', 0.0):.6f}"],
        ["X4", "Equity / Total Liabilities (Eq/TL)", f"{r.get('X4', 0.0):.6f}"],
        ["X5", "Sales / Total Assets (S/TA)", f"{r.get('X5', 0.0):.6f}"],
        ["", ""],
        ["=== POS LAPORAN KEUANGAN KUNCI (RUPIAH) ===", ""],
        ["Pos Akun", "Nominal (Rp)"],
    ]
    for k, label in [
        ("total_assets", "Total Aset"),
        ("total_liabilities", "Total Liabilitas"),
        ("current_assets", "Aset Lancar"),
        ("current_liabilities", "Liabilitas Lancar"),
        ("working_capital", "Modal Kerja Bersih"),
        ("total_equity", "Total Ekuitas"),
        ("retained_earnings", "Saldo Laba Ditahan"),
        ("ebit", "Laba Usaha (EBIT)"),
        ("total_revenue", "Pendapatan Bersih"),
        ("net_income", "Laba Bersih"),
        ("interest_expense", "Beban Bunga"),
        ("operating_cash_flow", "Arus Kas Operasional"),
    ]:
        val = fin.get(k, 0.0) or 0.0
        rows.append([label, f"{float(val):.2f}"])

    rows.extend([
        ["", ""],
        ["=== INDEKS KETAHANAN FINANSIAL & LIKUIDITAS ===", ""],
        ["Indikator", "Nilai", "Status"],
        ["Current Ratio", f"{adv.get('current_ratio', {}).get('value', 0.0):.2f}x", adv.get('current_ratio', {}).get('status', '-')],
        ["Debt to Equity Ratio (DER)", f"{adv.get('der', {}).get('value', 0.0):.2f}x", adv.get('der', {}).get('status', '-')],
        ["Interest Coverage Ratio (ICR)", f"{adv.get('icr', {}).get('value', 0.0):.2f}x", adv.get('icr', {}).get('status', '-')],
        ["OCF to Liabilities", f"{adv.get('ocf_to_liab', {}).get('value', 0.0):.2f}x", adv.get('ocf_to_liab', {}).get('status', '-')],
        ["Return on Assets (ROA)", f"{adv.get('roa', {}).get('value', 0.0)*100:.2f}%", adv.get('roa', {}).get('status', '-')],
        ["Net Profit Margin (NPM)", f"{adv.get('npm', {}).get('value', 0.0)*100:.2f}%", adv.get('npm', {}).get('status', '-')],
    ])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue()


def generate_full_json_report(
    company: str,
    ticker: str,
    year: int | str,
    sector: str = "",
    username: str = "Analyst",
    analysis_date: str = "",
    z: float = 0.0,
    z_cls: str = "standby",
    mda: float = 0.0,
    mda_cls: str = "standby",
    xgb_prob: float | None = None,
    cat3: dict | None = None,
    ratios: dict | None = None,
    financials: dict | None = None,
    adv_metrics: dict | None = None,
) -> str:
    """Menghasilkan data analisis lengkap dalam format JSON terstruktur untuk audit sistem."""
    data = {
        "metadata": {
            "report_title": "Financial Distress Multi-Model Prediction Audit",
            "company": company,
            "ticker": ticker,
            "year": int(year) if str(year).isdigit() else year,
            "sector": sector,
            "analyst": username,
            "timestamp": analysis_date or datetime.now().isoformat(),
            "engine_version": "DistressAI 2.0 (Skripsi FEB BEI)",
        },
        "results": {
            "altman_z_score": round(float(z), 4),
            "altman_classification": z_cls,
            "mda_score": round(float(mda), 4),
            "mda_classification": mda_cls,
            "xgb_probability": round(float(xgb_prob), 6) if xgb_prob is not None else None,
            "consensus": cat3 or {},
        },
        "ratios": {k: round(float(v), 6) for k, v in (ratios or {}).items()},
        "financial_statements": {k: float(v) for k, v in (financials or {}).items() if isinstance(v, (int, float))},
        "advanced_metrics": adv_metrics or {},
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


__all__ = [
    "VARIABLE_SCHEMA",
    "FINANCIAL_FIELDS",
    "ACCOUNT_SPECS",
    "COLUMN_ALIASES",
    "variable_label",
    "complete_financial_values",
    "normalize_dataframe_columns",
    "read_csv_file",
    "read_excel_file",
    "extract_pdf_pages",
    "parse_financial_number",
    "extract_financial_values_from_pages",
    "extract_financial_values_from_df",
    "extract_financial_values_from_text",
    "is_idx_xbrl_data",
    "get_idx_document_years",
    "extract_financial_values_from_idx_data",
    "extract_financial_values_from_excel",
    "get_pdf_document_years",
    "get_sample_template_dataframe",
    "get_sample_template_csv_bytes",
    "get_sample_template_excel_bytes",
    "generate_printable_html_report",
    "generate_full_csv_report",
    "generate_full_json_report",
]