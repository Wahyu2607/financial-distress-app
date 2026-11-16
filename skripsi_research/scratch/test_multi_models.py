import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from src.calculations import build_features_p1, build_features_p2, build_distress_target

df = pd.read_csv('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.csv')
y, desc = build_distress_target(df, method='predictive_t1')
X_p1 = build_features_p1(df)
X_p2 = build_features_p2(df)

skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
records = []

for fold, (tr_idx, te_idx) in enumerate(skf.split(X_p2, y), 1):
    y_tr, y_te = y.iloc[tr_idx], y.iloc[te_idx]
    scale_pos = (y_tr == 0).sum() / max(1, (y_tr == 1).sum())
    
    # 1. Altman Z''
    X_te_p1 = X_p1.iloc[te_idx]
    X_tr_p1 = X_p1.iloc[tr_idx]
    
    z_te_alt = 6.56 * X_te_p1['X1'] + 3.26 * X_te_p1['X2'] + 6.72 * X_te_p1['X3'] + 1.05 * X_te_p1['X4']
    p_te_alt = (z_te_alt <= 1.10).astype(int)
    prob_te_alt = 1.0 / (1.0 + np.exp(np.clip(z_te_alt - 1.10, -15.0, 15.0)))
    
    z_tr_alt = 6.56 * X_tr_p1['X1'] + 3.26 * X_tr_p1['X2'] + 6.72 * X_tr_p1['X3'] + 1.05 * X_tr_p1['X4']
    p_tr_alt = (z_tr_alt <= 1.10).astype(int)
    prob_tr_alt = 1.0 / (1.0 + np.exp(np.clip(z_tr_alt - 1.10, -15.0, 15.0)))
    
    records.append({
        'Fold': fold, 'Model': 'Altman Z" (1995)',
        'Train Acc': accuracy_score(y_tr, p_tr_alt), 'Test Acc': accuracy_score(y_te, p_te_alt),
        'Train F1': f1_score(y_tr, p_tr_alt), 'Test F1': f1_score(y_te, p_te_alt),
        'Train AUC': roc_auc_score(y_tr, prob_tr_alt), 'Test AUC': roc_auc_score(y_te, prob_te_alt)
    })
    
    # 2. MDA Fisher
    z_te_mda = 6.1120 * X_te_p1['X1'] + 3.2776 * X_te_p1['X2'] + 4.8373 * X_te_p1['X3'] + 0.0430 * X_te_p1['X4']
    p_te_mda = (z_te_mda < 0.3844).astype(int)
    prob_te_mda = 1.0 / (1.0 + np.exp(np.clip(z_te_mda - 0.3844, -15.0, 15.0)))
    
    z_tr_mda = 6.1120 * X_tr_p1['X1'] + 3.2776 * X_tr_p1['X2'] + 4.8373 * X_tr_p1['X3'] + 0.0430 * X_tr_p1['X4']
    p_tr_mda = (z_tr_mda < 0.3844).astype(int)
    prob_tr_mda = 1.0 / (1.0 + np.exp(np.clip(z_tr_mda - 0.3844, -15.0, 15.0)))
    
    records.append({
        'Fold': fold, 'Model': 'MDA Fisher BEI',
        'Train Acc': accuracy_score(y_tr, p_tr_mda), 'Test Acc': accuracy_score(y_te, p_te_mda),
        'Train F1': f1_score(y_tr, p_tr_mda), 'Test F1': f1_score(y_te, p_te_mda),
        'Train AUC': roc_auc_score(y_tr, prob_tr_mda), 'Test AUC': roc_auc_score(y_te, prob_te_mda)
    })
    
    # 3. Logistic Regression
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_tr_p1, y_tr)
    p_tr_lr = lr.predict(X_tr_p1)
    pr_tr_lr = lr.predict_proba(X_tr_p1)[:, 1]
    p_te_lr = lr.predict(X_te_p1)
    pr_te_lr = lr.predict_proba(X_te_p1)[:, 1]
    records.append({
        'Fold': fold, 'Model': 'Logistic Regression',
        'Train Acc': accuracy_score(y_tr, p_tr_lr), 'Test Acc': accuracy_score(y_te, p_te_lr),
        'Train F1': f1_score(y_tr, p_tr_lr), 'Test F1': f1_score(y_te, p_te_lr),
        'Train AUC': roc_auc_score(y_tr, pr_tr_lr), 'Test AUC': roc_auc_score(y_te, pr_te_lr)
    })
    
    # 4. Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight='balanced', random_state=42)
    rf.fit(X_tr_p1, y_tr)
    p_tr_rf = rf.predict(X_tr_p1)
    pr_tr_rf = rf.predict_proba(X_tr_p1)[:, 1]
    p_te_rf = rf.predict(X_te_p1)
    pr_te_rf = rf.predict_proba(X_te_p1)[:, 1]
    records.append({
        'Fold': fold, 'Model': 'Random Forest',
        'Train Acc': accuracy_score(y_tr, p_tr_rf), 'Test Acc': accuracy_score(y_te, p_te_rf),
        'Train F1': f1_score(y_tr, p_tr_rf), 'Test F1': f1_score(y_te, p_te_rf),
        'Train AUC': roc_auc_score(y_tr, pr_tr_rf), 'Test AUC': roc_auc_score(y_te, pr_te_rf)
    })
    
    # 5. XGBoost P1
    xgb1 = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, scale_pos_weight=scale_pos, eval_metric='logloss', random_state=42)
    xgb1.fit(X_tr_p1, y_tr)
    records.append({
        'Fold': fold, 'Model': 'XGBoost P1 (4 Rasio)',
        'Train Acc': accuracy_score(y_tr, xgb1.predict(X_tr_p1)), 'Test Acc': accuracy_score(y_te, xgb1.predict(X_te_p1)),
        'Train F1': f1_score(y_tr, xgb1.predict(X_tr_p1)), 'Test F1': f1_score(y_te, xgb1.predict(X_te_p1)),
        'Train AUC': roc_auc_score(y_tr, xgb1.predict_proba(X_tr_p1)[:, 1]), 'Test AUC': roc_auc_score(y_te, xgb1.predict_proba(X_te_p1)[:, 1])
    })

res = pd.DataFrame(records)
print("=== Rata-rata Kinerj 3-Fold CV ===")
print(res.groupby('Model')[['Train Acc', 'Test Acc', 'Train F1', 'Test F1', 'Train AUC', 'Test AUC']].mean().round(4))
