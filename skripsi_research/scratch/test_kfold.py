import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix
from xgboost import XGBClassifier
from src.calculations import build_features_p1, build_features_p2, build_distress_target

df = pd.read_csv('data/dataset_manufaktur_tahunan_15_variabel_2014_2026.csv')
y, desc = build_distress_target(df, method='predictive_t1')
X_p1 = build_features_p1(df)
X_p2 = build_features_p2(df)

skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)

records = []

for fold, (train_idx, test_idx) in enumerate(skf.split(X_p2, y), 1):
    print(f"\n--- FOLD {fold} ---")
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    # Scale pos weight for XGBoost
    scale_pos = (y_train == 0).sum() / max(1, (y_train == 1).sum())
    
    # 1. XGBoost P1
    X_tr_p1, X_te_p1 = X_p1.iloc[train_idx], X_p1.iloc[test_idx]
    xgb_p1 = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, scale_pos_weight=scale_pos, eval_metric='logloss', random_state=42)
    xgb_p1.fit(X_tr_p1, y_train)
    
    # Train eval
    p_tr = xgb_p1.predict(X_tr_p1)
    pr_tr = xgb_p1.predict_proba(X_tr_p1)[:, 1]
    # Test eval
    p_te = xgb_p1.predict(X_te_p1)
    pr_te = xgb_p1.predict_proba(X_te_p1)[:, 1]
    
    records.append({
        'Fold': fold, 'Model': 'XGBoost P1 (4 Rasio)',
        'Train Acc': accuracy_score(y_train, p_tr), 'Test Acc': accuracy_score(y_test, p_te),
        'Train F1': f1_score(y_train, p_tr), 'Test F1': f1_score(y_test, p_te),
        'Train AUC': roc_auc_score(y_train, pr_tr), 'Test AUC': roc_auc_score(y_test, pr_te),
        'Test Recall': recall_score(y_test, p_te), 'Test Precision': precision_score(y_test, p_te)
    })
    
    # 2. XGBoost P2
    X_tr_p2, X_te_p2 = X_p2.iloc[train_idx], X_p2.iloc[test_idx]
    xgb_p2 = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.08, scale_pos_weight=scale_pos, eval_metric='logloss', random_state=42)
    xgb_p2.fit(X_tr_p2, y_train)
    
    p_tr2 = xgb_p2.predict(X_tr_p2)
    pr_tr2 = xgb_p2.predict_proba(X_tr_p2)[:, 1]
    p_te2 = xgb_p2.predict(X_te_p2)
    pr_te2 = xgb_p2.predict_proba(X_te_p2)[:, 1]
    
    records.append({
        'Fold': fold, 'Model': 'XGBoost P2 (16 Fitur)',
        'Train Acc': accuracy_score(y_train, p_tr2), 'Test Acc': accuracy_score(y_test, p_te2),
        'Train F1': f1_score(y_train, p_tr2), 'Test F1': f1_score(y_test, p_te2),
        'Train AUC': roc_auc_score(y_train, pr_tr2), 'Test AUC': roc_auc_score(y_test, pr_te2),
        'Test Recall': recall_score(y_test, p_te2), 'Test Precision': precision_score(y_test, p_te2)
    })

res_df = pd.DataFrame(records)
print(res_df.to_string())
print("\nRata-rata per Model:")
print(res_df.groupby('Model')[['Train Acc', 'Test Acc', 'Train F1', 'Test F1', 'Train AUC', 'Test AUC']].mean())
