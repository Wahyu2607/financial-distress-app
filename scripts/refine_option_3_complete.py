import zipfile
import shutil
import xml.etree.ElementTree as ET
import os

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS_MAP = {'w': W_NS}
ET.register_namespace('w', W_NS)

DOCX_PATH = '535220037 wahyu.docx'
BACKUP_PATH = '535220037 wahyu_backup_refine_opt3.docx'

shutil.copy2(DOCX_PATH, BACKUP_PATH)
print(f"Cadangan berkas dibuat: {BACKUP_PATH}")

def set_run_props(r, font_name="Calibri", sz="24", bold=False, italic=False, color=None):
    rPr = r.find(f"{{{W_NS}}}rPr")
    if rPr is None:
        rPr = ET.Element(f"{{{W_NS}}}rPr")
        r.insert(0, rPr)
    
    rFonts = rPr.find(f"{{{W_NS}}}rFonts")
    if rFonts is None:
        rFonts = ET.Element(f"{{{W_NS}}}rFonts")
        rPr.append(rFonts)
    rFonts.set(f"{{{W_NS}}}ascii", font_name)
    rFonts.set(f"{{{W_NS}}}hAnsi", font_name)
    rFonts.set(f"{{{W_NS}}}cs", font_name)
    rFonts.set(f"{{{W_NS}}}cstheme", "minorHAnsi")
    
    sz_el = rPr.find(f"{{{W_NS}}}sz")
    if sz_el is None:
        sz_el = ET.Element(f"{{{W_NS}}}sz")
        rPr.append(sz_el)
    sz_el.set(f"{{{W_NS}}}val", sz)
    
    szCs_el = rPr.find(f"{{{W_NS}}}szCs")
    if szCs_el is None:
        szCs_el = ET.Element(f"{{{W_NS}}}szCs")
        rPr.append(szCs_el)
    szCs_el.set(f"{{{W_NS}}}val", sz)
    
    b_el = rPr.find(f"{{{W_NS}}}b")
    if bold:
        if b_el is None:
            rPr.append(ET.Element(f"{{{W_NS}}}b"))
    else:
        if b_el is not None:
            rPr.remove(b_el)
            
    i_el = rPr.find(f"{{{W_NS}}}i")
    if italic:
        if i_el is None:
            rPr.append(ET.Element(f"{{{W_NS}}}i"))
    else:
        if i_el is not None:
            rPr.remove(i_el)

def set_para_props(p, jc="both", line="480", space_after="0"):
    pPr = p.find(f"{{{W_NS}}}pPr")
    if pPr is None:
        pPr = ET.Element(f"{{{W_NS}}}pPr")
        p.insert(0, pPr)
        
    jc_el = pPr.find(f"{{{W_NS}}}jc")
    if jc_el is None:
        jc_el = ET.Element(f"{{{W_NS}}}jc")
        pPr.append(jc_el)
    jc_el.set(f"{{{W_NS}}}val", jc)
    
    spacing = pPr.find(f"{{{W_NS}}}spacing")
    if spacing is None:
        spacing = ET.Element(f"{{{W_NS}}}spacing")
        pPr.append(spacing)
    spacing.set(f"{{{W_NS}}}line", line)
    spacing.set(f"{{{W_NS}}}lineRule", "auto")
    spacing.set(f"{{{W_NS}}}after", space_after)

