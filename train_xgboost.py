from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Fitur rasio keuangan Altman Z''-Score yang digunakan oleh XGBoost
FEATURES = ["X1", "X2", "X3", "X4"]


def prepare_training_dataframe(df: pd.DataFrame, target_col: str | None = None) -> tuple[pd.DataFrame, pd.Series]:
    """
    Menyiapkan fitur X1-X4 dan target biner (1: distress, 0: non-distress).
    Mendukung input berupa tabel rasio langsung maupun laporan keuangan mentah.
    """
    df = df.copy()

    # Normalisasi nama kolom jika perlu
    col_map = {c.strip(): c for c in df.columns}

    # Jika rasio X1 - X4 belum ada, hitung dari akun keuangan mentah
    has_ratios = all(f in df.columns for f in FEATURES)
    if not has_ratios:
        # Cek kolom akun mentah alternatif
        wc = df["Working Capital"] if "Working Capital" in df else (df["Current Assets"] - df["Current Liabilities"] if ("Current Assets" in df and "Current Liabilities" in df) else None)
        ta = df.get("Total Assets")
        re_val = df.get("Retained Earnings")
        ebit = df.get("EBIT")
        eq = df.get("Common Stock Equity")
        tl = df["Total Liabilities Net Minority Interest"] if "Total Liabilities Net Minority Interest" in df else df.get("Total Liabilities")

        if ta is not None and tl is not None:
            df["X1"] = wc / ta
            df["X2"] = re_val / ta
            df["X3"] = ebit / ta
            df["X4"] = (eq / tl).clip(upper=3.0)
        else:
            missing_features = [f for f in FEATURES if f not in df.columns]
            raise ValueError(
                f"Dataset harus memiliki kolom rasio {missing_features} atau kolom akun laporan keuangan "
                "(Working Capital, Total Assets, Retained Earnings, EBIT, Common Stock Equity, Total Liabilities)."
            )

    # Batasi X4 <= 3.0 sesuai teori skripsi hal. 41 & 95
    if "X4" in df.columns:
        df["X4"] = df["X4"].clip(upper=3.0)

    # Menentukan kolom target klasifikasi (1: distress, 0: non-distress)
    actual_target = None
    if target_col and target_col in df.columns:
        actual_target = target_col
    elif "label" in df.columns:
        actual_target = "label"
    elif "distress" in df.columns:
        actual_target = "distress"
    elif "Retained Earnings" in df.columns and "EBIT" in df.columns:
        df["distress"] = ((df["Retained Earnings"] < 0) & (df["EBIT"] < 0)).astype(int)
        actual_target = "distress"
    elif "Net Income" in df.columns and "Retained Earnings" in df.columns:
        df["distress"] = ((df["Retained Earnings"] < 0) & (df["Net Income"] < 0)).astype(int)
        actual_target = "distress"
    else:
        raise ValueError(
            "Kolom target klasifikasi tidak ditemukan. Sediakan kolom 'label' atau 'distress' "
            "dengan nilai biner (1 = distress, 0 = non-distress)."
        )

    # Bersihkan NaN
    clean_df = df.dropna(subset=FEATURES + [actual_target]).copy()
    X = clean_df[FEATURES].astype(float)
    y = clean_df[actual_target].astype(int)

    if y.nunique() < 2:
        raise ValueError(f"Kolom target '{actual_target}' harus memiliki minimal dua kelas: 0 (non-distress) dan 1 (distress).")

    try:
        from src.calculations import label_dataset_3categories
        _, cat_counts = label_dataset_3categories(clean_df, method="financial_signals")
        print("\n=== Audit Pra-Pelatihan: Distribusi 3 Kategori Operasional ===")
        print(f"🟢 Safe Zone (Label 0): {cat_counts.get('safe', 0)} observasi")
        print(f"🟡 Grey Area (Label 2): {cat_counts.get('grey', 0)} observasi (Zona Waspada / Tanpa Pemaksaan Biner)")
        print(f"🔴 Distress Zone (Label 1): {cat_counts.get('distress', 0)} observasi")
    except Exception:
        pass

    return X, y


def train_model(
    df: pd.DataFrame,
    target_col: str | None = None,
    output_path: str = "models/xgb_model.json",
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: int = 3,
    learning_rate: float = 0.08,
):
    X, y = prepare_training_dataframe(df, target_col=target_col)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=random_state,
    )
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]

    cr = classification_report(y_test, pred, digits=4, output_dict=True)
    cm = confusion_matrix(y_test, pred)
    auc = float(roc_auc_score(y_test, prob))
    feat_imp = dict(zip(FEATURES, [float(v) for v in model.feature_importances_]))

    print("\n=== Classification Report ===")
    print(classification_report(y_test, pred, digits=4))
    print("=== Confusion Matrix ===")
    print(cm)
    print(f"ROC AUC: {auc:.4f}")
    print(f"Feature Importances: {feat_imp}")

    # Evaluasi Distribusi 3 Kategori Operasional pada Data Uji
    cat3_preds = []
    for p_val in prob:
        if p_val > 0.65:
            cat3_preds.append("Distress Zone (🔴 P > 0.65)")
        elif p_val >= 0.35:
            cat3_preds.append("Grey Area (🟡 0.35 <= P <= 0.65)")
        else:
            cat3_preds.append("Safe Zone (🟢 P < 0.35)")
    
    cat3_dist = pd.Series(cat3_preds).value_counts().to_dict()
    print("\n=== Distribusi Prediksi 3 Kategori Operasional (Data Uji) ===")
    for k, v in cat3_dist.items():
        print(f"- {k}: {v} emiten ({v/len(cat3_preds)*100:.1f}%)")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(output))
    print(f"\nModel XGBoost berhasil disimpan ke: {output}")

    return {
        "model": model,
        "classification_report": cr,
        "confusion_matrix": cm.tolist(),
        "roc_auc": auc,
        "feature_importances": feat_imp,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }


def main():
    parser = argparse.ArgumentParser(description="Train XGBoost Financial Distress Model using X1-X4 ratios")
    parser.add_argument("--file", "--csv", required=True, help="Path ke file dataset (CSV / Excel)")
    parser.add_argument("--target", default=None, help="Nama kolom target (default: label / distress)")
    parser.add_argument("--output", default="models/xgb_model.json", help="Path penyimpanan model JSON")
    args = parser.parse_args()

    file_p = Path(args.file)
    if not file_p.exists():
        raise FileNotFoundError(f"File dataset tidak ditemukan: {file_p}")

    if file_p.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(file_p)
    else:
        df = pd.read_csv(file_p)

    train_model(df, target_col=args.target, output_path=args.output)


if __name__ == "__main__":
    main()
