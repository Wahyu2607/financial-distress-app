import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve, auc
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from src.calculations import build_features_p1, build_features_p2, build_distress_target

os.makedirs('scratch/test_plots', exist_ok=True)

df = pd.read_csv('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.csv')
y, desc = build_distress_target(df, method='predictive_t1')
X_p1 = build_features_p1(df)
X_p2 = build_features_p2(df)

# EDA Plot
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
# Target dist
counts = y.value_counts()
axes[0].pie(counts, labels=['Non-Distress (Sehat)', 'Distress (Bermasalah)'], autopct='%1.1f%%',
            startangle=140, colors=['#2b5c8f', '#d9534f'], explode=(0, 0.1), shadow=True,
            textprops={'fontsize': 11, 'weight': 'bold'})
axes[0].set_title('Distribusi Status Keuangan Emiten BEI (2014-2026)\n(Total: 3.770 Observasi Tahunan)', fontsize=12, fontweight='bold', pad=12)

# Correlation heatmap of X1-X4
corr = X_p1.corr()
im = axes[1].imshow(corr, cmap='Blues', vmin=-1.0, vmax=1.0)
cbar = plt.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04)
cbar.ax.tick_params(labelsize=10)
axes[1].set_xticks(range(len(corr.columns)))
axes[1].set_yticks(range(len(corr.columns)))
axes[1].set_xticklabels(corr.columns, fontsize=11, fontweight='bold')
axes[1].set_yticklabels(corr.columns, fontsize=11, fontweight='bold')
for i in range(len(corr)):
    for j in range(len(corr)):
        val = corr.iloc[i, j]
        color = 'white' if abs(val) > 0.5 else 'black'
        axes[1].text(j, i, f"{val:.3f}", ha='center', va='center', color=color, fontsize=11, fontweight='bold')
axes[1].set_title('Matriks Korelasi Pearson Antar-Variabel Altman (X1-X4)', fontsize=12, fontweight='bold', pad=12)
plt.tight_layout()
plt.savefig('scratch/test_plots/plot1_eda.png', dpi=120)
plt.close()
print("Plot 1 generated successfully.")
