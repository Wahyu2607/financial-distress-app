# 📉 Financial Distress Decision Support System (DistressAI)
### Sistem Pendukung Keputusan Berbasis Web untuk Memprediksi dan Mengklasifikasikan *Financial Distress* pada Emiten Industri Manufaktur Bursa Efek Indonesia (BEI)

[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg?style=flat&logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://python.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0%2B-EB445A.svg?logo=xgboost)](https://xgboost.readthedocs.io)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4%2B-F7931E.svg?logo=scikit-learn)](https://scikit-learn.org)
[![Status](https://img.shields.io/badge/Status-Thesis%20Ready%20%28100%25%29-10B981.svg)]()

---

## 📌 Ringkasan Proyek

Repositori ini memuat kode sumber lengkap aplikasi **Sistem Pendukung Keputusan (Decision Support System / DSS)** berbasis web yang dikembangkan khusus untuk memprediksi, mengklasifikasikan, dan mendiagnosis kondisi kesulitan keuangan (*financial distress*) pada perusahaan industri manufaktur yang terdaftar di Bursa Efek Indonesia (BEI / IDX).

Sistem menyandingkan tiga pendekatan metodologi finansial secara simultan:
1. **Pendekatan Statistik Klasik**: Formula *Altman Z''-Score (Emerging Market)* 4 variabel.
2. **Pendekatan Statistik Re-estimasi Empiris**: *Multivariate Discriminant Analysis* (MDA) Fisher berkoefisien baru hasil kalibrasi 704 data observasi emiten manufaktur BEI.
3. **Pendekatan Kecerdasan Buatan (Machine Learning)**: Algoritma *Extreme Gradient Boosting* (XGBoost) untuk menangkap pola non-linear dan ketidakseimbangan kelas (*imbalanced data*) pasar modal.

---

## 🚀 Fitur Utama Sistem

| No | Fitur Utama | Deskripsi Implementasi |
| :---: | :--- | :--- |
| **1** | **Input Data Keuangan Multi-Sumber** | Mendukung 5 mode input: Masukan Manual, Integrasi Otomatis API Bursa (Yahoo Finance & IDX), Impor Excel Taksonomi XBRL Resmi BEI (.xlsx), Impor File CSV, dan Ekstraksi Dokumen PDF Laporan Keuangan Tahunan. Tersedia template CSV & Excel siap unduh. |
| **2** | **Prapemrosesan & Normalisasi Data** | Pembersihan data mentah, validasi input, konversi format Rupiah penuh, pengisian pos hilang secara akuntansi (*accounting equation completion*), serta penerapan pembatasan nilai ekstrem (*capping* rasio $X_4 \le 3.0$) sesuai literatur Altman (1995/2017). |
| **3** | **Perhitungan Statistik Konvensional (Altman & MDA)** | Komputasi rasio pembentuk model ($X_1 - X_5$), perhitungan Altman $Z''$-Score (zona aman, *grey area*, dan *distress zone*), serta perhitungan MDA koefisien empiris BEI dengan titik potong centroid objektif $0.3844$. |
| **4** | **Pemodelan Machine Learning (XGBoost)** | Inferensi klasifikasi biner cerdas (Distress vs Non-Distress) berbasis pohon keputusan berbobot (*gradient boosting*), dilengkapi probabilitas sigmoid, log-odds margin, dan penanganan ketidakseimbangan kelas (*scale_pos_weight*). |
| **5** | **Komparasi Kinerja Multi-Model & Kesesuaian** | Penyandingan langsung nilai skor, ambang batas, dan hasil keputusan ketiga model dalam satu antarmuka terpadu, dilengkapi lencana kesesuaian skor (*Model Concordance Badge* sesuai Gambar 3.2), komparasi teoretis Altman Asli 1968 (5 variabel) vs Altman Z'' 1995 (4 variabel), serta kesimpulan konsensus mayoritas. |
| **6** | **Evaluasi Model & Metrik Performa AI** | Kartu ringkasan metrik performa (*Accuracy*, *ROC-AUC*, *Precision*, *Recall*, *F1-Score*, *Specificity*, dan *Youden's J Index* Persamaan 18 Hal. 67), visualisasi *Confusion Matrix* 4 kuadran, kurva interaktif *AUC-ROC*, serta Tabel Benchmark Multi-Model empiris (Lampiran 4 Hal. 141–143). |
| **7** | **Visualisasi Dasbor Interaktif & Intelijen Finansial** | Dasbor interaktif *gauge meter*, Checklist 5 Indikator Peringatan Dini Finansial (*Early Warning Checklist*: `EBIT < 0`, `TIE < 1`, `CFO < 0`, `CE < 0`, `NWC < 0` sesuai Gambar 3.2 & Lampiran 5), dekomposisi faktor penekan (*drivers*), simulator *What-If*, kalkulator *break-even point*, dan memo eksekutif. |
| **+** | **Skrining Massal Multi-Emiten (*Batch Screening*)** | Memproses seluruh baris data emiten pada CSV atau Excel secara simultan, menyajikan tabel peringkat risiko pasar, dan menyediakan opsi ekspor rekap ke Excel (.xlsx) dan CSV. |
| **+** | **Pengujian Unit Otomatis (*Unit Tests*)** | Berkas pengujian unit otomatis (`tests/test_calculations.py`) untuk memverifikasi keakuratan matematis seluruh formula termasuk Altman 1968, MDA, XGBoost, Youden's J, dan Warning Factors. |

---

## 🛠️ Panduan Instalasi & Menjalankan Aplikasi

### 1. Prasyarat Sistem
- Python versi **3.10** atau lebih tinggi
- Git (opsional)

### 2. Klon Repositori & Persiapan Direktori
```bash
git clone https://github.com/username/financial_distress_streamlit.git
cd financial_distress_streamlit
```

### 3. Buat dan Aktifkan Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalasi Dependensi
```bash
pip install -r requirements.txt
```

### 5. Jalankan Aplikasi Streamlit
```bash
streamlit run app.py
```
Aplikasi akan otomatis terbuka di browser pada alamat default: `http://localhost:8501`.

### 6. Menjalankan Pengujian Unit Otomatis (*Unit Tests*)
Untuk menguji keakuratan seluruh formula kalkulasi:
```bash
python -m unittest tests/test_calculations.py
```

---

## 🔑 Kredensial Pengguna Sistem (Login Defaults)

Sistem telah dilengkapi modul otentikasi berbasis keamanan industri **PBKDF2-HMAC-SHA256 (100.000 iterasi)** dengan salt kriptografi unik dan basis data dual-mode (SQLite lokal otomatis atau PostgreSQL Cloud).

| Peran (*Role*) | Username | Password | Deskripsi Hak Akses |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin123` | Akses penuh: Panel kontrol parameter global, moderasi riwayat analisis seluruh user, audit data, kalibrasi ulang model XGBoost, dan kebijakan situs. |
| **Financial Analyst** | `user` | `user123` | Akses analisis: Dasbor analisis terintegrasi, penarikan API pasar, skrining massal, komparasi multi-model, simulasi What-If, dan unduh memo eksekutif. |

*Tersedia tombol akses cepat **"1-Click Demo Login"** pada halaman utama untuk kemudahan demonstrasi sidang skripsi.*

---

## 📐 Landasan Teori Matematis & Metodologi

### 1. Rasio Keuangan Pembentuk Model
Model menggunakan 4 rasio keuangan utama ($X_1 - X_4$) ditambah rasio efisiensi $X_5$:
- **$X_1$ (Working Capital / Total Assets)**: Mengukur likuiditas bersih modal kerja terhadap ukuran aset.
- **$X_2$ (Retained Earnings / Total Assets)**: Mengukur profitabilitas kumulatif dan usia operasional emiten.
- **$X_3$ (EBIT / Total Assets)**: Mengukur produktivitas murni aset dalam menghasilkan laba operasi.
- **$X_4$ (Common Stock Equity / Total Liabilities)**: Mengukur daya ungkit solvabilitas keuangan (*financial leverage*).
- **$X_5$ (Total Revenue / Total Assets)**: Mengukur perputaran total aset (*asset turnover*).

### 2. Formula Altman $Z''$-Score (Emerging Market, 1995/2017)
Model diskriminan 4 variabel tanpa $X_5$ untuk menghindari bias perputaran aset industri negara berkembang:
$$Z'' = 6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4$$
- **Zona Bahaya (*Distress Zone*)**: $Z'' \le 1.10$
- **Zona Abu-abu (*Grey Area*)**: $1.10 < Z'' \le 2.60$
- **Zona Aman (*Safe Zone*)**: $Z'' > 2.60$

### 3. Formula Re-estimasi Empiris MDA Fisher BEI
Koefisien hasil estimasi ulang diskriminan linear pada 704 data observasi manufaktur BEI:
$$Z''_{\text{baru}} = 6.1120 X_1 + 3.2776 X_2 + 4.8373 X_3 + 0.0430 X_4$$
- Centroid Distress: $-2.4502$
- Centroid Non-Distress: $+3.2189$
- **Titik Potong Objektif (*Cut-off*)**: **$0.3844$** (Rata-rata kedua centroid). Nilai $\ge 0.3844$ diklasifikasikan **Aman**, nilai $< 0.3844$ diklasifikasikan **Distress**.

### 4. Aturan Pembatasan Nilai Ekstrem (*Capping Rule* $X_4 \le 3.0$)
Berdasarkan literatur Altman (1995/2017) dan pedoman skripsi hal. 41 & 95, nilai rasio $X_4$ dibatasi maksimum $3.0$ agar perusahaan dengan utang sangat kecil tidak memperoleh skor kesehatan yang melambung semu (*overstated safe score*).

### 5. Model Machine Learning XGBoost
- **Fungsi Objektif**: `binary:logistic`
- **Parameter**: `n_estimators=50`, `max_depth=2`, `learning_rate=0.3`, `scale_pos_weight` disesuaikan untuk mengatasi ketidakseimbangan kelas.
- **Kriteria Target Empiris**: Status kebangkrutan biner ($1 = \text{Distress}, 0 = \text{Non-Distress}$) didasarkan pada kondisi $\text{Retained Earnings} < 0$ dan $\text{EBIT} < 0$.

### 6. Statistik Youden's J Index (Persamaan 18 Hal. 67)
Metrik pengukur efektivitas pemisahan diagnostik optimal antara sensitivitas (daya deteksi emiten bangkrut) dan spesifisitas (daya deteksi emiten sehat):
$$J = \text{Sensitivity} + \text{Specificity} - 1 = \text{Recall} + \text{Specificity} - 1$$
Nilai $J = 1.0$ mencerminkan daya klasifikasi sempurna tanpa kesalahan (*zero false positive & false negative*), sebagaimana tercantum pada Lampiran 4 proposal skripsi.

### 7. 5 Faktor Pemicu Tekanan Finansial (Bagan Alir Gambar 3.2 & Lampiran 5)
Sesuai rancangan sistem Bab III Gambar 3.2 (Hal. 88 & 95) dan Lampiran 5 (Hal. 144), sistem mengevaluasi 5 kondisi pemicu alarm dini:
1. **$EBIT < 0$**: Rugi usaha operasional murni sebelum beban bunga dan pajak.
2. **$TIE < 1.0$**: *Times Interest Earned* di bawah 1.0 (laba operasional tidak mampu menutup beban bunga pinjaman).
3. **$CFO < 0$**: Arus kas operasi bersih negatif (*cash burn*).
4. **$CE < 0$**: Ekuitas modal saham biasa defisit (*negative book value of equity*).
5. **$NWC < 0$**: Modal kerja bersih defisit (*Current Assets < Current Liabilities*).

---

## 📂 Struktur Direktori Proyek

```text
financial_distress_streamlit/
├── app.py                      # Berkas aplikasi utama Streamlit (Routing, Page Controller)
├── config.json                 # Konfigurasi parameter model global (koefisien, cut-off)
├── requirements.txt            # Daftar pustaka dan dependensi Python
├── README.md                   # Dokumentasi teknis & akademik sistem
│
├── src/                        # Modul Arsitektur Sistem
│   ├── calculations.py         # Logika komputasi finansial, Altman, MDA, XGBoost, & Batch
│   ├── database.py             # Manajemen SQLite/PostgreSQL & PBKDF2 Password Hashing
│   ├── financial_api.py        # Pipeline integrasi data Yahoo Finance & feed pasar modal
│   ├── io_utils.py             # Parser dokumen XBRL IDX, Excel, CSV, PDF, & Generator Template
│   ├── styles.py               # Injeksi tema visual CSS Dark Glassmorphism FinTech
│   └── ui.py                   # Komponen rendering UI (Gauge, Radar, ROC, Confusion Matrix)
│
├── data/                       # Data Empiris Skripsi
│   └── datakeuangan.xlsx       # Dataset master 704 data observasi emiten manufaktur BEI
│
├── models/                     # Artefak Pemodelan Machine Learning
│   ├── xgb_model.json          # Bobot pohon model XGBoost yang telah dilatih
│   └── xgb_evaluation.json     # Laporan metrik evaluasi model (CM, ROC Curve, Report)
│
└── tests/                      # Pengujian Perangkat Lunak
    └── test_calculations.py    # Unit tests formula matematis & integritas sistem
```

---

## 🎓 Panduan Sidang Skripsi (*Defense Cheat Sheet / FAQ*)

Pertanyaan umum yang kerap diajukan oleh dosen penguji beserta jawaban argumentatif berbasis metodologi:

#### Q1: *Mengapa menggunakan model Altman 4 variabel (Z''-Score 1995) dan bukan model asli 5 variabel (Z-Score 1968)?*
> **Jawaban:** Model Altman asli 5 variabel menyertakan rasio $X_5$ (*Sales / Total Assets*). Dalam riset lanjutan Edward I. Altman (1995/2017), variabel $X_5$ terbukti sangat bias terhadap jenis industri (industri padat modal memiliki perputaran aset yang secara alamiah lebih lambat dibanding industri barang konsumsi) dan rentan terhadap fluktuasi pasar berkembang (*emerging market*). Altman mereformulasi model menjadi $Z''$-Score 4 variabel agar dapat diterapkan secara adil dan objektif pada emiten di bursa negara berkembang seperti Indonesia.

#### Q2: *Mengapa rasio $X_4$ perlu dibatasi maksimum 3.0 (Capping)?*
> **Jawaban:** Rasio $X_4$ membagi Ekuitas dengan Liabilitas. Jika suatu emiten memiliki liabilitas yang sangat minim, nilai pecahan tersebut dapat melonjak ekstrem (misalnya $X_4 = 15.0$ atau $25.0$). Tanpa pembatasan, skor $Z''$ emiten tersebut akan otomatis masuk zona aman yang sangat tinggi meskipun operasional usahanya sedang merugi ($X_3$ negatif). Altman menetapkan *capping* pada $X_4 = 3.0$ untuk menstabilkan model dari distorsi struktur permodalan ekstrem.

#### Q3: *Mengapa nilai cut-off pada model MDA bernilai 0.3844 dan bukan 0?*
> **Jawaban:** Pada analisis diskriminan Fisher, titik potong objektif ditentukan oleh titik tengah antara dua titik berat centroid kelompok sampel:
> $$\text{Cut-off} = \frac{\bar{Z}_{\text{distress}} + \bar{Z}_{\text{non-distress}}}{2} = \frac{-2.4502 + 3.2189}{2} = 0.38435 \approx 0.3844$$
> Nilai di atas $0.3844$ lebih condong ke karakteristik kelompok sehat, sedangkan di bawahnya condong ke kelompok bangkrut.

#### Q4: *Mengapa kita membutuhkan Machine Learning XGBoost jika Altman Z-Score sudah ada?*
> **Jawaban:** Model Altman dan MDA adalah model parametrik linear yang mengasumsikan hubungan antar-rasio bersifat aditif linear dan data berdistribusi normal multivariat. Dalam kenyataan pasar modal, interaksi risiko keuangan sering kali bersifat **non-linear dan asimetris**. XGBoost sebagai algoritma *tree-based ensemble* mampu memetakan interaksi non-linear yang kompleks dan menangani *imbalanced data* di BEI (di mana emiten sehat jauh lebih banyak daripada emiten bangkrut) dengan sensitivitas yang jauh lebih tinggi.

#### Q5: *Mengapa meminimalkan Type II Error (False Negative) lebih diprioritaskan dalam evaluasi model?*
> **Jawaban:** Dalam manajemen risiko kredit dan investasi pasar modal, kerugian akibat *Type I Error* (salah memprediksi emiten sehat sebagai distress) hanyalah *opportunity loss* (kehilangan peluang untung). Sebaliknya, kerugian akibat *Type II Error* (gagal mendeteksi emiten yang akan bangkrut dan mengiranya aman) adalah *direct capital default loss* (kehilangan seluruh modal/utang macet). Oleh karena itu, metrik *Recall* dan *AUC-ROC* yang tinggi pada model XGBoost sistem ini menjadi jaminan keandalan tertinggi bagi pemangku kepentingan.

---

## 📜 Lisensi & Pengutipan
Proyek ini dikembangkan untuk keperluan akademik dan penelitian skripsi. Silakan gunakan dan rujuk repositori ini dengan mencantumkan atribusi kepada peneliti.
