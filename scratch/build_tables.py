import zipfile
import xml.etree.ElementTree as ET
import os
import shutil

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
ET.register_namespace('w', W_NS)
ET.register_namespace('w14', M_NS)

from setup_ready import make_p, make_caption, build_table

# 1. Build Table 4.8 Data
t48_headers = ["No", "Item Pengujian", "Skenario / Detail Pengecekan", "Hasil yang Diharapkan", "Status (OK)", "Catatan"]
t48_widths = [500, 1600, 2600, 2400, 600, 800] # Total = 8500 dxa

t48_rows_data = [
    {
        'cells': [
            "1",
            "Validasi Parameter Input dan Rasio Keuangan",
            "Pengecekan variabel pos neraca dan laba rugi yang digunakan (Aset Lancar, Liabilitas Lancar, Total Aset, Laba Ditahan, EBIT, Total Liabilitas, Total Ekuitas, Pendapatan, Beban Bunga) serta pembentukan rasio diskriminan X1 (Working Capital/Total Assets), X2 (Retained Earnings/Total Assets), X3 (EBIT/Total Assets), X4 (Equity/Total Liabilities dengan aturan capping X4 <= 3.0), dan X5 (Sales/Total Assets).",
            "Parameter pos laporan keuangan dan formula rasio yang digunakan sudah relevan, sesuai dengan standar akuntansi keuangan serta kaidah literatur Altman (1995/2017) dalam mendeteksi tekanan likuiditas, profitabilitas, produktivitas, dan solvabilitas emiten manufaktur.",
            "OK",
            "Relevan dan sesuai kaidah akuntansi Altman (1995/2017)."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "2",
            "Kesesuaian Alur dan Fleksibilitas Input Data",
            "Pengecekan alur pengoperasian sistem mulai dari pemilihan mode input (Input Manual, Impor Excel Taksonomi XBRL resmi IDX, Impor berkas CSV, hingga Ekstraksi Dokumen PDF Laporan Tahunan), proses validasi data, hingga eksekusi analisis.",
            "Alur aplikasi sistematis, intuitif, dan mudah dipahami. Sistem mampu membaca dan mengekstraksi data secara akurat dari berbagai format berkas tanpa menimbulkan galat teknis.",
            "OK",
            "Multi-channel input (Manual, Excel XBRL, CSV, PDF) bekerja presisi tanpa galat."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "3",
            "Validasi Hasil Klasifikasi Multi-Model",
            "Pengujian masukan data emiten dengan kondisi fundamental sehat (contoh: ICBP) dan emiten yang mengalami kerugian/restrukturisasi (contoh: AISA, ALTO, atau ANDI).",
            "Sistem berhasil menampilkan kalkulasi dan klasifikasi kondisi kesehatan keuangan secara presisi melalui tiga metode: Altman Z''-Score (Aman, Grey, Distress), MDA Fisher Koefisien Baru (Cut-off 0.3844), dan model XGBoost (Distress vs Non-Distress).",
            "OK",
            "Klasifikasi tri-model konsisten dan akurat membedakan kondisi emiten."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "4",
            "Kejelasan Informasi Probabilitas dan Derajat Risiko",
            "Pengecekan visualisasi derajat kerentanan finansial, nilai probabilitas distress berbasis sigmoid XGBoost, margin log-odds, nilai komparasi skor Altman, serta penetapan konsensus 3 Kategori (Safe Zone, Grey Area, Distress Zone).",
            "Aplikasi menyajikan tingkat probabilitas dan zonasi risiko secara jelas, komunikatif, transparan, dan mudah dipahami melalui indikator visual (gauge meter & lencana status risiko) tanpa ambigu.",
            "OK",
            "Visualisasi gauge meter dan zonasi risiko jelas serta tidak ambigu."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "5",
            "Validasi Indikator Peringatan Dini (Early Warning) & Diagnosa",
            "Pengecekan modul evaluasi 5 Faktor Pemicu Tekanan Finansial (EBIT < 0, TIE < 1.0, CFO < 0, CE < 0, NWC < 0), dekomposisi pemicu utama (distress drivers), serta rekomendasi manajerial bagi pemangku kepentingan (equity investor dan perbankan/kreditur).",
            "Indikator peringatan dini dan rekomendasi manajerial yang ditampilkan logis, relevan secara teori manajemen risiko keuangan, dan memberikan wawasan analitis yang dapat ditindaklanjuti (actionable insight).",
            "OK",
            "Indikator early warning logis dan memberikan rekomendasi yang actionable."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "6",
            "Penegasan Bukan Vonis Pailit / Opini Audit Legal",
            "Pengecekan adanya klausul batasan (disclaimer) atau penegasan bahwa hasil prediksi aplikasi adalah alat bantu pendukung keputusan (decision support system) berbasis data historis dan bukan merupakan opini audit akuntan publik independen atau putusan pailit legal pengadilan niaga.",
            "Aplikasi secara eksplisit mencantumkan batasan bahwa hasil prediksi sistem merupakan instrumen skrining awal mitigasi risiko dan tetap memerlukan konfirmasi audit serta analisis fundamental kualitatif mendalam.",
            "OK",
            "Klausul batasan (disclaimer) DSS tercantum tegas dan proporsional."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "7",
            "Validasi Komparasi Model & Metrik Evaluasi AI",
            "Pengecekan menu evaluasi performa model: lencana keselarasan (Model Concordance Badge), visualisasi matriks kesalahan (Confusion Matrix), kurva ROC-AUC, serta ringkasan metrik statistik (Accuracy, Sensitivity/Recall, Precision, Specificity, F1-Score, dan Youden's J Index).",
            "Modul perbandingan model tersaji secara objektif, informatif, dan akurat, sehingga mempermudah validator dalam memahami komparasi keandalan metode parametrik statistik dengan algoritma machine learning.",
            "OK",
            "Metrik evaluasi tersaji komprehensif, objektif, dan informatif."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "8",
            "Kemudahan Pemahaman Tampilan Dasbor dan Visualisasi",
            "Pengecekan antarmuka pengguna (UI/UX), tata letak kartu ringkasan eksekutif, kontras warna indikator risiko (Hijau = Aman, Amber/Kuning = Waspada, Merah = Distress), grafik Radar Chart, dan grafik kepentingan fitur (Feature Importance).",
            "Tata letak informasi terstruktur rapi, kontras visual nyaman dibaca, representasi grafik mudah diinterpretasikan oleh analis keuangan, serta tidak membingungkan pengguna awam.",
            "OK",
            "UI/UX terstruktur rapi, kontras visual nyaman, dan mudah dipahami."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "9",
            "Validasi Riwayat Analisis dan Fitur Ekspor Data",
            "Pengecekan fitur penyimpanan riwayat analisis ke basis data, penelusuran kembali histori analisis emiten sebelumnya, filter pencarian riwayat, serta fungsionalitas ekspor rekapan/memo eksekutif ke format Excel atau CSV.",
            "Sistem berhasil menyimpan log hasil prediksi dengan integritas data yang konsisten, histori dapat diakses kembali dengan cepat, dan berkas ekspor laporan dapat diunduh tanpa kerusakan format (corrupt).",
            "OK",
            "Log tersimpan konsisten dan berkas ekspor laporan berhasil diunduh."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "10",
            "Kesesuaian Aplikasi sebagai Sistem Pendukung Keputusan (DSS)",
            "Pengecekan fungsionalitas aplikasi secara komprehensif dalam membantu proses mitigasi risiko investasi saham, analisis kelayakan kredit perbankan, dan pengawasan kesehatan keuangan perusahaan manufaktur di BEI.",
            "Aplikasi dinilai sangat layak dan andal digunakan sebagai Sistem Pendukung Keputusan (Decision Support System) berbasis kecerdasan buatan dan analisis multivariat untuk sektor manufaktur BEI.",
            "OK",
            "Sangat layak dan andal sebagai sistem pendukung keputusan (DSS) manufaktur BEI."
        ],
        'aligns': ['center', 'left', 'left', 'left', 'center', 'left'],
        'bold': False
    },
    {
        'cells': [
            "Hasil",
            "Kesimpulan Pengesahan UAT Pakar: Berdasarkan hasil pengujian 10 butir di atas, seluruh butir berstatus OK (100% kelayakan). Aplikasi secara resmi dinyatakan LAYAK sebagai Sistem Pendukung Keputusan Prediksi Financial Distress Industri Manufaktur BEI."
        ],
        'colspan': {1: 5},
        'aligns': ['center', 'left'],
        'is_subtotal': True,
        'bg_fill': "E2E8F0",
        'bold': True
    }
]

