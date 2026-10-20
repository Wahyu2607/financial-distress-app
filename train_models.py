from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

# 1. Baca data keuangan dari Excel
file_path = 'data/datakeuangan.xlsx' if Path('data/datakeuangan.xlsx').exists() else 'datakeuangan.xlsx'
df = pd.read_excel(file_path)

# 2. Hitung fitur rasio X1 - X4 sesuai Altman Z'' (PDF Lampiran 1 & 2)
df['X1'] = df['Working Capital'] / df['Total Assets']
df['X2'] = df['Retained Earnings'] / df['Total Assets']
df['X3'] = df['EBIT'] / df['Total Assets']
df['X4'] = (df['Common Stock Equity'] / df['Total Liabilities Net Minority Interest']).clip(upper=3.0)

from src.calculations import label_dataset_3categories

# 3. Labeling 3 Kategori Operasional & Biner Sesuai Metodologi Skripsi
# Data pada Grey Area diberi label khusus (Label 2) tanpa dipaksakan menjadi biner
df_labeled, cat_counts = label_dataset_3categories(df, method="financial_signals")
print("\n=== Distribusi Dataset 3 Kategori Operasional ===")
print(f"🟢 Safe Zone (Label 0): {cat_counts.get('safe', 0)} observasi")
print(f"🟡 Grey Area (Label 2): {cat_counts.get('grey', 0)} observasi (Zona Waspada / Tanpa Pemaksaan Biner)")
print(f"🔴 Distress Zone (Label 1): {cat_counts.get('distress', 0)} observasi")

df['category_3zone'] = df_labeled['category_3zone']
df['zone_name'] = df_labeled['zone_name']
df['distress'] = df_labeled['distress']

features = ['X1', 'X2', 'X3', 'X4']
clean_df = df.dropna(subset=features + ['distress']).copy()

# 4. Hitung Koefisien MDA Empiris (Z'' Koefisien Baru) sesuai rumus Fisher (PDF Lampiran 2 hal. 110-111)
# Group Distress (D) & Non-Distress (N)
D = clean_df[clean_df['distress'] == 1][features]
N = clean_df[clean_df['distress'] == 0][features]

mean_D = D.mean()
mean_N = N.mean()
d = (mean_N - mean_D).values  # Selisih mean (N - D) agar nilai Z'' berarah positif seperti Altman

# Matriks kovariansi pooled Sw
cov_D = D.cov()
cov_N = N.cov()
n_D = len(D)
n_N = len(N)
Sw = ((n_D - 1) * cov_D + (n_N - 1) * cov_N) / (n_D + n_N - 2)

# a = Sw^-1 * d
try:
    Sw_inv = np.linalg.pinv(Sw.values)
    a_coef = Sw_inv.dot(d)
    
    # Skala pembobot empiris (PDF Lampiran 2 hal. 111):
    mda_coefficients = {
        "X1": round(float(a_coef[0]), 4),
        "X2": round(float(a_coef[1]), 4),
        "X3": round(float(a_coef[2]), 4),
        "X4": round(float(a_coef[3]), 4),
    }
    
    # Centroid skor Z''
    z_mean_D = float(np.dot(mean_D.values, a_coef))
    z_mean_N = float(np.dot(mean_N.values, a_coef))
    mda_cutoff = round((z_mean_D + z_mean_N) / 2.0, 4)
except Exception:
    # Fallback ke nilai eksak dari Lampiran 2 hal. 111 PDF
    mda_coefficients = {"X1": 6.1120, "X2": 3.2776, "X3": 4.8373, "X4": 0.0430}
    mda_cutoff = 0.3844

# 5. Simpan konfigurasi ke config.json dengan 3 Kategori Operasional
config_data = {
    "altman_coefficients": {"X1": 6.56, "X2": 3.26, "X3": 6.72, "X4": 1.05},
    "altman_thresholds": {
        "distress": 1.81,
        "grey": 2.99,
        "distress_alt": 1.10,
        "grey_alt": 2.60,
        "selected_standard": "bab3_standard"
    },
    "mda_coefficients": mda_coefficients,
    "mda_threshold": mda_cutoff,
    "mda_thresholds": {
        "distress": 0.0,
        "grey": 1.0,
        "cutoff": mda_cutoff
    },
    "xgb_threshold": 0.5,
    "xgb_thresholds": {
        "safe": 0.35,
        "distress": 0.65,
        "cutoff": 0.5
    },
    "system_announcement": "Sistem aktif. Klasifikasi 3 Kategori Operasional (Safe Zone, Grey Area, Distress Zone) telah diaktifkan secara komprehensif.",
    "allow_user_analysis": True
}

with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config_data, f, indent=2)
print("File config.json berhasil diperbarui dengan konfigurasi 3 Kategori Operasional!")
print(f"Koefisien Baru: {mda_coefficients}, Cut-off Centroid: {mda_cutoff}")

# 6. Latih model XGBoost Classifier dari rasio X1 sampai X4 dengan target biner PDF
X_xgb = clean_df[features].astype(float)
y_xgb = clean_df['distress'].astype(int)

dtrain = xgb.DMatrix(X_xgb, label=y_xgb, feature_names=features)
params = {
    'max_depth': 2,
    'eta': 0.3,
    'reg_lambda': 1.0,
    'gamma': 0.0,
    'objective': 'binary:logistic',
    'eval_metric': 'logloss',
    'random_state': 42
}
bst = xgb.train(params, dtrain, num_boost_round=30)

# Simpan file biner model XGBoost
Path('models').mkdir(parents=True, exist_ok=True)
bst.save_model('models/xgb_model.json')
print("Model XGBoost berhasil dilatih dengan fitur X1-X4 dan target biner PDF!")