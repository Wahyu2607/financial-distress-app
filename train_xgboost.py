from __future__ import annotations

import argparse
from pathlib import Path
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
from src.calculations import (
    build_features_p1,
    build_features_p2,
    build_distress_target,
    train_xgboost_classifier,
)

FEATURES_P1 = ["X1", "X2", "X3", "X4"]
FEATURES_P2 = FEATURES_P1 + [
    "Current_Ratio", "DAR", "DER", "ROA", "ICR",
    "CFO_to_TL", "CFO_to_CL", "Revenue_to_Assets",
    "Revenue_Growth", "Net_Income_Growth", "Total_Assets_Growth", "OCF_Growth",
]


def print_evaluation_summary(eval_res: dict):
    """
    Menampilkan ringkasan komparasi evaluasi dua pengujian XGBoost dan model statistik (Altman & MDA).
    """
    p1 = eval_res.get("pengujian_1", {})
    p2 = eval_res.get("pengujian_2", {})
    alt = eval_res.get("models_evaluation", {}).get("altman", {})
    mda = eval_res.get("models_evaluation", {}).get("mda", {})
    split = eval_res.get("split_info", {})

    print("\n" + "=" * 80)
    print("HASIL EVALUASI KOMPARATIF MULTI-MODEL PADA DATA TESTING INDEPENDEN (HOLD-OUT)")
    print("=" * 80)
    print(f"Total Sampel Data : {eval_res.get('total_samples', 0)}")
    print(f"Data Training     : {split.get('train_samples', 0)} ({split.get('train_pct', 0)}%)")
    print(f"Data Validation   : {split.get('val_samples', 0)}")
    print(f"Data Testing      : {split.get('test_samples', 0)} ({split.get('test_pct', 0)}%)")
    print("-" * 80)
    print(f"{'Metrik Evaluasi':<25} | {'XGBoost P1 (4 Rasio)':<18} | {'XGBoost P2 (16 Fitur)':<18} | {'Altman Z\" (1995)':<18} | {'MDA Fisher BEI':<15}")
    print("-" * 80)

    metrics = [
        ("Akurasi (Accuracy)", f"{p1.get('accuracy', 0)*100:.2f}%", f"{p2.get('accuracy', 0)*100:.2f}%", f"{alt.get('accuracy', 0)*100:.2f}%", f"{mda.get('accuracy', 0)*100:.2f}%"),
        ("ROC-AUC", f"{p1.get('roc_auc', 0):.4f}", f"{p2.get('roc_auc', 0):.4f}", f"{alt.get('roc_auc', 0):.4f}", f"{mda.get('roc_auc', 0):.4f}"),
        ("PR-AUC", f"{p1.get('pr_auc', 0):.4f}", f"{p2.get('pr_auc', 0):.4f}", f"{alt.get('pr_auc', 0):.4f}", f"{mda.get('pr_auc', 0):.4f}"),
        ("Presisi (Precision)", f"{p1.get('precision', 0)*100:.2f}%", f"{p2.get('precision', 0)*100:.2f}%", f"{alt.get('precision', 0)*100:.2f}%", f"{mda.get('precision', 0)*100:.2f}%"),
        ("Recall / Sensitivitas", f"{p1.get('recall', 0)*100:.2f}%", f"{p2.get('recall', 0)*100:.2f}%", f"{alt.get('recall', 0)*100:.2f}%", f"{mda.get('recall', 0)*100:.2f}%"),
        ("Spesifisitas", f"{p1.get('specificity', 0)*100:.2f}%", f"{p2.get('specificity', 0)*100:.2f}%", f"{alt.get('specificity', 0)*100:.2f}%", f"{mda.get('specificity', 0)*100:.2f}%"),
        ("F1-Score", f"{p1.get('f1_score', 0):.4f}", f"{p2.get('f1_score', 0):.4f}", f"{alt.get('f1_score', 0):.4f}", f"{mda.get('f1_score', 0):.4f}"),
        ("Youden's J Index", f"{p1.get('youden_j', 0):.4f}", f"{p2.get('youden_j', 0):.4f}", f"{alt.get('youden_j', 0):.4f}", f"{mda.get('youden_j', 0):.4f}"),
        ("Type I Error (FP Rate)", f"{p1.get('type1_error', 0)*100:.2f}%", f"{p2.get('type1_error', 0)*100:.2f}%", f"{alt.get('type1_error', 0)*100:.2f}%", f"{mda.get('type1_error', 0)*100:.2f}%"),
        ("Type II Error (FN Rate)", f"{p1.get('type2_error', 0)*100:.2f}%", f"{p2.get('type2_error', 0)*100:.2f}%", f"{alt.get('type2_error', 0)*100:.2f}%", f"{mda.get('type2_error', 0)*100:.2f}%"),
    ]

    for label, v_p1, v_p2, v_alt, v_mda in metrics:
        print(f"{label:<25} | {v_p1:<18} | {v_p2:<18} | {v_alt:<18} | {v_mda:<15}")

    print("-" * 80)
    cm_p1 = p1.get("cm_details", {})
    cm_p2 = p2.get("cm_details", {})
    print(f"Confusion Matrix P1: TP={cm_p1.get('tp',0)}, TN={cm_p1.get('tn',0)}, FP={cm_p1.get('fp',0)}, FN={cm_p1.get('fn',0)}")
    print(f"Confusion Matrix P2: TP={cm_p2.get('tp',0)}, TN={cm_p2.get('tn',0)}, FP={cm_p2.get('fp',0)}, FN={cm_p2.get('fn',0)}")

    print("\nFeature Importances P1 (Altman 4 Rasio):")
    for feat, imp in p1.get("feature_importances", {}).items():
        print(f"  - {feat:<4}: {imp*100:.2f}%")

    print("\nTop 8 Feature Importances P2 (Altman + 12 Fitur):")
    sorted_p2 = sorted(p2.get("feature_importances", {}).items(), key=lambda x: x[1], reverse=True)[:8]
    for feat, imp in sorted_p2:
        print(f"  - {feat:<20}: {imp*100:.2f}%")