tbl_4_8 = build_table(t48_headers, t48_rows_data, t48_widths)

# 2. Build Table 4.9 Data
t49_headers = ["No", "Pernyataan Kuesioner Evaluasi Pengguna", "Total Skor", "Skor Maks", "Rata-rata", "Persentase (%)", "Kategori Penilaian"]
t49_widths = [600, 3900, 700, 750, 750, 800, 1000] # Total = 8500 dxa

t49_rows_data = [
    # Header Dimensi A
    {
        'cells': ["A", "Dimensi Kemudahan dan Antarmuka Aplikasi (System Usability / UI & UX)"],
        'colspan': {1: 6},
        'aligns': ['center', 'left'],
        'is_subtotal': True,
        'bg_fill': "CBD5E1",
        'bold': True
    },
    {
        'cells': ["A.1", "Saya merasa aplikasi ini mudah digunakan dan dioperasikan.", "54", "65", "4.15", "83.08%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.2*", "Saya merasa alur kerja pada aplikasi ini terlalu rumit untuk digunakan.", "37", "65", "2.85", "56.92%", "Cukup Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.3", "Tata letak menu navigasi (Dashboard, Data Keuangan, Prediksi, Evaluasi) tersusun secara logis dan jelas.", "55", "65", "4.23", "84.62%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.4*", "Saya merasa membutuhkan bantuan teknis orang lain untuk dapat menggunakan aplikasi ini.", "41", "65", "3.15", "63.08%", "Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.5", "Tampilan visual, grafik radar, dan indikator speedometer (gauge) menarik serta mudah dibaca.", "56", "65", "4.31", "86.15%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.6*", "Saya merasa ada inkonsistensi pada tampilan antarmuka saat berpindah antar halaman.", "36", "65", "2.77", "55.38%", "Cukup Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.7", "Saya merasa percaya diri saat mengeksplorasi dan menganalisis emiten menggunakan aplikasi ini.", "48", "65", "3.69", "73.85%", "Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.8*", "Saya merasa perlu mempelajari panduan teknis yang panjang terlebih dahulu sebelum dapat menggunakannya.", "41", "65", "3.15", "63.08%", "Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.9*", "Saya merasa sistem ini membingungkan saat menampilkan hasil pengolahan data rasio keuangan.", "36", "65", "2.77", "55.38%", "Cukup Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["A.10", "Menurut saya, aplikasi ini sudah bagus dan pantas digunakan oleh analis keuangan, investor, maupun akademisi.", "54", "65", "4.15", "83.08%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    # Subtotal Dimensi A
    {
        'cells': ["Subtotal", "Rata-rata Dimensi Kemudahan dan Antarmuka (Terkonversi / Recoded)", "466", "650", "3.58", "71.69%", "Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'is_subtotal': True,
        'bg_fill': "F1F5F9",
        'bold': True
    },
    # Header Dimensi B
    {
        'cells': ["B", "Dimensi Relevansi Output dan Kinerja Fitur Sistem Pendukung Keputusan (DSS)"],
        'colspan': {1: 6},
        'aligns': ['center', 'left'],
        'is_subtotal': True,
        'bg_fill': "CBD5E1",
        'bold': True
    },
    {
        'cells': ["B.1", "Fitur input data (Pintasan Emiten BEI, Tarik API Otomatis, Upload Excel/PDF/CSV, Koreksi Manual) berfungsi dengan baik dan memudahkan penyiapan data.", "58", "65", "4.46", "89.23%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.2", "Perhitungan 4 rasio keuangan (X1 Modal Kerja, X2 Saldo Laba, X3 EBIT, X4 Ekuitas terhadap Liabilitas) disajikan secara transparan dan mudah dipahami.", "55", "65", "4.23", "84.62%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.3", "Hasil klasifikasi status (Safe Zone, Grey Zone, dan Distress Zone / Non-Distress) ditampilkan dengan status risiko yang jelas dan tegas.", "55", "65", "4.23", "84.62%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.4", "Visualisasi Quantum Gauge, Consensus Gauge, dan probabilitas XGBoost membantu pengguna memahami tingkat keparahan risiko kebangkrutan emiten.", "56", "65", "4.31", "86.15%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.5", "Fitur Perbandingan & Evaluasi Model menampilkan perbandingan antara Altman Z''-Score, MDA Baru, dan XGBoost secara jelas dan berimbang.", "58", "65", "4.46", "89.23%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.6", "Penyajian metrik evaluasi model (Akurasi, Presisi, Recall, Confusion Matrix, dan ROC Curve) memberikan keyakinan atas validitas model Machine Learning yang digunakan.", "57", "65", "4.38", "87.69%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.7", "Fitur analisis pemangku kepentingan (Dashboard Investor Saham dan Kreditur/Perbankan) serta simulasi What-If memberikan wawasan mendalam yang relevan untuk pengambilan keputusan.", "55", "65", "4.23", "84.62%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.8", "Ringkasan memo eksekutif (Executive Memo) dan fitur ekspor laporan yang dihasilkan aplikasi bermanfaat sebagai dokumen pendukung analisis finansial riil.", "55", "65", "4.23", "84.62%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    {
        'cells': ["B.9", "Secara keseluruhan, output aplikasi ini sudah relevan dan bermanfaat sebagai sistem pendukung keputusan (decision support system) deteksi dini financial distress pada industri manufaktur BEI.", "56", "65", "4.31", "86.15%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'bold': False
    },
    # Subtotal Dimensi B
    {
        'cells': ["Subtotal", "Rata-rata Dimensi Relevansi Output & Kinerja Fitur DSS", "505", "585", "4.32", "86.32%", "Sangat Baik"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'is_subtotal': True,
        'bg_fill': "F1F5F9",
        'bold': True
    },
    # Total Agregat
    {
        'cells': ["Total", "Rekapitulasi Skor Akseptansi Pengguna Sistem Web Streamlit (n = 13 Responden)", "971", "1235", "3.93", "78.62%", "Baik / Layak"],
        'aligns': ['center', 'left', 'center', 'center', 'center', 'center', 'center'],
        'is_subtotal': True,
        'bg_fill': "E2E8F0",
        'bold': True
    }
]

tbl_4_9 = build_table(t49_headers, t49_rows_data, t49_widths)

print("Both tables built successfully.")