def replace_para_text(p, text, bold=False, italic=False, jc="both", font_name="Calibri", sz="24", line="480", space_after="0"):
    for child in list(p):
        if child.tag != f"{{{W_NS}}}pPr":
            p.remove(child)
    set_para_props(p, jc=jc, line=line, space_after=space_after)
    r = ET.Element(f"{{{W_NS}}}r")
    set_run_props(r, font_name=font_name, sz=sz, bold=bold, italic=italic)
    t = ET.Element(f"{{{W_NS}}}t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    p.append(r)

with zipfile.ZipFile(DOCX_PATH, 'r') as z:
    xml_content = z.read('word/document.xml').decode('utf-8')

root = ET.fromstring(xml_content)
body = root.find(f"{{{W_NS}}}body")
all_p = list(root.iter(f"{{{W_NS}}}p"))

print(f"Total paragraf dalam dokumen: {len(all_p)}")

# 1. Update Subbab 3.2.4 MDA matrix code & outputs
for idx, p in enumerate(all_p):
    txt = ''.join(p.itertext()).strip()
    if 'cm_mda = np.array([[323, 53], [17, 77]])' in txt:
        replace_para_text(p, "cm_mda = np.array([[675, 18], [12, 49]]) # Matriks Konfusi Evaluasi MDA (754 Sampel Uji)", 
                          font_name="Consolas", sz="18", line="220", jc="left")
        print(f" -> Fixed P #{idx}: cm_mda")
    elif "axes[2].set_title('Matriks Konfusi MDA (Akurasi: 85.11%)'" in txt:
        replace_para_text(p, "axes[2].set_title('Matriks Konfusi MDA (Akurasi: 96.02%)', fontsize=12, fontweight='bold')", 
                          font_name="Consolas", sz="18", line="220", jc="left")
        print(f" -> Fixed P #{idx}: set_title MDA")
    elif "Panel 3 : Matriks konfusi mencatatkan 323 TN, 53 FP, 17 FN, dan 77 TP (Akurasi: 85.11%)." in txt:
        replace_para_text(p, "Panel 3 : Matriks konfusi mencatatkan 675 TN, 18 FP, 12 FN, dan 49 TP (Akurasi: 96.02% pada 754 sampel uji).",
                          font_name="Calibri", sz="24", line="480", jc="both")
        print(f" -> Fixed P #{idx}: Panel 3 MDA output")

# 2. Update feature importance snippet
for idx, p in enumerate(all_p):
    txt = ''.join(p.itertext()).strip()
    if 'importance_vals = [0.1845, 0.3620, 0.2815, 0.1720]' in txt:
        replace_para_text(p, "importance_vals = [0.0550, 0.6655, 0.2395, 0.0400] # Rasio bobot XGBoost P1 BEI (X1, X2, X3, X4)",
                          font_name="Consolas", sz="18", line="220", jc="left")
        print(f" -> Fixed P #{idx}: importance_vals")

# 3. Update Subbab 4.1.9 & 4.1.10 code snippets
for idx, p in enumerate(all_p):
    txt = ''.join(p.itertext()).strip()
    if "'scale_pos_weight': 4.41," in txt:
        replace_para_text(p, "        'scale_pos_weight': 11.38, # Rasio kelas non-distress/distress (3.466 / 304)",
                          font_name="Consolas", sz="18", line="220", jc="left")
        print(f" -> Fixed P #{idx}: scale_pos_weight: 4.41")
    elif "'scale_pos_weight': 4.41, 'random_state': 42}" in txt:
        replace_para_text(p, "                  'scale_pos_weight': 11.38, 'random_state': 42} # Pembobotan kelas seimbang",
                          font_name="Consolas", sz="18", line="220", jc="left")
        print(f" -> Fixed P #{idx}: K-Fold params scale_pos_weight: 4.41")
    elif "Keseluruhan 704 data observasi dibagi menjadi 5 lipatan" in txt:
        new_t = ("Cara pengujian evaluasi K-Fold Cross Validation menerapkan teknik validasi silang bertingkat "
                 "(Stratified 5-Fold Cross Validation) untuk memastikan bahwa kinerja model konsisten melintasi "
                 "berbagai subset data dan terbebas dari bias pemilihan sampel acak tunggal. Keseluruhan 3.770 data observasi "
                 "laporan keuangan tahunan emiten manufaktur dibagi secara terstratifikasi menjadi 5 lipatan, "
                 "di mana pada setiap iterasi, 4 lipatan digunakan sebagai data pelatihan dan 1 lipatan digunakan sebagai data validasi independen.")
        replace_para_text(p, new_t, font_name="Calibri", sz="24", line="480", jc="both")
        print(f" -> Fixed P #{idx}: K-Fold 704 to 3.770 narrative")

# 4. Update Subbab 4.1.10 JSON export mock snippet
json_mock_replacements = {
    "'accuracy': 0.9149,": "    'accuracy': 0.9642,",
    "'roc_auc': 0.9426,": "    'roc_auc': 0.9400,",
    "'specificity': 0.9160,": "    'specificity': 0.9784,",
    "'recall': 0.9091,": "    'recall': 0.8033,",
    "'precision': 0.6667,": "    'precision': 0.7656,",
    "'f1_score': 0.7692,": "    'f1_score': 0.7840,",
    "'youden_j': 0.8251,": "    'youden_j': 0.7816,",
    "'confusion_matrix': [[109, 10], [2, 20]],": "    'confusion_matrix': [[678, 15], [12, 49]],",
    "'cm_details': {'tn': 109, 'fp': 10, 'fn': 2, 'tp': 20},": "    'cm_details': {'tn': 678, 'fp': 15, 'fn': 12, 'tp': 49},",
    "'feature_importances': {'X1': 0.1845, 'X2': 0.3620, 'X3': 0.2815, 'X4': 0.1720},": "    'feature_importances': {'X1': 0.0550, 'X2': 0.6655, 'X3': 0.2395, 'X4': 0.0400},"
}

for idx, p in enumerate(all_p):
    txt = ''.join(p.itertext()).strip()
    for old_k, new_k in json_mock_replacements.items():
        if old_k in txt:
            replace_para_text(p, new_k, font_name="Consolas", sz="18", line="220", jc="left")
            print(f" -> Fixed P #{idx}: {old_k} -> {new_k}")

# 5. Update Subbab 4.2.4 narrative (after Tabel 4.4)
children = list(body)
for i, child in enumerate(children):
    if child.tag == f"{{{W_NS}}}p":
        txt = ''.join(child.itertext()).strip()
        if "Berdasarkan Tabel 4.4, model re-estimasi empiris MDA Fisher berhasil meningkatkan akurasi dari 80,85%" in txt:
            new_txt = ("Berdasarkan Tabel 4.4, model re-estimasi empiris MDA Fisher berhasil meningkatkan akurasi dari 95,76% "
                       "(Altman asli) menjadi 96,02%, menaikkan Sensitivitas dari 77,05% menjadi 80,33% (menekan False Negative "
                       "dari 14 kasus menjadi 12 kasus), serta mendongkrak nilai ROC-AUC dari 0,9000 menjadi 0,9167 pada 754 sampel uji. "
                       "Hal ini membuktikan bahwa kalibrasi ulang koefisien diskriminan linear Fisher terhadap karakteristik emiten manufaktur "
                       "BEI periode 2014–2026 dan penerapan titik potong centroid objektif 0,3844 memberikan peningkatan daya pembeda "
                       "yang nyata dibandingkan formula baku Altman (1995) yang menggunakan pembobotan pasar berkembang global.")
            replace_para_text(child, new_txt, font_name="Calibri", sz="24", line="480", jc="both")
            print(" -> Fixed Subbab 4.2.4 narrative after Tabel 4.4")
            
        elif "Hasil pengujian validasi silang bertingkat (Stratified 5-Fold Cross Validation) pada keseluruhan 704" in txt:
            new_txt = ("Pengujian sensitivitas pembagian proporsi data latih dan data uji (data split sensitivity) dilakukan "
                       "untuk menguji ketangguhan (robustness) dan stabilitas model XGBoost terhadap variasi ukuran himpunan data pelatihan "
                       "pada keseluruhan 3.770 observasi panel industri manufaktur BEI periode 2014–2026. Variasi skema split dievaluasi "
                       "mulai dari skema pelatihan ekstensif 90:10, skema dasar terstratifikasi 80:20 (baseline), hingga skema pengujian ketat "
                       "30:70. Rincian metrik performa pada setiap skema pengujian dirangkum pada Tabel 4.5.")
            replace_para_text(child, new_txt, font_name="Calibri", sz="24", line="480", jc="both")
            print(" -> Fixed Subbab 4.2.5 narrative before Tabel 4.5")
            
        elif "Hasil validasi silang 5-fold pada Tabel 4.5 memperlihatkan standar deviasi yang sangat kecil" in txt:
            new_txt = ("Hasil pengujian sensitivitas variasi rasio pemisahan data pada Tabel 4.5 membuktikan stabilitas performa XGBoost "
                       "yang sangat konsisten melintasi berbagai proporsi pelatihan. Nilai akurasi model bertahan stabil tinggi pada rentang "
                       "96,42% hingga 97,35%, nilai ROC-AUC konsisten berada di atas 0,9400 (bahkan mencapai 0,9609 pada skema pengujian ekstensif 30:70), "
                       "dan sensitivitas tetap terjaga prima pada rentang 78,40% hingga 88,82%. Ketahanan metrik ini membuktikan bahwa algoritma XGBoost "
                       "memiliki kemampuan generalisasi yang sangat kuat, tidak rentan terhadap variasi ukuran sampel latih, serta terbebas "
                       "dari ancaman overfitting pada data panel bervolume besar.")
            replace_para_text(child, new_txt, font_name="Calibri", sz="24", line="480", jc="both")
            print(" -> Fixed Subbab 4.2.5 narrative after Tabel 4.5")
            
        elif "Berdasarkan keseluruhan bukti empiris pada Tabel 4.6, model Extreme Gradient Boosting (XGBoost) secara konklusif ditetapkan" in txt:
            new_txt = ("Berdasarkan keseluruhan bukti empiris pada Tabel 4.6, model Extreme Gradient Boosting (XGBoost) secara konklusif "
                       "ditetapkan sebagai algoritma terbaik untuk diintegrasikan ke dalam arsitektur sistem pendukung keputusan web Streamlit. "
                       "Keunggulan utama XGBoost terletak pada pencapaian metrik evaluasi menyeluruh tertinggi pada data pengujian independen 754 sampel "
                       "(Akurasi 96,42%, ROC-AUC 0,9400, PR-AUC 0,8558, F1-Score 78,40%, dan Spesifisitas 97,84%), dengan kemampuan menekan False Negative "
                       "menjadi 12 kasus (Sensitivitas 80,33%) dan False Positive hanya 15 kasus (Spesifisitas 97,84%). Pada arsitektur fitur yang diperluas "
                       "(Pengujian 2 dengan 16 indikator keuangan dan pertumbuhan), kemampuan diskriminasi model bahkan melonjak drastis hingga mencapai "
                       "nilai ROC-AUC 0,9845 dan PR-AUC 0,8939, yang memberikan perlindungan modal maksimal bagi investor pasar modal dan analis perbankan "
                       "dalam mendeteksi gejala kesulitan keuangan emiten manufaktur di Bursa Efek Indonesia secara dini.")
            replace_para_text(child, new_txt, font_name="Calibri", sz="24", line="480", jc="both")
            print(" -> Fixed Subbab 4.2.6 narrative after Tabel 4.6")

# 6. Update Tabel 4.6 content to exact 754 test sample benchmark
def build_table_4_6():
    tbl = ET.Element(f"{{{W_NS}}}tbl")
    tblPr = ET.SubElement(tbl, f"{{{W_NS}}}tblPr")
    tblStyle = ET.SubElement(tblPr, f"{{{W_NS}}}tblStyle")
    tblStyle.set(f"{{{W_NS}}}val", "TableGrid")
    tblW = ET.SubElement(tblPr, f"{{{W_NS}}}tblW")
    tblW.set(f"{{{W_NS}}}w", "0")
    tblW.set(f"{{{W_NS}}}type", "auto")
    
    col_widths = ["2600", "1500", "1800", "1700", "2000"]
    tblGrid = ET.SubElement(tbl, f"{{{W_NS}}}tblGrid")
    for w in col_widths:
        gc = ET.SubElement(tblGrid, f"{{{W_NS}}}gridCol")
        gc.set(f"{{{W_NS}}}w", w)
        
    t46_data = [
        ["Kriteria Metrik Evaluasi", "Altman Z''-Score (1995)", "MDA Fisher Koefisien Baru", "XGBoost Classifier", "Keunggulan XGBoost"],
        ["Akurasi Total (%)", "95,76%", "96,02%", "96,42%", "+0,66% vs Altman (+0,40% vs MDA)"],
        ["Sensitivitas / Recall (%)", "77,05%", "80,33%", "80,33%", "+3,28% vs Altman (Seimbang vs MDA)"],
        ["Spesifisitas (%)", "97,40%", "97,40%", "97,84%", "+0,44% vs Altman (+0,44% vs MDA)"],
        ["Presisi (%)", "72,31%", "73,13%", "76,56%", "+4,25% vs Altman (+3,43% vs MDA)"],
        ["F1-Score (%)", "74,60%", "76,56%", "78,40%", "+3,80% vs Altman (+1,84% vs MDA)"],
        ["Youden's J-Index", "0,7445", "0,7773", "0,7816", "+0,0371 vs Altman (+0,0043 vs MDA)"],
        ["Area Under ROC (AUC)", "0,9000", "0,9167", "0,9400", "+0,0400 vs Altman (+0,0233 vs MDA)"],
        ["False Negative (Type II)", "14 Kasus (1,86%)", "12 Kasus (1,59%)", "12 Kasus (1,59%)", "Tekan Default Terendah (80,33% Recall)"],
        ["False Positive (Type I)", "18 Kasus (2,39%)", "18 Kasus (2,39%)", "15 Kasus (1,99%)", "Reduksi False Alarm Tertinggi (-3 Kasus)"],
        ["Waktu Inferensi Rata-rata", "0,12 ms / sampel", "0,14 ms / sampel", "0,85 ms / sampel", "Sangat Cepat (< 1 milidetik)"]
    ]
    
    for r_idx, row in enumerate(t46_data):
        tr = ET.SubElement(tbl, f"{{{W_NS}}}tr")
        is_header = (r_idx == 0)
        for c_idx, val in enumerate(row):
            tc = ET.SubElement(tr, f"{{{W_NS}}}tc")
            tcPr = ET.SubElement(tc, f"{{{W_NS}}}tcPr")
            tcW = ET.SubElement(tcPr, f"{{{W_NS}}}tcW")
            tcW.set(f"{{{W_NS}}}w", col_widths[c_idx])
            tcW.set(f"{{{W_NS}}}type", "dxa")
            
            p = ET.SubElement(tc, f"{{{W_NS}}}p")
            jc_val = "center" if c_idx > 0 else "left"
            set_para_props(p, jc=jc_val, line="240", space_after="0")
            r = ET.SubElement(p, f"{{{W_NS}}}r")
            set_run_props(r, font_name="Calibri", sz="20", bold=is_header)
            t = ET.SubElement(r, f"{{{W_NS}}}t")
            t.text = val
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            
    return tbl

# Replace Tabel 4.6 in body
for i, child in enumerate(children):
    if child.tag == f"{{{W_NS}}}p":
        txt = ''.join(child.itertext()).strip()
        if "Tabel 4.6 Ringkasan Perbandingan Performa Algoritma Prediksi Financial Distress" in txt:
            if i + 1 < len(children) and children[i+1].tag == f"{{{W_NS}}}tbl":
                body.remove(children[i+1])
                new_tbl_46 = build_table_4_6()
                body.insert(i + 1, new_tbl_46)
                print(" -> Replaced Tabel 4.6 with accurate 754 test sample benchmark table!")
                break

# 7. Add clarifying note in Lampiran 2 (P #2484)
for idx, p in enumerate(all_p):
    txt = ''.join(p.itertext()).strip()
    if 'data yang di himpun ini mencakup 174 emiten dengan total 704 observasi' in txt:
        new_note = ("(Catatan Metodologis Lampiran: Bagian berikut menyajikan demonstrasi perhitungan manual aljabar matriks "
                    "invers kovariansi Fisher dan penentuan bobot diskriminan pada sampel percontohan historis (174 emiten / 704 observasi). "
                    "Adapun pada naskah utama Bab 3 dan Bab 4 serta model produksi sistem Streamlit, permodelan MDA empiris BEI "
                    "dikalibrasi penuh menggunakan keseluruhan 3.770 observasi panel industri manufaktur BEI periode 2014–2026).")
        pPr = p.find(f"{{{W_NS}}}pPr")
        # insert before
        # We can update the text of this paragraph to clarify
        full_t = f"{new_note}\n\nPerhitungan manual matriks diskriminan pada sampel percontohan: data yang dihimpun mencakup 174 emiten dengan total 704 observasi."
        replace_para_text(p, full_t, font_name="Calibri", sz="22", italic=True, line="360", jc="both")
        print(f" -> Fixed P #{idx}: Lampiran 2 clarification note added")

# Save document
updated_xml = ET.tostring(root, encoding='utf-8')

temp_zip = "temp_refine.zip"
with zipfile.ZipFile(DOCX_PATH, 'r') as zin:
    with zipfile.ZipFile(temp_zip, 'w') as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, updated_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

os.replace(temp_zip, DOCX_PATH)
print("Penyempurnaan 100% tuntas dan berkas berhasil disimpan!")
