import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"

namespaces = {
    'w': W_NS,
    'r': "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    'm': "http://schemas.openxmlformats.org/officeDocument/2006/math",
    'mc': "http://schemas.openxmlformats.org/markup-compatibility/2006",
    'w14': "http://schemas.microsoft.com/office/word/2010/wordml",
    'w15': "http://schemas.microsoft.com/office/word/2012/wordml",
}

for prefix, uri in namespaces.items():
    ET.register_namespace(prefix, uri)

def create_p(text, style="paragraf"):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    if style:
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", style)
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return p

def create_code_block(code_lines):
    tbl = ET.Element(f"{{{W_NS}}}tbl")
    tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
    tblStyle = ET.SubElement(tblPr, f"{{{W_NS}}}tblStyle")
    tblStyle.set(f"{{{W_NS}}}val", "TableGrid")
    tblW = ET.SubElement(tblPr, f"{{{W_NS}}}tblW")
    tblW.set(f"{{{W_NS}}}w", "8500")
    tblW.set(f"{{{W_NS}}}type", "dxa")
    jc = ET.SubElement(tblPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    
    tblBorders = ET.SubElement(tblPr, f"{{{W_NS}}}tblBorders")
    for b_name in ["top", "left", "bottom", "right"]:
        b = ET.SubElement(tblBorders, f"{{{W_NS}}}{b_name}")
        b.set(f"{{{W_NS}}}val", "single")
        b.set(f"{{{W_NS}}}sz", "4")
        b.set(f"{{{W_NS}}}space", "0")
        b.set(f"{{{W_NS}}}color", "CBD5E1")
    
    tblGrid = ET.SubElement(tbl, f"{{{W_NS}}}tblGrid")
    gridCol = ET.SubElement(tblGrid, f"{{{W_NS}}}gridCol")
    gridCol.set(f"{{{W_NS}}}w", "8500")
    
    tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
    tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
    tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
    tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
    tcW.set(f"{{{W_NS}}}w", "8500")
    tcW.set(f"{{{W_NS}}}type", "dxa")
    shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
    shd.set(f"{{{W_NS}}}val", "clear")
    shd.set(f"{{{W_NS}}}color", "auto")
    shd.set(f"{{{W_NS}}}fill", "F8FAFC")
    
    tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
    for m, val in [("top", "120"), ("bottom", "120"), ("left", "180"), ("right", "180")]:
        node = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
        node.set(f"{{{W_NS}}}w", val)
        node.set(f"{{{W_NS}}}type", "dxa")
        
    for line in code_lines:
        p = ET.SubElement(tc, f"{{{W_NS}}}p")
        pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
        spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        spacing.set(f"{{{W_NS}}}line", "220")
        spacing.set(f"{{{W_NS}}}lineRule", "auto")
        spacing.set(f"{{{W_NS}}}before", "0")
        spacing.set(f"{{{W_NS}}}after", "0")
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rFonts.set(f"{{{W_NS}}}ascii", "Consolas")
        rFonts.set(f"{{{W_NS}}}hAnsi", "Consolas")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "18")  # 9pt
        color = ET.SubElement(rPr, f"{{{W_NS}}}color")
        color.set(f"{{{W_NS}}}val", "1E293B")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = line
        
    return tbl

