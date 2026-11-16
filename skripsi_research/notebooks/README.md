# 📓 Direktori Notebook Analisis & Eksperimen Model

Direktori ini memuat seluruh berkas Jupyter Notebook / Google Colab yang digunakan untuk penelitian, eksplorasi data, pengujian metodologi, dan evaluasi multi-model klasifikasi *financial distress*.

---

## 📋 Daftar Notebook

| Nama Berkas | Lingkungan | Deskripsi |
| :--- | :--- | :--- |
| **`financial_distress_kfold3_colab.ipynb`** | Google Colab / Jupyter | **Notebook Eksperimen Utama (Thesis Final)**:<br>• Validasi silang *Stratified 3-Fold Cross-Validation*.<br>• Komparasi multi-model: Altman $Z''$-Score, MDA Fisher BEI, Logistic Regression, Random Forest, dan XGBoost.<br>• Visualisasi kurva ROC, Precision-Recall, Confusion Matrix, Boxplot stabilitas F1-Score, dan heatmap korelasi.<br>• Serialisasi bobot pohon model ke format JSON (`models/xgb_model.json`). |
| **`financial_distress_bab3_bab4.ipynb`** | Jupyter Lab / Colab | **Notebook Simulasi Metodologi Bab 3 & Bab 4**:<br>• Pengujian fungsi per pos keuangan akuntansi.<br>• Pembatasan rasio (*capping*) $X_4 \le 3.0$.<br>• Perhitungan centroid diskriminan empiris BEI ($0.3844$).<br>• Analisis diagnostik studi kasus emiten (AISA & simulasi). |
| **`financial_distress_model.ipynb`** | Google Colab | **Notebook Model Standar (Baseline)**:<br>• Pipeline awal pengujian model Altman, MDA, dan XGBoost sebelum implementasi Stratified K-Fold. |

---

## 🚀 Panduan Eksekusi di Google Colab
1. Buka [Google Colab](https://colab.research.google.com/).
2. Pilih tab **Upload** dan unggah berkas notebook yang ingin dijalankan (disarankan `financial_distress_kfold3_colab.ipynb`).
3. Unggah dataset laporan keuangan (`dataset_manufaktur_tahunan_15_variabel_2014_2026.xlsx` dari folder `data/`) ketika diminta atau letakkan di direktori kerja Colab.
4. Jalankan sel secara berurutan (*Runtime -> Run all*).
