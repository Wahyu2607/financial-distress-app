# 🎓 Direktori Naskah Skripsi, Riset Akademik, & Eksperimen

Direktori ini menampung seluruh berkas yang berkaitan dengan **penelitian akademik dan penyusunan naskah skripsi** (di luar program aplikasi web Streamlit/FastAPI):

---

## 📁 Struktur Isi Direktori

```
skripsi_research/
├── docs/                      # Dokumen naskah skripsi & instrumen pengujian
│   ├── skripsi/               # Naskah Microsoft Word skripsi (update6) & cadangan
│   └── uat/                   # Transkrip butir kuesioner User Acceptance Test (UAT)
│
├── notebooks/                 # Berkas Jupyter / Google Colab
│   ├── financial_distress_kfold3_colab.ipynb  # Pipeline eksperimen utama (Stratified 3-Fold CV)
│   ├── financial_distress_bab3_bab4.ipynb     # Notebook simulasi metodologi Bab 3 & Bab 4
│   └── financial_distress_model.ipynb         # Notebook Google Colab standar
│
├── reports/                   # Gambar-gambar visualisasi & plot untuk naskah skripsi
│   └── gambar_google_colab/   # Gambar plot evaluasi, confusion matrix, ROC curve, boxplot
│
├── prototypes/                # Prototipe UI antarmuka (HTML & React JSX)
│   ├── SpacerAuth.jsx         # Komponen React mockup autentikasi
│   ├── SpacerAuthSlider.jsx   # Komponen React varian slider
│   ├── spacer_auth.html       # Standalone HTML preview
│   └── spacer_auth_slider.html
│
├── scripts_naskah/            # 23 skrip otomatisasi injeksi teks, tabel, & gambar ke Word Docx
│   ├── align_to_option_3_dataset_3770.py
│   ├── inject_subbab_*.py
│   ├── overhaul_*.py
│   ├── run_overhaul_bab_3.py
│   └── ...
│
└── scratch/                   # Area kerja sementara, dump data, dan analisis respon kuesioner
```

---

## 📌 Catatan
- Seluruh berkas dalam folder ini **tidak dieksekusi langsung** oleh aplikasi utama (`app.py` atau `backend/main.py`).
- Pemisahan ini dilakukan agar struktur repositori program aplikasi menjadi bersih, terstruktur, dan siap untuk deployment maupun pengujian perangkat lunak.