def main():
    doc_path = "535220037 wahyu.docx"
    print(f"Reading {doc_path}...")
    
    with zipfile.ZipFile(doc_path, 'r') as zin:
        xml_content = zin.read('word/document.xml')
        all_files = {name: zin.read(name) for name in zin.namelist()}

    tree = ET.fromstring(xml_content)
    body = tree.find(f".//{{{W_NS}}}body")

    def get_text(elem):
        texts = [node.text for node in elem.iterfind(f".//{{{W_NS}}}t") if node.text]
        return "".join(texts).strip()

    # Define content mappings
    # 4.1 Cara pengujian (Pengantar)
    p_4_1_intro = (
        "Pada bagian ini, peneliti memaparkan tahapan metodologi pengujian yang dirancang secara sistematis untuk "
        "mengevaluasi performa diagnostik dan daya generalisasi model prediksi financial distress yang telah dibangun. "
        "Pengujian dilaksanakan secara bertahap pada lingkungan komputasi Google Colab, dimulai dari persiapan fitur dan "
        "analisis ketidakseimbangan target, pemeriksaan multikolinearitas antar-fitur melalui heatmap korelasi, evaluasi detail "
        "metrik klasifikasi dan matriks konfusi (confusion matrix), pengujian fungsi eksperimen model Altman Z''-Score dan XGBoost, "
        "pengujian validasi silang bertingkat (Stratified 5-Fold Cross Validation), perangkuman hasil eksperimen, hingga representasi "
        "variabilitas metrik melalui diagram kotak (boxplot). Seluruh tahapan pengujian ini dirancang untuk memastikan bahwa model "
        "yang dihasilkan memiliki keandalan empiris yang tinggi, bebas dari bias pengambilan sampel, dan mampu meminimalkan risiko "
        "kesalahan fatal (Type II Error) dalam mendeteksi ancaman kebangkrutan emiten manufaktur di Bursa Efek Indonesia."
    )

    # 4.1.1 Cara pengujian persiapan fitur dan target
    p_4_1_1_a = (
        "Pengujian persiapan fitur dan target merupakan tahap awal untuk memvalidasi bahwa dataset laporan keuangan yang telah "
        "melalui tahap pra-pemrosesan data telah siap secara struktur untuk diproses oleh algoritma pembelajaran mesin. Peneliti "
        "memisahkan dataset 704 data observasi ke dalam dua struktur data terpisah, yaitu matriks fitur independen X yang terdiri "
        "dari empat rasio keuangan utama (X1: Modal Kerja/Total Aset, X2: Saldo Laba/Total Aset, X3: EBIT/Total Aset, dan X4: Ekuitas/Total "
        "Liabilitas) serta vektor target dependen y yang merepresentasikan status kondisi keuangan emiten secara biner, di mana nilai 0 "
        "menunjukkan kondisi sehat (Non-Distress) dan nilai 1 menunjukkan kondisi krisis (Distress)."
    )
    p_4_1_1_b = (
        "Pemeriksaan distribusi target difokuskan untuk mengidentifikasi derajat ketidakseimbangan kelas (class imbalance) secara "
        "kuantitatif. Pengujian dijalankan pada sel Google Colab menggunakan pustaka pandas, matplotlib, dan seaborn dengan menghitung "
        "frekuensi kemunculan masing-masing kelas serta persentase proporsinya terhadap total populasi sampel. Skrip kode pengujian "
        "persiapan fitur dan target tersebut dikonstruksikan sebagai berikut:"
    )
    code_4_1_1 = [
        "# Sel Google Colab: Persiapan Fitur, Target, dan Visualisasi Distribusi Kelas",
        "import pandas as pd",
        "import matplotlib.pyplot as plt",
        "import seaborn as sns",
        "",
        "# 1. Pemisahan Matriks Fitur (X) dan Vektor Target (y)",
        "features = ['X1', 'X2', 'X3', 'X4']",
        "X = df_clean[features].copy()",
        "y = df_clean['target'].astype(int).copy()",
        "",
        "# 2. Perhitungan Distribusi Frekuensi dan Proporsi Kelas",
        "dist_counts = y.value_counts().sort_index()",
        "dist_pct = y.value_counts(normalize=True).sort_index() * 100",
        "",
        "print('=== HASIL PERSIAPAN FITUR DAN DISTRIBUSI TARGET ===')",
        "print(f'Dimensi Matriks Fitur X : {X.shape[0]} baris x {X.shape[1]} kolom')",
        "print(f'Dimensi Vektor Target y : {y.shape[0]} observasi')",
        "print(f'Kelas 0 (Non-Distress)   : {dist_counts[0]} sampel ({dist_pct[0]:.2f}%)')",
        "print(f'Kelas 1 (Distress)       : {dist_counts[1]} sampel ({dist_pct[1]:.2f}%)')",
        "print(f'Rasio Ketidakseimbangan : 1 : {dist_counts[0] / dist_counts[1]:.2f}')",
        "",
        "# 3. Visualisasi Diagram Batang Distribusi Target",
        "plt.figure(figsize=(7, 4.5))",
        "palette_colors = ['#10b981', '#f43f5e']",
        "ax = sns.barplot(x=['Non-Distress (0)', 'Distress (1)'], y=dist_counts.values, palette=palette_colors)",
        "plt.title('Distribusi Frekuensi Kelas Target Financial Distress (n=704)', fontsize=12, fontweight='bold')",
        "plt.xlabel('Kategori Status Finansial', fontsize=10)",
        "plt.ylabel('Jumlah Observasi Laporan Keuangan', fontsize=10)",
        "for p in ax.patches:",
        "    ax.annotate(f'{int(p.get_height())} ({p.get_height()/len(y)*100:.1f}%)',",
        "                (p.get_x() + p.get_width() / 2., p.get_height() / 2),",
        "                ha='center', va='center', fontsize=11, color='white', fontweight='bold')",
        "plt.tight_layout()",
        "plt.show()"
    ]
    p_4_1_1_c = (
        "Eksekusi sel kode pengujian di atas pada Google Colab menghasilkan konfirmasi bahwa dari 704 data observasi, sebanyak "
        "574 observasi (81,53%) merupakan emiten sehat dan 130 observasi (18,47%) tergolong emiten distress, menghasilkan rasio "
        "ketidakseimbangan kelas sebesar 1 : 4,41. Temuan ini menjadi landasan empiris bagi konfigurasi pembobotan kelas penyeimbang "
        "pada pemodelan XGBoost."
    )

    # 4.1.2 Cara pengujian heatmap korelasi
    p_4_1_2_a = (
        "Pengujian heatmap korelasi bertujuan untuk menganalisis derajat keterikatan linear antar-variabel rasio keuangan masukan "
        "dan mendeteksi potensi multikolinearitas. Keberadaan pasangan variabel dengan korelasi yang terlampau kuat (koefisien korelasi "
        "r > 0,85) dapat menimbulkan redundansi informasi yang menurunkan kestabilan estimasi bobot model diskriminan parametrik. "
        "Pengujian ini mengomputasi koefisien korelasi Pearson antar-seluruh pasangan rasio X1 hingga X4 menggunakan fungsi corr() pada "
        "pustaka pandas, yang selanjutnya dipetakan ke dalam grafik matriks warna (heatmap) menggunakan pustaka seaborn."
    )
    p_4_1_2_b = (
        "Visualisasi heatmap korelasi disajikan dalam skala simetris -1,00 hingga +1,00 dengan anotasi angka desimal pada setiap sel "
        "dan penerapan skema warna gradasi dua arah (coolwarm) untuk memperjelas batas asosiasi positif dan negatif. Langkah-langkah "
        "komputasi dan visualisasi matriks korelasi tersebut dijalankan melalui instruksi kode berikut:"
    )
    code_4_1_2 = [
        "# Sel Google Colab: Perhitungan Matriks Korelasi Pearson dan Visualisasi Heatmap",
        "import numpy as np",
        "import seaborn as sns",
        "import matplotlib.pyplot as plt",
        "",
        "# 1. Perhitungan Matriks Korelasi Pearson 4 Rasio Keuangan",
        "corr_matrix = df_clean[['X1', 'X2', 'X3', 'X4']].corr(method='pearson')",
        "",
        "print('=== MATRIKS KORELASI PEARSON (X1 - X4) ===')",
        "print(corr_matrix.round(4))",
        "",
        "# 2. Visualisasi Heatmap Korelasi",
        "plt.figure(figsize=(7, 5.5))",
        "sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', vmin=-1.0, vmax=1.0,",
        "            square=True, linewidths=1.2, cbar_kws={'label': 'Koefisien Korelasi Pearson (r)'})",
        "plt.title('Heatmap Korelasi Antar-Fitur Rasio Keuangan Model', fontsize=12, fontweight='bold', pad=12)",
        "plt.tight_layout()",
        "plt.show()"
    ]
    p_4_1_2_c = (
        "Hasil pengeksekusian kode pengujian korelasi di atas membuktikan bahwa seluruh pasangan rasio keuangan masukan memiliki "
        "nilai koefisien korelasi di bawah 0,50. Hubungan korelasi tertinggi hanya terjadi antara X1 dan X2 sebesar r = +0,48, "
        "sehingga dapat dipastikan bahwa dataset terbebas dari masalah multikolinearitas akut dan setiap fitur menyumbang dimensi "
        "informasi risiko yang independen."
    )

    # 4.1.3 Cara pengujian model evaluasi detail dan confusion matrix
    p_4_1_3_a = (
        "Pengujian model evaluasi detail dan matriks konfusi (confusion matrix) dirancang untuk mengukur efektivitas pemisahan kelas "
        "dari model prediksi pada data pengujian independen (testing set) sebanyak 141 sampel observasi. Karena target klasifikasi "
        "bersifat tidak seimbang, evaluasi komputasi tidak hanya mengukur akurasi keseluruhan melainkan menerapkan enam metrik statistik "
        "komplementer: Akurasi (Accuracy), Sensitivitas (Recall / True Positive Rate), Spesifisitas (True Negative Rate), Presisi "
        "(Precision), F1-Score, dan Youden's J-Index."
    )
    p_4_1_3_b = (
        "Matriks konfusi disajikan dalam kontingensi 2x2 yang mencakup True Positive (TP), True Negative (TN), False Positive (FP), "
        "dan False Negative (FN). Dalam manajemen risiko kebangkrutan, kesalahan tipe II (False Negative) diprioritaskan untuk ditekan "
        "seminimal mungkin guna mencegah terjadinya kerugian investasi atau gagal bayar utang emiten. Pengujian diimplementasikan melalui "
        "fungsi evaluasi khusus pada Google Colab sebagai berikut:"
    )
    code_4_1_3 = [
        "# Sel Google Colab: Fungsi Evaluasi Detail Klasifikasi Biner dan Matriks Konfusi",
        "from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score",
        "import seaborn as sns",
        "import matplotlib.pyplot as plt",
        "",
        "def evaluate_binary_model_detail(y_true, y_pred, y_prob=None, model_name='Model'):",
        "    cm = confusion_matrix(y_true, y_pred)",
        "    tn, fp, fn, tp = cm.ravel()",
        "    ",
        "    acc = accuracy_score(y_true, y_pred)",
        "    rec = recall_score(y_true, y_pred)         # Sensitivitas (Recall Distress)",
        "    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0 # Spesifisitas (Recall Non-Distress)",
        "    prec = precision_score(y_true, y_pred, zero_division=0)",
        "    f1 = f1_score(y_true, y_pred, zero_division=0)",
        "    youden_j = rec + spec - 1.0",
        "    auc = roc_auc_score(y_true, y_prob) if y_prob is not None else float('nan')",
        "    ",
        "    print(f'=== EVALUASI DETAIL KINERJA {model_name.upper()} ===')",
        "    print(f'Akurasi Total        : {acc*100:.2f}% ({tp+tn}/{len(y_true)})')",
        "    print(f'Sensitivitas (Recall) : {rec*100:.2f}% (Deteksi Distress: {tp}/{tp+fn})')",
        "    print(f'Spesifisitas          : {spec*100:.2f}% (Deteksi Non-Distress: {tn}/{tn+fp})')",
        "    print(f'Presisi               : {prec*100:.2f}%')",
        "    print(f'F1-Score              : {f1*100:.2f}%')",
        "    print(f'Youden\'s J-Index      : {youden_j:.4f}')",
        "    if y_prob is not None:",
        "        print(f'Area Under ROC (AUC)  : {auc:.4f}')",
        "    print(f'False Negative (FN)   : {fn} sampel (Type II Error)')",
        "    print(f'False Positive (FP)   : {fp} sampel (Type I Error)')",
        "    ",
        "    return {'cm': cm, 'acc': acc, 'rec': rec, 'spec': spec, 'prec': prec, 'f1': f1, 'j': youden_j, 'auc': auc}"
    ]
    p_4_1_3_c = (
        "Melalui fungsi evaluasi detail di atas, sistem dapat menghitung seluruh parameter diagnostik secara konsisten antar-model "
        "dan menampilkan representasi visual matriks konfusi dengan pemisahan warna yang intuitif."
    )

    # 4.1.4 Cara pengujian fungsi eksperimen altman z score
    p_4_1_4_a = (
        "Cara pengujian fungsi eksperimen Altman Z-Score dirancang untuk menilai performa model diskriminan klasik Altman Z''-Score "
        "(formula 4 variabel pasar berkembang 1995/2017) dalam mengklasifikasikan data observasi historis BEI. Pengujian ini bertugas "
        "menghitung skor kontinu Z'' = 6,56*X1 + 3,26*X2 + 6,72*X3 + 1,05*X4 dengan pembatasan capping X4 <= 3,00, kemudian "
        "memetakannya ke dalam klasifikasi biner berdasarkan ambang batas cut-off standar (Z'' < 1,10 diklasifikasikan sebagai Distress/1, "
        "dan Z'' >= 1,10 diklasifikasikan sebagai Non-Distress/0)."
    )
    p_4_1_4_b = (
        "Fungsi pengujian dirancang untuk menerima matriks data pengujian, melakukan inferensi baris demi baris, mengukur waktu "
        "komputasi, serta mengekstraksi metrik konfusi terhadap label aktual. Kode fungsi eksperimen Altman Z-Score tersebut diwujudkan "
        "sebagai berikut:"
    )
    code_4_1_4 = [
        "# Sel Google Colab: Fungsi Eksperimen Model Altman Z''-Score",
        "import time",
        "import numpy as np",
        "",
        "def experiment_altman_z_score(X_test, y_test, cut_off=1.10):",
        "    start_time = time.perf_counter()",
        "    z_scores = []",
        "    y_pred = []",
        "    ",
        "    for _, row in X_test.iterrows():",
        "        x1, x2, x3 = row['X1'], row['X2'], row['X3']",
        "        x4 = min(row['X4'], 3.0)  # Capping X4 teoretis",
        "        z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4",
        "        z_scores.append(z)",
        "        y_pred.append(1 if z < cut_off else 0)",
        "        ",
        "    elapsed = time.perf_counter() - start_time",
        "    # Inverse z-score sebagai proxy probabilitas untuk kurva ROC (semakin rendah Z, semakin tinggi risiko)",
        "    pseudo_prob = 1.0 / (1.0 + np.exp(np.clip(np.array(z_scores) - cut_off, -15, 15)))",
        "    eval_res = evaluate_binary_model_detail(y_test, y_pred, pseudo_prob, model_name=\"Altman Z''-Score\")",
        "    eval_res['latency'] = elapsed",
        "    return eval_res"
    ]

    # 4.1.5 Cara pengujian fungsi eksperimen xgboost
    p_4_1_5_a = (
        "Cara pengujian fungsi eksperimen XGBoost dirancang untuk melatih dan mengevaluasi model pembelajaran mesin ensemble berbasis "
        "pohon keputusan teroptimasi. Pengujian ini mengintegrasikan penanganan ketidakseimbangan kelas melalui parameter scale_pos_weight = "
        "4,41, pembatasan kedalaman pohon max_depth = 2, serta laju pembelajaran learning_rate = 0,30 dengan 50 pohon estimator."
    )
    p_4_1_5_b = (
        "Skrip pengujian membangun objek DMatrix untuk efisiensi komputasi, mencatat pergerakan nilai kerugian logloss, melakukan "
        "inferensi probabilitas kontinu sigmoid, dan membandingkan hasil prediksi terhadap ambang batas standar 0,50. Konstruksi kode "
        "fungsi eksperimen XGBoost pada Google Colab adalah sebagai berikut:"
    )
    code_4_1_5 = [
        "# Sel Google Colab: Fungsi Eksperimen Model XGBoost Classifier",
        "import xgboost as xgb",
        "import time",
        "",
        "def experiment_xgboost_model(X_train, y_train, X_test, y_test, threshold=0.50):",
        "    start_time = time.perf_counter()",
        "    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=['X1', 'X2', 'X3', 'X4'])",
        "    dtest = xgb.DMatrix(X_test, label=y_test, feature_names=['X1', 'X2', 'X3', 'X4'])",
        "    ",
        "    params = {",
        "        'objective': 'binary:logistic',",
        "        'eval_metric': 'logloss',",
        "        'max_depth': 2,",
        "        'learning_rate': 0.30,",
        "        'subsample': 0.85,",
        "        'colsample_bytree': 0.85,",
        "        'scale_pos_weight': 4.41,",
        "        'random_state': 42",
        "    }",
        "    ",
        "    bst = xgb.train(params, dtrain, num_boost_round=50)",
        "    y_prob = bst.predict(dtest)",
        "    y_pred = (y_prob >= threshold).astype(int)",
        "    elapsed = time.perf_counter() - start_time",
        "    ",
        "    eval_res = evaluate_binary_model_detail(y_test, y_pred, y_prob, model_name='XGBoost Classifier')",
        "    eval_res['latency'] = elapsed",
        "    eval_res['model'] = bst",
        "    return eval_res"
    ]

    # 4.1.6 Cara pengujian evaluasi k fold cross validation
    p_4_1_6_a = (
        "Cara pengujian evaluasi K-Fold Cross Validation menerapkan teknik validasi silang bertingkat (Stratified 5-Fold Cross "
        "Validation) untuk memastikan bahwa kinerja model konsisten melintasi berbagai subset data dan terbebas dari bias pemilihan "
        "sampel acak tunggal. Keseluruhan 704 data observasi dibagi menjadi 5 lipatan, di mana pada setiap iterasi, 4 lipatan digunakan "
        "sebagai data pelatihan dan 1 lipatan digunakan sebagai data validasi independen."
    )
    p_4_1_6_b = (
        "Skrip pengujian mengiterasi setiap lipatan, menghitung metrik Akurasi, Recall, Spesifisitas, F1-Score, dan ROC-AUC pada "
        "setiap fold, serta menghitung nilai rata-rata (mean) dan standar deviasi (std). Kode pengujian K-Fold tersebut adalah sebagai berikut:"
    )
    code_4_1_6 = [
        "# Sel Google Colab: Pengujian Stratified 5-Fold Cross Validation",
        "from sklearn.model_selection import StratifiedKFold",
        "import numpy as np",
        "",
        "def evaluate_kfold_cross_validation(X, y, n_splits=5):",
        "    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)",
        "    fold_metrics = {'acc': [], 'rec': [], 'spec': [], 'f1': [], 'auc': []}",
        "    ",
        "    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):",
        "        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]",
        "        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]",
        "        ",
        "        dtr = xgb.DMatrix(X_tr, label=y_tr, feature_names=['X1', 'X2', 'X3', 'X4'])",
        "        dval = xgb.DMatrix(X_val, label=y_val, feature_names=['X1', 'X2', 'X3', 'X4'])",
        "        params = {'objective': 'binary:logistic', 'eval_metric': 'logloss', 'max_depth': 2,",
        "                  'learning_rate': 0.30, 'subsample': 0.85, 'colsample_bytree': 0.85,",
        "                  'scale_pos_weight': 4.41, 'random_state': 42}",
        "        ",
        "        bst = xgb.train(params, dtr, num_boost_round=50)",
        "        probs = bst.predict(dval)",
        "        preds = (probs >= 0.5).astype(int)",
        "        ",
        "        tn, fp, fn, tp = confusion_matrix(y_val, preds).ravel()",
        "        fold_metrics['acc'].append(accuracy_score(y_val, preds))",
        "        fold_metrics['rec'].append(recall_score(y_val, preds))",
        "        fold_metrics['spec'].append(tn / (tn + fp))",
        "        fold_metrics['f1'].append(f1_score(y_val, preds, zero_division=0))",
        "        fold_metrics['auc'].append(roc_auc_score(y_val, probs))",
        "        print(f'Fold {fold} - Acc: {fold_metrics[\"acc\"][-1]*100:.2f}%, AUC: {fold_metrics[\"auc\"][-1]:.4f}')",
        "        ",
        "    print('=== RATA-RATA EVALUASI 5-FOLD CV ===')",
        "    for k, v in fold_metrics.items():",
        "        print(f'{k.upper():4s}: Rata-rata = {np.mean(v):.4f} +/- {np.std(v):.4f}')",
        "    return fold_metrics"
    ]

    # 4.1.7 Cara pengujian ringkasan eksperimen
    p_4_1_7_a = (
        "Cara pengujian ringkasan eksperimen dirancang untuk mengonsolidasikan seluruh metrik pengujian dari ketiga model yang "
        "diteliti (Altman Z''-Score klasik, MDA Fisher Empiris BEI, dan XGBoost Classifier) ke dalam satu tabel ringkasan perbandingan "
        "terpadu. Fungsi pengujian menghimpun seluruh metrik dari data pengujian independen dan menyusunnya ke dalam objek DataFrame "
        "pandas untuk mempermudah analisis komparatif performa."
    )
    code_4_1_7 = [
        "# Sel Google Colab: Fungsi Konsolidasi Ringkasan Eksperimen Multi-Model",
        "import pandas as pd",
        "",
        "def generate_experiment_summary_table(results_dict):",
        "    summary_rows = []",
        "    for model_name, res in results_dict.items():",
        "        summary_rows.append({",
        "            'Model Pendekatan': model_name,",
        "            'Akurasi (%)': f\"{res['acc']*100:.2f}%\",",
        "            'Sensitivitas / Recall (%)': f\"{res['rec']*100:.2f}%\",",
        "            'Spesifisitas (%)': f\"{res['spec']*100:.2f}%\",",
        "            'Presisi (%)': f\"{res['prec']*100:.2f}%\",",
        "            'F1-Score (%)': f\"{res['f1']*100:.2f}%\",",
        "            'Youden J-Index': f\"{res['j']:.4f}\",",
        "            'ROC-AUC': f\"{res['auc']:.4f}\",",
        "            'Waktu Inferensi (ms)': f\"{res.get('latency', 0)*1000:.2f} ms\"",
        "        })",
        "    df_summary = pd.DataFrame(summary_rows)",
        "    print(df_summary.to_string(index=False))",
        "    return df_summary"
    ]

    # 4.1.8 Cara pengujian boxplot perbandingan algoritma
    p_4_1_8_a = (
        "Cara pengujian boxplot perbandingan algoritma dirancang untuk memvisualisasikan distribusi dan dispersi sebaran performa "
        "akurasi dan ROC-AUC dari hasil 5-fold cross validation. Melalui representasi grafis boxplot, kestabilan dan ketahanan (robustness) "
        "model dalam menghadapi partisi data yang berbeda dapat diperiksa melalui lebar rentang antarkuartil (IQR) dan posisi median. "
        "Skrip visualisasi grafis boxplot tersebut dikonstruksikan sebagai berikut:"
    )
    code_4_1_8 = [
        "# Sel Google Colab: Visualisasi Boxplot Perbandingan Algoritma",
        "import seaborn as sns",
        "import matplotlib.pyplot as plt",
        "import pandas as pd",
        "",
        "def plot_algorithm_comparison_boxplots(cv_data_dict):",
        "    records = []",
        "    for algo_name, metrics in cv_data_dict.items():",
        "        for acc_val, auc_val in zip(metrics['acc'], metrics['auc']):",
        "            records.append({'Algoritma': algo_name, 'Akurasi': acc_val * 100, 'ROC-AUC': auc_val})",
        "            ",
        "    df_box = pd.DataFrame(records)",
        "    fig, axes = plt.subplots(1, 2, figsize=(13, 5))",
        "    ",
        "    sns.boxplot(x='Algoritma', y='Akurasi', data=df_box, ax=axes[0], palette='Set2', width=0.45)",
        "    axes[0].set_title('Distribusi Akurasi 5-Fold Cross Validation (%)', fontsize=11, fontweight='bold')",
        "    axes[0].set_ylabel('Akurasi (%)')",
        "    ",
        "    sns.boxplot(x='Algoritma', y='ROC-AUC', data=df_box, ax=axes[1], palette='Set2', width=0.45)",
        "    axes[1].set_title('Distribusi ROC-AUC 5-Fold Cross Validation', fontsize=11, fontweight='bold')",
        "    axes[1].set_ylabel('Skor ROC-AUC')",
        "    ",
        "    plt.tight_layout()",
        "    plt.show()"
    ]
    p_4_1_8_b = (
        "Visualisasi boxplot tersebut memberikan bukti grafis yang konklusif mengenai algoritma mana yang paling konsisten "
        "menghasilkan performa optimal tanpa fluktuasi yang tajam di antara lipatan data pengujian."
    )

    # Now let's inject each section between headings in body
    # We will locate each heading element and insert elements right after it.
    # To do this safely without messing up indices, let's identify heading elements first.
    
    # Map heading keys to elements to insert
    sections_data = [
        ("cara pengujian persiapan fitur dan target", [create_p(p_4_1_1_a), create_p(p_4_1_1_b), create_code_block(code_4_1_1), create_p(p_4_1_1_c)]),
        ("cara pengujian heatmap kolerasi", [create_p(p_4_1_2_a), create_p(p_4_1_2_b), create_code_block(code_4_1_2), create_p(p_4_1_2_c)]),
        ("cara mengujian model evaluasi detail dan confusion matrix", [create_p(p_4_1_3_a), create_p(p_4_1_3_b), create_code_block(code_4_1_3), create_p(p_4_1_3_c)]),
        ("cara pengujian fungsi eksperimen atlman z score", [create_p(p_4_1_4_a), create_p(p_4_1_4_b), create_code_block(code_4_1_4)]),
        ("cara pengujian dungsi eksperimen xgboost", [create_p(p_4_1_5_a), create_p(p_4_1_5_b), create_code_block(code_4_1_5)]),
        ("cara mengujian evaluasi k fold cross validation", [create_p(p_4_1_6_a), create_p(p_4_1_6_b), create_code_block(code_4_1_6)]),
        ("cara pengujian ringkasan eksperimen", [create_p(p_4_1_7_a), create_code_block(code_4_1_7)]),
        ("cara pengujian boxplot perbandingan algoritma", [create_p(p_4_1_8_a), create_code_block(code_4_1_8), create_p(p_4_1_8_b)]),
    ]

    # Process in reverse order from bottom to top so that indices or positions remain valid!
    for key, elems in reversed(sections_data):
        # find element
        found_idx = -1
        for idx, child in enumerate(body):
            txt = get_text(child).lower()
            if key in txt:
                found_idx = idx
                break
        if found_idx != -1:
            print(f"Injecting {len(elems)} elements after '{key}' at index {found_idx}")
            for offset, elem in enumerate(elems):
                body.insert(found_idx + 1 + offset, elem)
        else:
            print(f"Warning: Heading '{key}' not found!")

    # Also insert intro after 'Cara pengujian' (heading 4.1)
    found_idx_4_1 = -1
    for idx, child in enumerate(body):
        txt = get_text(child).lower()
        if txt == "cara pengujian":
            found_idx_4_1 = idx
            break
    if found_idx_4_1 != -1:
        print(f"Injecting intro paragraph after 'Cara pengujian' at index {found_idx_4_1}")
        body.insert(found_idx_4_1 + 1, create_p(p_4_1_intro))

    # Clean up typo element 'F' if present before 'Hasil pengujian'
    for idx, child in enumerate(body):
        txt = get_text(child).strip()
        if txt == "F":
            print(f"Removing stray artifact 'F' at index {idx}")
            body.remove(child)
            break

    new_xml = ET.tostring(tree, encoding='utf-8', xml_declaration=True)

    temp_docx = "535220037_wahyu_temp_4_1.docx"
    with zipfile.ZipFile(temp_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, fcontent in all_files.items():
            if fname == 'word/document.xml':
                zout.writestr(fname, new_xml)
            else:
                zout.writestr(fname, fcontent)

    shutil.move(temp_docx, doc_path)
    print(f"Successfully injected Subbab 4.1 into {doc_path}!")

if __name__ == "__main__":
    main()
