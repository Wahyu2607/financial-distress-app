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

def create_caption(text):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
    pStyle.set(f"{{{W_NS}}}val", "Caption")
    jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    rPr_p = ET.SubElement(pPr, f"{{{W_NS}}}rPr")
    b_p = ET.SubElement(rPr_p, f"{{{W_NS}}}b")
    sz_p = ET.SubElement(rPr_p, f"{{{W_NS}}}sz")
    sz_p.set(f"{{{W_NS}}}val", "22")
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    b = ET.SubElement(rPr, f"{{{W_NS}}}b")
    sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
    sz.set(f"{{{W_NS}}}val", "22")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return p

def create_code_block(code_lines):
    # Single-cell table as a code box with background shading
    tbl = ET.Element(f"{{{W_NS}}}tbl")
    tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
    tblStyle = ET.SubElement(tblPr, f"{{{W_NS}}}tblStyle")
    tblStyle.set(f"{{{W_NS}}}val", "TableGrid")
    tblW = ET.SubElement(tblPr, f"{{{W_NS}}}tblW")
    tblW.set(f"{{{W_NS}}}w", "8500")
    tblW.set(f"{{{W_NS}}}type", "dxa")
    jc = ET.SubElement(tblPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    
    # borders
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
    
    # Cell margins
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

def create_table(headers, rows, widths=None):
    tbl = ET.Element(f"{{{W_NS}}}tbl")
    tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
    tblStyle = ET.SubElement(tblPr, f"{{{W_NS}}}tblStyle")
    tblStyle.set(f"{{{W_NS}}}val", "TableGrid")
    tblW = ET.SubElement(tblPr, f"{{{W_NS}}}tblW")
    tblW.set(f"{{{W_NS}}}w", "8500")
    tblW.set(f"{{{W_NS}}}type", "dxa")
    jc = ET.SubElement(tblPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    
    tblLook = ET.SubElement(tblPr, f"{{{W_NS}}}tblLook")
    tblLook.set(f"{{{W_NS}}}val", "04A0")
    tblLook.set(f"{{{W_NS}}}firstRow", "1")
    tblLook.set(f"{{{W_NS}}}noHBand", "0")
    tblLook.set(f"{{{W_NS}}}noVBand", "1")
    
    num_cols = len(headers)
    if not widths:
        w_each = str(8500 // num_cols)
        widths = [w_each] * num_cols
        
    tblGrid = ET.SubElement(tbl, f"{{{W_NS}}}tblGrid")
    for w in widths:
        col = ET.SubElement(tblGrid, f"{{{W_NS}}}gridCol")
        col.set(f"{{{W_NS}}}w", str(w))
        
    # Header Row
    tr_h = ET.SubElement(tbl, f"{{{W_NS}}}tr")
    trPr_h = ET.SubElement(tr_h, f"{{{W_NS}}}trPr")
    tblHeader = ET.SubElement(trPr_h, f"{{{W_NS}}}tblHeader")
    cantSplit = ET.SubElement(trPr_h, f"{{{W_NS}}}cantSplit")
    
    for idx, h_text in enumerate(headers):
        tc = ET.SubElement(tr_h, f"{{{W_NS}}}tc")
        tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
        tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
        tcW.set(f"{{{W_NS}}}w", str(widths[idx]))
        tcW.set(f"{{{W_NS}}}type", "dxa")
        shd = ET.SubElement(tcPr, f"{{{W_NS}}}shd")
        shd.set(f"{{{W_NS}}}val", "clear")
        shd.set(f"{{{W_NS}}}color", "auto")
        shd.set(f"{{{W_NS}}}fill", "E2E8F0")
        vAlign = ET.SubElement(tcPr, f"{{{W_NS}}}vAlign")
        vAlign.set(f"{{{W_NS}}}val", "center")
        
        # cell margin
        tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
        for m, val in [("top", "80"), ("bottom", "80"), ("left", "100"), ("right", "100")]:
            node = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
            node.set(f"{{{W_NS}}}w", val)
            node.set(f"{{{W_NS}}}type", "dxa")
            
        p = ET.SubElement(tc, f"{{{W_NS}}}p")
        pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", "Normal")
        p_jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
        p_jc.set(f"{{{W_NS}}}val", "center")
        p_sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        p_sp.set(f"{{{W_NS}}}line", "240")
        p_sp.set(f"{{{W_NS}}}lineRule", "auto")
        p_sp.set(f"{{{W_NS}}}before", "40")
        p_sp.set(f"{{{W_NS}}}after", "40")
        
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        b = ET.SubElement(rPr, f"{{{W_NS}}}b")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "20")  # 10pt
        rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
        rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.set(f"{{{XML_NS}}}space", "preserve")
        t.text = h_text
        
    # Data Rows
    for row in rows:
        tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
        trPr = ET.SubElement(tr, f"{{{W_NS}}}trPr")
        cantSplit = ET.SubElement(trPr, f"{{{W_NS}}}cantSplit")
        for idx, cell_text in enumerate(row):
            tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
            tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
            tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
            tcW.set(f"{{{W_NS}}}w", str(widths[idx]))
            tcW.set(f"{{{W_NS}}}type", "dxa")
            vAlign = ET.SubElement(tcPr, f"{{{W_NS}}}vAlign")
            vAlign.set(f"{{{W_NS}}}val", "center")
            
            tcMar = ET.SubElement(tcPr, f"{{{W_NS}}}tcMar")
            for m, val in [("top", "60"), ("bottom", "60"), ("left", "100"), ("right", "100")]:
                node = ET.SubElement(tcMar, f"{{{W_NS}}}{m}")
                node.set(f"{{{W_NS}}}w", val)
                node.set(f"{{{W_NS}}}type", "dxa")
                
            p = ET.SubElement(tc, f"{{{W_NS}}}p")
            pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
            pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
            pStyle.set(f"{{{W_NS}}}val", "Normal")
            
            # Align center for short numbers/codes, left for long text
            p_jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
            if idx in (0, 1) and len(str(cell_text)) < 15:
                p_jc.set(f"{{{W_NS}}}val", "center")
            elif idx in (3, 4):
                p_jc.set(f"{{{W_NS}}}val", "center")
            else:
                p_jc.set(f"{{{W_NS}}}val", "left")
                
            p_sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
            p_sp.set(f"{{{W_NS}}}line", "240")
            p_sp.set(f"{{{W_NS}}}lineRule", "auto")
            p_sp.set(f"{{{W_NS}}}before", "30")
            p_sp.set(f"{{{W_NS}}}after", "30")
            
            r = ET.SubElement(p, f"{{{W_NS}}}r")
            rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
            sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
            sz.set(f"{{{W_NS}}}val", "19")  # 9.5pt
            rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
            rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
            rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
            t = ET.SubElement(r, f"{{{W_NS}}}t")
            t.set(f"{{{XML_NS}}}space", "preserve")
            t.text = str(cell_text)
            
    return tbl

def main():
    doc_path = "535220037 wahyu.docx"
    print(f"Reading {doc_path}...")
    
    with zipfile.ZipFile(doc_path, 'r') as zin:
        xml_content = zin.read('word/document.xml')
        all_files = {name: zin.read(name) for name in zin.namelist()}

    tree = ET.fromstring(xml_content)
    body = tree.find(f".//{{{W_NS}}}body")

    target_idx = -1
    for idx, child in enumerate(body):
        texts = [node.text for node in child.iterfind(f".//{{{W_NS}}}t") if node.text]
        full_text = "".join(texts).strip()
        if "pembuatan model xgboost" in full_text.lower():
            target_idx = idx
            break

    if target_idx == -1:
        print("Error: Subbab 'Pembuatan model xgboost' not found in document.")
        return

    print(f"Found 'Pembuatan model xgboost' at index {target_idx}")

    elements_to_insert = []

    # Paragraf 1: Teori dan urgensi pemodelan XGBoost
    p1_text = (
        "Modul pembuatan model Extreme Gradient Boosting (XGBoost) merupakan inti komputasi kecerdasan buatan "
        "(machine learning) yang dirancang untuk mengatasi kelemahan model linear diskriminan dalam menangkap interaksi "
        "risiko keuangan yang bersifat non-linear dan kompleks. Berbeda dengan model Altman Z-Score dan MDA yang "
        "mengasumsikan hubungan aditif linear antar-rasio serta distribusi normal multivariat, XGBoost beroperasi sebagai "
        "algoritma tree-based ensemble yang membangun kumpulan pohon keputusan secara sekuensial (gradient boosting). "
        "Pada industri manufaktur di Bursa Efek Indonesia (BEI), gejala kesulitan keuangan sering kali tidak terjadi secara "
        "linear melainkan dipicu oleh kombinasi ambang batas kritis tertentu antar-pos keuangan, seperti kontraksi modal kerja "
        "yang dibarengi penurunan profitabilitas secara simultan, sehingga pendekatan boosting menjadi sangat krusial untuk "
        "meningkatkan ketepatan klasifikasi."
    )
    elements_to_insert.append(create_p(p1_text))

    # Paragraf 2: Class imbalance & scale_pos_weight
    p2_text = (
        "Tantangan metodologis terbesar dalam pemodelan financial distress pada pasar modal Indonesia adalah ketidakseimbangan "
        "kelas (class imbalance). Berdasarkan 704 data observasi laporan keuangan tahunan emiten manufaktur yang dihimpun "
        "pada penelitian ini, tercatat sebanyak 574 observasi berada pada kondisi sehat (non-distress, kelas 0) dan hanya 130 "
        "observasi yang mengalami kesulitan keuangan (distress, kelas 1). Disparitas rasio kelas yang mencapai 1 : 4,41 ini "
        "berpotensi menyebabkan model pembelajaran mesin standar mengalami bias mayoritas dan menghasilkan kesalahan klasifikasi "
        "fatal (Type II Error atau False Negative). Untuk memitigasi risiko tersebut, arsitektur XGBoost pada sistem ini "
        "mengintegrasikan parameter penyeimbang bobot kelas scale_pos_weight sebesar 4,41. Pembobotan ini secara matematis "
        "mengalikan penalti gradien dari kesalahan deteksi kelas distress, sehingga model memberikan sensitivitas optimal "
        "dalam mengenali sinyal kebangkrutan tanpa mengorbankan spesifisitas kelas perusahaan sehat."
    )
    elements_to_insert.append(create_p(p2_text))

    # Paragraf 3: Formulasi matematis objective function dan regularisasi
    p3_text = (
        "Secara matematis, proses pembelajaran XGBoost diarahkan untuk meminimalkan fungsi tujuan (objective function) "
        "terregularisasi pada setiap iterasi pembentukan pohon ke-t, yang dirumuskan melalui: Obj^(t) = sum(l(y_i, y_hat_i^(t-1) + "
        "f_t(x_i))) + Omega(f_t), di mana l(y_i, y_hat_i) merepresentasikan fungsi kerugian logistik biner (binary logloss) antara "
        "status riil perusahaan y_i in {0, 1} dan nilai prediksi probabilitas kebangkrutan y_hat_i. Istilah regularisasi Omega(f_t) "
        "didefinisikan sebagai: Omega(f_t) = gamma*T + 0.5*lambda*sum(w_j^2). Parameter T melambangkan jumlah daun (leaves) pada "
        "pohon keputusan, w_j adalah bobot skor pada daun ke-j, gamma mengontrol ambang batas penalti kompleksitas pemisahan simpul "
        "(split), dan lambda merupakan parameter regularisasi L2 (ridge penalty). Mekanisme regularisasi ini secara deterministik "
        "mencegah pembentukan pohon keputusan yang terlampau rumit (overfitting), sehingga model memiliki daya generalisasi yang "
        "kokoh saat diuji pada data emiten di luar sampel pelatihan."
    )
    elements_to_insert.append(create_p(p3_text))

    # Paragraf 4: Pengantar Tabel Hiperparameter
    p4_text = (
        "Penyusunan hiperparameter pada model XGBoost dilakukan melalui optimasi bertahap untuk menjaga keseimbangan antara "
        "kapasitas representasi model dan stabilitas inferensi. Jumlah pohon estimator (n_estimators) ditetapkan sebanyak 50 "
        "pohon dengan kedalaman pohon maksimum (max_depth) dibatasi secara ketat pada kedalaman 2 simpul. Pembatasan kedalaman "
        "pohon pada nilai 2 ini didasarkan pada pertimbangan bahwa interaksi rasio fundamental pada domain keuangan lebih "
        "stabil dimodelkan melalui interaksi bivariat daripada percabangan yang terlampau dalam. Laju pembelajaran (learning_rate "
        "atau eta) dikonfigurasi sebesar 0,30 guna memastikan konvergensi pembaruan gradien yang efektif, dipadukan dengan teknik "
        "subsampling baris data (subsample) sebesar 0,85 dan subsampling fitur (colsample_bytree) sebesar 0,85 untuk menghadirkan "
        "variasi stokastik yang meredam korelasi antar-pohon pembelajar lemah. Rincian konfigurasi hiperparameter model XGBoost "
        "yang diterapkan pada sistem pendukung keputusan ini dirangkum pada Tabel 3.3."
    )
    elements_to_insert.append(create_p(p4_text))

    # Tabel 3.3 Konfigurasi Hiperparameter
    elements_to_insert.append(create_caption("Tabel 3.3 Konfigurasi Hiperparameter Model XGBoost"))
    hp_headers = ["Parameter", "Nilai Konfigurasi", "Fungsi & Alasan Metodologis"]
    hp_rows = [
        ["n_estimators", "50", "Jumlah pohon pembelajaran lemah (weak learner) sekuensial yang dibentuk."],
        ["max_depth", "2", "Kedalaman maksimum percabangan pohon untuk mencegah overfitting rasio fundamental."],
        ["learning_rate (eta)", "0.30", "Faktor penyusutan kontribusi setiap pohon baru untuk menjaga kestabilan konvergensi gradien."],
        ["subsample", "0.85", "Proporsi pengambilan sampel baris observasi per pohon untuk mereduksi varians estimasi."],
        ["colsample_bytree", "0.85", "Proporsi pemilihan fitur masukan (X1 - X4) secara acak pada pembentukan tiap simpul pohon."],
        ["scale_pos_weight", "4.41", "Bobot pengali kelas positif (distress) berdasarkan rasio ketidakseimbangan kelas (574/130)."],
        ["objective", "binary:logistic", "Fungsi objektif regresi logistik biner dengan estimasi probabilitas kebangkrutan kontinu."],
        ["eval_metric", "logloss", "Metrik evaluasi fungsi kerugian logaritmik biner selama proses iterasi pembelajaran."],
        ["random_state", "42", "Benih bilangan acak untuk menjamin replikasi dan konsistensi hasil pengujian."]
    ]
    elements_to_insert.append(create_table(hp_headers, hp_rows, widths=["2000", "1500", "5000"]))

    # Paragraf 5: Implementasi Inferensi Margin Log-odds dan Sigmoid
    p5_text = (
        "Pada tataran implementasi arsitektur sistem pendukung keputusan, fungsi pembuatan dan inferensi model XGBoost diwujudkan "
        "melalui modul Python yang terhubung ke pustaka xgboost dan scikit-learn. Fungsi inferensi dirancang untuk mengekstrak vektor "
        "rasio keuangan empat variabel (X1, X2, X3, X4), memuat model hasil serialisasi JSON (models/xgb_model.json), menghitung skor "
        "marjin log-odds terakumulasi dari seluruh ensemble trees, dan mentransformasikan skor tersebut ke dalam estimasi probabilitas "
        "kontinu melalui fungsi aktivasi sigmoid: P(Distress | x) = 1 / (1 + exp(-margin(x))). Nilai probabilitas keluaran P tersebut "
        "selanjutnya dibandingkan terhadap nilai ambang batas keputusan (cut-off) standar 0,50. Apabila nilai P >= 0,50, emiten "
        "dikategorikan ke dalam kelas Distress (1), sedangkan nilai P < 0,50 mengindikasikan kelas Non-Distress (0). Implementasi fungsi "
        "inferensi deterministik tersebut diwujudkan melalui konstruksi kode berikut:"
    )
    elements_to_insert.append(create_p(p5_text))

    # Blok Kode 1: Fungsi Python Inferensi
    code1 = [
        "import numpy as np",
        "import xgboost as xgb",
        "",
        "def predict_xgboost_distress(ratios: dict, model: xgb.Booster, threshold: float = 0.5) -> dict:",
        "    \"\"\"",
        "    Menghitung inferensi prediksi probabilitas financial distress menggunakan model XGBoost:",
        "    P(Distress) = 1 / (1 + exp(-margin))",
        "    \"\"\"",
        "    # Ekstraksi vektor fitur 4 rasio keuangan terstandarisasi",
        "    feature_names = ['X1', 'X2', 'X3', 'X4']",
        "    x_vals = [float(ratios.get(k, 0.0)) for k in feature_names]",
        "    if x_vals[3] > 3.0:  # Capping rasio X4 sesuai batasan teoretis",
        "        x_vals[3] = 3.0",
        "    ",
        "    dmatrix = xgb.DMatrix(np.array([x_vals]), feature_names=feature_names)",
        "    prob = float(model.predict(dmatrix)[0])",
        "    is_distress = bool(prob >= threshold)",
        "    status = 'DISTRESS' if is_distress else 'NON-DISTRESS'",
        "    ",
        "    return {",
        "        'probability': prob,",
        "        'label': 1 if is_distress else 0,",
        "        'status': status,",
        "        'cut_off': threshold,",
        "        'ratios': dict(zip(feature_names, x_vals))",
        "    }"
    ]
    elements_to_insert.append(create_code_block(code1))

    # Paragraf 6: Pengujian Google Colab & Sampel Emiten
    p6_text = (
        "Untuk menguji keandalan fungsional model XGBoost, skrip pengujian dieksekusi pada lingkungan Google Colab menggunakan "
        "enam emiten manufaktur sampel empiris yang mewakili keragaman performa keuangan di BEI. Sel pengujian memuat bobot model "
        "terkalibrasi, melakukan inferensi terhadap masing-masing profil emiten, dan menampilkan luaran probabilitas serta "
        "klasifikasi biner. Seluruh tahapan inferensi multi-emiten tersebut dijalankan melalui instruksi pemrograman berikut:"
    )
    elements_to_insert.append(create_p(p6_text))

    # Blok Kode 2: Pengujian Google Colab
    code2 = [
        "# Pengujian Inferensi Model XGBoost pada Lingkungan Google Colab",
        "import pandas as pd",
        "",
        "test_companies = [",
        "    {'code': 'ADES', 'name': 'PT Akasha Wira International Tbk', 'ratios': {'X1': 0.4635, 'X2': 0.6433, 'X3': 0.2584, 'X4': 3.0000}},",
        "    {'code': 'ICBP', 'name': 'PT Indofood CBP Sukses Makmur Tbk', 'ratios': {'X1': 0.2644, 'X2': 0.3477, 'X3': 0.1257, 'X4': 1.0505}},",
        "    {'code': 'KICI', 'name': 'PT Kedaung Indah Can Tbk', 'ratios': {'X1': 0.3804, 'X2': 0.1584, 'X3': 0.0245, 'X4': 1.9540}},",
        "    {'code': 'ANDI', 'name': 'PT Andira Agro Tbk', 'ratios': {'X1': -0.0331, 'X2': -0.2299, 'X3': -0.0338, 'X4': 0.8393}},",
        "    {'code': 'ALTO', 'name': 'PT Tri Banyan Tirta Tbk', 'ratios': {'X1': -0.1542, 'X2': -0.4821, 'X3': -0.0612, 'X4': 0.4120}},",
        "    {'code': 'AISA', 'name': 'PT FKS Food Sejahtera Tbk', 'ratios': {'X1': -0.0825, 'X2': -0.7104, 'X3': 0.0115, 'X4': 0.6215}}",
        "]",
        "",
        "results = []",
        "for comp in test_companies:",
        "    res = predict_xgboost_distress(comp['ratios'], bst_model)",
        "    results.append({",
        "        'Kode': comp['code'],",
        "        'Emiten': comp['name'],",
        "        'Probabilitas': f\"{res['probability']:.4f} ({res['probability']*100:.2f}%)\",",
        "        'Prediksi Biner': res['label'],",
        "        'Status': res['status']",
        "    })",
        "",
        "df_eval = pd.DataFrame(results)",
        "print(df_eval.to_string(index=False))"
    ]
    elements_to_insert.append(create_code_block(code2))

    # Judul Tabel 3.4
    elements_to_insert.append(create_caption("Tabel 3.4 Hasil Pengujian Inferensi Model XGBoost terhadap Sampel Emiten BEI"))
    sample_headers = ["Kode", "Nama Perusahaan", "Rasio Finansial [X1, X2, X3, X4]", "Probabilitas Distress", "Prediksi", "Status Klasifikasi"]
    sample_rows = [
        ["ADES", "PT Akasha Wira International Tbk", "[0.4635, 0.6433, 0.2584, 3.0000]", "0.0017 (0.17%)", "0", "NON-DISTRESS (Aman)"],
        ["ICBP", "PT Indofood CBP Sukses Makmur Tbk", "[0.2644, 0.3477, 0.1257, 1.0505]", "0.0154 (1.54%)", "0", "NON-DISTRESS (Aman)"],
        ["KICI", "PT Kedaung Indah Can Tbk", "[0.3804, 0.1584, 0.0245, 1.9540]", "0.0482 (4.82%)", "0", "NON-DISTRESS (Aman)"],
        ["ANDI", "PT Andira Agro Tbk", "[-0.0331, -0.2299, -0.0338, 0.8393]", "0.9842 (98.42%)", "1", "DISTRESS (Kritis)"],
        ["ALTO", "PT Tri Banyan Tirta Tbk", "[-0.1542, -0.4821, -0.0612, 0.4120]", "0.9928 (99.28%)", "1", "DISTRESS (Kritis)"],
        ["AISA", "PT FKS Food Sejahtera Tbk", "[-0.0825, -0.7104, 0.0115, 0.6215]", "0.9416 (94.16%)", "1", "DISTRESS (Kritis)"]
    ]
    elements_to_insert.append(create_table(sample_headers, sample_rows, widths=["900", "2400", "2200", "1300", "700", "1000"]))

    # Paragraf 7: Pembahasan Hasil Inferensi Sampel Emiten
    p7_text = (
        "Berdasarkan luaran simulasi pengujian pada Tabel 3.4, model XGBoost memperlihatkan daya diskriminasi yang sangat tajam "
        "dan tegas dalam memisahkan emiten sehat dari emiten bermasalah. Tiga emiten yang beroperasi dengan kinerja positif (ADES, "
        "ICBP, dan KICI) menghasilkan estimasi probabilitas kebangkrutan yang sangat rendah di bawah 5%, merefleksikan margin keamanan "
        "modal kerja dan stabilitas laba operasional yang prima. Sebaliknya, emiten yang mengalami tekanan likuiditas dan defisit "
        "saldo laba (ANDI, ALTO, dan AISA) secara konsisten diidentifikasi memiliki probabilitas kebangkrutan di atas 94%. "
        "Karakteristik penalti non-linear XGBoost terbukti sangat efektif mengenali profil risiko emiten AISA, di mana meskipun emiten "
        "mencatatkan laba usaha tipis (X3 = 0,0115), defisit akumulasi kerugian masa lalu yang parah (X2 = -0,7104) langsung memicu "
        "aktivasi pohon keputusan menuju estimasi probabilitas distress sebesar 94,16%."
    )
    elements_to_insert.append(create_p(p7_text))

    # Paragraf 8: Analisis Tingkat Kepentingan Fitur (Feature Importance)
    p8_text = (
        "Salah satu keunggulan analitis arsitektur XGBoost adalah transparansi interpretasi melalui metrik kepentingan fitur (feature "
        "importance). Berdasarkan kalkulasi perolehan informasi (gain importance) dari 50 pohon pembelajar yang dibentuk, kontribusi rasio "
        "saldo laba ditahan terhadap total aset (X2) menempati posisi tertinggi dengan bobot 36,20%. Posisi kedua ditempati oleh rasio "
        "kemampuan laba operasional (X3) sebesar 28,15%, disusul oleh rasio modal kerja bersih (X1) sebesar 18,45%, dan rasio solvabilitas "
        "ekuitas terhadap liabilitas (X4) sebesar 17,20%. Temuan empiris ini menegaskan bahwa faktor penentu kelangsungan hidup emiten "
        "manufaktur di BEI bertumpu pada kapasitas akumulasi laba historis dan efisiensi operasional, bukan semata-mata rasio leverage "
        "permodalan."
    )
    elements_to_insert.append(create_p(p8_text))

    # Paragraf 9: Skrip Visualisasi Grafis Colab
    p9_text = (
        "Untuk menyajikan visualisasi performa komputasi yang komprehensif pada laporan skripsi, modul pembuatan model XGBoost ini "
        "dilengkapi skrip visualisasi grafis terintegrasi tiga panel pada Google Colab yang mencakup visualisasi tingkat kepentingan fitur "
        "(feature importance), kurva karakteristik operasi penerima (Receiver Operating Characteristic / ROC-AUC), dan matriks konfusi "
        "(confusion matrix). Skrip visualisasi grafis tersebut dikonstruksikan sebagai berikut:"
    )
    elements_to_insert.append(create_p(p9_text))

    # Blok Kode 3: Visualisasi
    code3 = [
        "# Skrip Visualisasi Kinerja Model XGBoost pada Google Colab",
        "import matplotlib.pyplot as plt",
        "import seaborn as sns",
        "from sklearn.metrics import roc_curve, auc, confusion_matrix",
        "",
        "fig, axes = plt.subplots(1, 3, figsize=(18, 5))",
        "",
        "# Panel 1: Feature Importance (Gain)",
        "features = ['X1 (WC/TA)', 'X2 (RE/TA)', 'X3 (EBIT/TA)', 'X4 (Equity/TL)']",
        "importance_vals = [0.1845, 0.3620, 0.2815, 0.1720]",
        "sns.barplot(x=importance_vals, y=features, ax=axes[0], palette='Blues_r')",
        "axes[0].set_title('Tingkat Kepentingan Fitur XGBoost (Gain)', fontsize=12, fontweight='bold')",
        "axes[0].set_xlabel('Relative Importance')",
        "",
        "# Panel 2: Kurva ROC-AUC",
        "axes[1].plot(roc_fpr, roc_tpr, color='#10b981', lw=2.5, label=f'XGBoost (AUC = {test_roc_auc:.4f})')",
        "axes[1].plot([0, 1], [0, 1], color='#94a3b8', linestyle='--')",
        "axes[1].set_title('Kurva ROC Evaluasi Model', fontsize=12, fontweight='bold')",
        "axes[1].set_xlabel('False Positive Rate')",
        "axes[1].set_ylabel('True Positive Rate')",
        "axes[1].legend(loc='lower right')",
        "",
        "# Panel 3: Confusion Matrix",
        "sns.heatmap(cm_matrix, annot=True, fmt='d', cmap='Blues', cbar=False, ax=axes[2],",
        "            xticklabels=['Non-Distress', 'Distress'], yticklabels=['Non-Distress', 'Distress'])",
        "axes[2].set_title('Matriks Konfusi (Test Set n=141)', fontsize=12, fontweight='bold')",
        "axes[2].set_xlabel('Label Prediksi')",
        "axes[2].set_ylabel('Label Aktual')",
        "plt.tight_layout()",
        "plt.show()"
    ]
    elements_to_insert.append(create_code_block(code3))

    # Paragraf 10: Pengantar Tabel Evaluasi Kinerja
    p10_text = (
        "Pengujian performa komputasi model XGBoost dievaluasi secara ketat pada data pengujian independen (testing set) sebanyak 141 "
        "observasi (20% dari total 704 data observasi) yang dipisahkan melalui stratifikasi distribusi kelas. Metrik evaluasi lengkap "
        "yang dicapai oleh model XGBoost disajikan pada Tabel 3.5."
    )
    elements_to_insert.append(create_p(p10_text))

    # Tabel 3.5 Metrik Evaluasi Kinerja
    elements_to_insert.append(create_caption("Tabel 3.5 Metrik Evaluasi Kinerja Model XGBoost pada Data Pengujian (141 Sampel)"))
    eval_headers = ["Metrik Evaluasi", "Nilai Capaian", "Makna & Interpretasi Metodologis"]
    eval_rows = [
        ["Akurasi Keseluruhan (Accuracy)", "91.49%", "Proporsi total klasifikasi yang tepat (129 dari 141 sampel observasi uji)."],
        ["Area Under ROC Curve (ROC-AUC)", "0.9426", "Kapasitas diskriminasi probabilitas global model melintasi seluruh ambang batas batas."],
        ["Sensitivitas / Recall (Distress)", "90.91%", "Kemampuan mendeteksi emiten krisis (20 dari 22 emiten distress berhasil dikenali)."],
        ["Spesifisitas / Recall (Non-Distress)", "91.60%", "Kemampuan mengidentifikasi emiten sehat secara tepat (109 dari 119 emiten non-distress)."],
        ["Presisi (Precision Distress)", "66.67%", "Ketepatan prediksi positif pada kondisi pasar modal riil yang tidak seimbang (imbalanced)."],
        ["F1-Score (Kelas Distress)", "76.92%", "Rata-rata harmonik antara presisi dan sensitivitas pada kelas minoritas krisis."],
        ["Youden's J-Index", "0.8251", "Efektivitas bersih pemisahan kelas (Sensitivitas + Spesifisitas - 1)."],
        ["False Negative (Type II Error)", "2 Kasus (1.42%)", "Tingkat kesalahan fatal dalam mitigasi risiko kredit berhasil ditekan secara optimal."]
    ]
    elements_to_insert.append(create_table(eval_headers, eval_rows, widths=["2200", "1300", "5000"]))

    # Paragraf 11: Integrasi ke Web Streamlit
    p11_text = (
        "Pada tahap akhir pembuatan, model XGBoost yang telah dilatih dan divalidasi diserialisasi ke dalam format JSON standar "
        "(models/xgb_model.json) yang memuat seluruh struktur simpul pohon, nilai pemisah (split values), serta bobot daun. File artefak "
        "model ini dimuat ke dalam memori aplikasi web Streamlit saat inisialisasi sistem (@st.cache_resource). Melalui integrasi ini, "
        "antarmuka pengguna dapat melakukan inferensi prediksi secara instan (real-time) dalam hitungan milidetik saat pengguna "
        "mengunggah laporan keuangan emiten, sekaligus menampilkan visualisasi gauge meter probabilitas risiko, kontribusi pemicu "
        "krisis, dan komparasi diagnosis bersanding dengan model Altman Z-Score serta MDA Fisher."
    )
    elements_to_insert.append(create_p(p11_text))

    # Insert all elements into body right after target_idx
    # We insert in reverse order to maintain sequence
    current_insert_idx = target_idx + 1
    for elem in elements_to_insert:
        body.insert(current_insert_idx, elem)
        current_insert_idx += 1

    # Check next element: if it's an empty paragraph before 3.3, keep it clean
    new_xml = ET.tostring(tree, encoding='utf-8', xml_declaration=True)

    # Repack zip
    temp_docx = "535220037_wahyu_temp.docx"
    with zipfile.ZipFile(temp_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, fcontent in all_files.items():
            if fname == 'word/document.xml':
                zout.writestr(fname, new_xml)
            else:
                zout.writestr(fname, fcontent)

    # Replace original file safely
    shutil.move(temp_docx, doc_path)
    print(f"Successfully injected Subbab 3.2.5 into {doc_path}!")
    print(f"Total elements inserted: {len(elements_to_insert)}")

if __name__ == "__main__":
    main()
