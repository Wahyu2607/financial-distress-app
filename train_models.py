from __future__ import annotations

import json
from pathlib import Path
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np
import pandas as pd
from src.calculations import label_dataset_3categories, train_xgboost_classifier

# 1. Baca data keuangan dari Excel
candidate_data = Path('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.xlsx')
file_path = str(candidate_data) if candidate_data.exists() else ('data/fiks data calculate.xlsx' if Path('data/fiks data calculate.xlsx').exists() else 'data/datakeuangan.xlsx')
print(f"Menggunakan dataset utama panel tahunan: {file_path}")
if "fiks data calculate" in file_path:
    df = pd.read_excel(file_path, sheet_name='perhitungan').iloc[:702]
else:
    df = pd.read_excel(file_path)

print(f"Total Baris Data Latih: {len(df)}, Jumlah Emiten: {df['Kode Saham'].nunique() if 'Kode Saham' in df.columns else 'N/A'}")

# 2. Koefisien MDA Empiris (Z'' Koefisien Baru) sesuai rumus Fisher (PDF Lampiran 2 hal. 110-111)
mda_coefficients = {"X1": 6.1120, "X2": 3.2776, "X3": 4.8373, "X4": 0.0430}
mda_cutoff = 0.3844

# 3. Simpan konfigurasi ke config.json dengan 3 Kategori Operasional
if Path('config.json').exists():
    with open('config.json', 'r', encoding='utf-8') as f:
        try:
            config_data = json.load(f)
        except Exception:
            config_data = {}
else:
    config_data = {}

config_data.setdefault("altman_coefficients", {"X1": 6.56, "X2": 3.26, "X3": 6.72, "X4": 1.05})
config_data.setdefault("altman_thresholds", {
    "distress": 1.81,
    "grey": 2.99,
    "distress_alt": 1.10,
    "grey_alt": 2.60,
    "selected_standard": "bab3_standard"
})
config_data["mda_coefficients"] = mda_coefficients
config_data["mda_threshold"] = mda_cutoff
config_data["mda_thresholds"] = {
    "distress": 0.0,
    "grey": 1.0,
    "cutoff": mda_cutoff
}
config_data.setdefault("xgb_threshold", 0.5)
config_data.setdefault("xgb_thresholds", {
    "safe": 0.35,
    "distress": 0.65,
    "cutoff": 0.5
})
config_data.setdefault("system_announcement", "")
config_data.setdefault("allow_user_analysis", True)
config_data.setdefault("registration_passcode", "DISTRESS2026")

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config_data, f, indent=2)
print("File config.json berhasil disinkronkan.")

# 4. Latih dan Evaluasi Model (Pengujian 1 dan Pengujian 2) untuk Baseline 80/20
Path('models').mkdir(parents=True, exist_ok=True)
print("\n" + "="*70)
print("MEMULAI PELATIHAN DUA PENGUJIAN XGBOOST (P1 & P2) - BASELINE 80/20")
print("="*70)
eval_res = train_xgboost_classifier(
    df,
    output_path='models/xgb_model.json',
    test_size=0.2,
    random_state=42,
    n_estimators=100,
    max_depth=3,
    learning_rate=0.08,
    target_method='predictive_t1',
)

print(f"\n[HASIL EVALUASI BASELINE 80/20]")
p1 = eval_res.get('pengujian_1', {})
p2 = eval_res.get('pengujian_2', {})
print(f"Pengujian 1 (4 Rasio Altman) : Akurasi={p1.get('accuracy', 0)*100:.2f}%, AUC={p1.get('roc_auc', 0):.4f}, PR-AUC={p1.get('pr_auc', 0):.4f}, F1={p1.get('f1_score', 0):.4f}")
print(f"Pengujian 2 (16 Fitur Lengkap): Akurasi={p2.get('accuracy', 0)*100:.2f}%, AUC={p2.get('roc_auc', 0):.4f}, PR-AUC={p2.get('pr_auc', 0):.4f}, F1={p2.get('f1_score', 0):.4f}")

# 5. Pre-compute Cache Evaluasi untuk Variasi Split Lainnya (10%, 30%, 40%, 50%, 70%)
print("\n" + "="*70)
print("MEMPERBARUI CACHE EVALUASI UNTUK VARIASI DATA SPLIT (10% s.d. 70%)")
print("="*70)
split_tests = [0.10, 0.30, 0.40, 0.50, 0.70]
for sp in split_tests:
    sp_pct = int(round(sp * 100))
    train_xgboost_classifier(
        df,
        output_path='models/xgb_model.json',
        test_size=sp,
        random_state=42,
        n_estimators=100,
        max_depth=3,
        learning_rate=0.08,
        target_method='predictive_t1',
    )
    print(f"  ✓ Cache split {100-sp_pct}/{sp_pct} (xgb_evaluation_{sp_pct}.json) berhasil diperbarui.")

print("\nSeluruh model dan berkas evaluasi multi-model berhasil dibuat dan diverifikasi!")