def main():
    parser = argparse.ArgumentParser(description="Pelatihan dan Evaluasi Dua Pengujian XGBoost Financial Distress")
    parser.add_argument("--file", "--csv", default="data/dataset_manufaktur_tahunan_15_variabel_2014_2026.xlsx", help="Path dataset (Excel/CSV)")
    parser.add_argument("--target", default=None, help="Nama kolom target spesifik jika ada")
    parser.add_argument("--target-method", default="predictive_t1", choices=["contemporaneous", "predictive_t1"], help="Metode target: predictive_t1 (Standar Emas) atau contemporaneous")
    parser.add_argument("--output", default="models/xgb_model.json", help="Path output model JSON")
    parser.add_argument("--test-size", type=float, default=0.2, help="Ukuran data testing (default 0.2)")
    parser.add_argument("--n-estimators", type=int, default=100, help="Jumlah decision trees (default 100)")
    parser.add_argument("--max-depth", type=int, default=3, help="Kedalaman maksimum pohon (default 3)")
    parser.add_argument("--learning-rate", type=float, default=0.08, help="Learning rate eta (default 0.08)")
    args = parser.parse_args()

    file_p = Path(args.file)
    if not file_p.exists():
        # Fallback ke dataset alternatif
        alt_p = Path("data/datakeuangan.xlsx")
        if alt_p.exists():
            file_p = alt_p
        else:
            raise FileNotFoundError(f"File dataset tidak ditemukan: {file_p}")

    print(f"Membaca dataset dari: {file_p}")
    if file_p.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(file_p)
    else:
        df = pd.read_csv(file_p)

    eval_result = train_xgboost_classifier(
        df,
        target_col=args.target,
        output_path=args.output,
        test_size=args.test_size,
        random_state=42,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        target_method=args.target_method,
    )

    print_evaluation_summary(eval_result)
    print(f"\nModel berhasil disimpan ke: {args.output}")
    print(f"Model P1 tersimpan ke: {Path(args.output).parent / 'xgb_model_p1.json'}")
    print(f"Model P2 tersimpan ke: {Path(args.output).parent / 'xgb_model_p2.json'}")
    print(f"Metadata evaluasi tersimpan ke: {Path(args.output).parent / 'xgb_evaluation.json'}")


if __name__ == "__main__":
    main()
