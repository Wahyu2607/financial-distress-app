import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

PPTX_PATH = "skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND.pptx"
PPTX_BACKUP = "skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx"
TEMP_DIR = "skripsi_research/scratch/pptx_unpack"

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"
A14_NS = "http://schemas.microsoft.com/office/drawing/2010/main"
A16_NS = "http://schemas.microsoft.com/office/drawing/2014/main"

for prefix, uri in [
    ('p', P_NS), ('a', A_NS), ('r', R_NS), ('m', M_NS),
    ('mc', MC_NS), ('p14', P14_NS), ('a14', A14_NS), ('a16', A16_NS)
]:
    ET.register_namespace(prefix, uri)

def make_r(text, bold=False, italic=False, size=None, color=None, scheme=None):
    r = ET.Element(f"{{{A_NS}}}r")
    rPr = ET.SubElement(r, f"{{{A_NS}}}rPr", lang="en-US", dirty="0")
    if bold:
        rPr.set("b", "1")
    if italic:
        rPr.set("i", "1")
    if size:
        rPr.set("sz", str(size))
    
    solidFill = ET.SubElement(rPr, f"{{{A_NS}}}solidFill")
    if color:
        ET.SubElement(solidFill, f"{{{A_NS}}}srgbClr", val=color)
    elif scheme:
        ET.SubElement(solidFill, f"{{{A_NS}}}schemeClr", val=scheme)
    else:
        ET.SubElement(solidFill, f"{{{A_NS}}}schemeClr", val="bg1")
        
    ET.SubElement(rPr, f"{{{A_NS}}}latin", typeface="Arial")
    ET.SubElement(rPr, f"{{{A_NS}}}cs", typeface="Arial")
    
    t = ET.SubElement(r, f"{{{A_NS}}}t")
    t.text = text
    return r

def make_p(runs, align="l", space_after=600, line_spacing=120000):
    p = ET.Element(f"{{{A_NS}}}p")
    pPr = ET.SubElement(p, f"{{{A_NS}}}pPr", algn=align)
    if space_after:
        spcAft = ET.SubElement(pPr, f"{{{A_NS}}}spcAft")
        ET.SubElement(spcAft, f"{{{A_NS}}}spcPts", val=str(space_after))
    if line_spacing:
        lnSpc = ET.SubElement(pPr, f"{{{A_NS}}}lnSpc")
        ET.SubElement(lnSpc, f"{{{A_NS}}}spcPct", val=str(line_spacing))
        
    for item in runs:
        if isinstance(item, tuple):
            text = item[0]
            bold = item[1] if len(item) > 1 else False
            size = item[2] if len(item) > 2 else None
            color = item[3] if len(item) > 3 else None
            scheme = item[4] if len(item) > 4 else None
            p.append(make_r(text, bold=bold, size=size, color=color, scheme=scheme))
        else:
            p.append(item)
            
    endParaRPr = ET.SubElement(p, f"{{{A_NS}}}endParaRPr", lang="en-ID", dirty="0")
    ET.SubElement(endParaRPr, f"{{{A_NS}}}latin", typeface="Arial")
    ET.SubElement(endParaRPr, f"{{{A_NS}}}cs", typeface="Arial")
    fill = ET.SubElement(endParaRPr, f"{{{A_NS}}}solidFill")
    ET.SubElement(fill, f"{{{A_NS}}}schemeClr", val="bg1")
    return p

def set_shape_text(sp, paragraphs_runs, align="l", default_space_after=600):
    txBody = sp.find(f"{{{P_NS}}}txBody")
    if txBody is None:
        txBody = ET.SubElement(sp, f"{{{P_NS}}}txBody")
        ET.SubElement(txBody, f"{{{A_NS}}}bodyPr")
        ET.SubElement(txBody, f"{{{A_NS}}}lstStyle")
    else:
        for p in list(txBody.findall(f"{{{A_NS}}}p")):
            txBody.remove(p)
            
    for p_runs in paragraphs_runs:
        txBody.append(make_p(p_runs, align=align, space_after=default_space_after))

def create_textbox_shape(shape_id, shape_name, x, y, cx, cy, paragraphs_runs, bg_color=None, border_color=None, align="l", default_space_after=400):
    sp = ET.Element(f"{{{P_NS}}}sp")
    nvSpPr = ET.SubElement(sp, f"{{{P_NS}}}nvSpPr")
    ET.SubElement(nvSpPr, f"{{{P_NS}}}cNvPr", id=str(shape_id), name=shape_name)
    ET.SubElement(nvSpPr, f"{{{P_NS}}}cNvSpPr", txBox="1")
    ET.SubElement(nvSpPr, f"{{{P_NS}}}nvPr")
    
    spPr = ET.SubElement(sp, f"{{{P_NS}}}spPr")
    xfrm = ET.SubElement(spPr, f"{{{A_NS}}}xfrm")
    ET.SubElement(xfrm, f"{{{A_NS}}}off", x=str(x), y=str(y))
    ET.SubElement(xfrm, f"{{{A_NS}}}ext", cx=str(cx), cy=str(cy))
    
    prstGeom = ET.SubElement(spPr, f"{{{A_NS}}}prstGeom", prst="roundRect" if bg_color else "rect")
    ET.SubElement(prstGeom, f"{{{A_NS}}}avLst")
    if bg_color:
        solidFill = ET.SubElement(spPr, f"{{{A_NS}}}solidFill")
        ET.SubElement(solidFill, f"{{{A_NS}}}srgbClr", val=bg_color)
    else:
        ET.SubElement(spPr, f"{{{A_NS}}}noFill")
        
    if border_color:
        ln = ET.SubElement(spPr, f"{{{A_NS}}}ln", w="19050")
        lnFill = ET.SubElement(ln, f"{{{A_NS}}}solidFill")
        ET.SubElement(lnFill, f"{{{A_NS}}}srgbClr", val=border_color)
    
    txBody = ET.SubElement(sp, f"{{{P_NS}}}txBody")
    bodyPr = ET.SubElement(txBody, f"{{{A_NS}}}bodyPr", wrap="square", rtlCol="0")
    if bg_color:
        bodyPr.set("lIns", "182880")
        bodyPr.set("tIns", "146304")
        bodyPr.set("rIns", "182880")
        bodyPr.set("bIns", "146304")
    ET.SubElement(txBody, f"{{{A_NS}}}lstStyle")
    
    for p_runs in paragraphs_runs:
        txBody.append(make_p(p_runs, align=align, space_after=default_space_after))
        
    return sp

# Unpack from pristine backup
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
with zipfile.ZipFile(PPTX_BACKUP, 'r') as z:
    z.extractall(TEMP_DIR)
print(f"Unpacked {PPTX_BACKUP} to {TEMP_DIR}")

# Process Slide 1
s1_path = os.path.join(TEMP_DIR, "ppt/slides/slide1.xml")
t1 = ET.parse(s1_path)
spTree1 = t1.find(".//p:spTree", {"p": P_NS})
for sp in spTree1.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [
            [
                ("Prediksi Financial Distress pada Industri Manufaktur yang Terdaftar di Bursa Efek Indonesia ", True, 2600, "FFFFFF"),
                ("dengan Pendekatan Model Extreme Gradient Boosting dan Altman Z-Score", True, 2400, "FF4B4B")
            ]
        ], align="l", default_space_after=400)
    elif name == "Subtitle 2":
        set_shape_text(sp, [
            [("Wahyu Pamungkas ", True, 1700, "FFFFFF"), ("(NIM: 535220037)", True, 1600, "FFD700")],
            [("Dosen Pembimbing Utama: ", False, 1400, "CCCCCC"), ("Pak Tony, S.Kom., M.Kom., Ph.D.", True, 1400, "FFFFFF")],
            [("Dosen Pembimbing Pendamping: ", False, 1400, "CCCCCC"), ("Pak Arnold Kaudin, S.E., M.M., M.Com., Ph.D.", True, 1400, "FFFFFF")],
            [("Program Studi Sarjana Teknik Informatika | Fakultas Teknologi Informasi | Universitas Tarumanagara", False, 1300, "AAAAAA")],
            [("Jakarta, 16 November 2026", True, 1300, "FF4B4B")]
        ], align="l", default_space_after=250)
t1.write(s1_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 1.")

# Process Slide 2
s2_path = os.path.join(TEMP_DIR, "ppt/slides/slide2.xml")
t2 = ET.parse(s2_path)
spTree2 = t2.find(".//p:spTree", {"p": P_NS})
for sp in spTree2.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("AGENDA PRESENTASI SIDANG SKRIPSI (10 MENIT)", True, 2800, "FFFFFF")]])
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [("1. Latar Belakang & Urgensi: ", True, 1500, "FF4B4B"), ("Peran pilar industri manufaktur BEI, risiko financial distress, & asimetri informasi pasar modal.", False, 1450, "FFFFFF")],
            [("2. Gap Perancangan: ", True, 1500, "FF4B4B"), ("Kelemahan linearitas model klasik, severe class imbalance (1:11,40), & relevansi koefisien empiris lokal.", False, 1450, "FFFFFF")],
            [("3. Solusi Multi-Metodologi: ", True, 1500, "FF4B4B"), ("Sinergi Altman Z'' 1995, MDA Fisher BEI, XGBoost Classifier, & 4 rasio fundamental.", False, 1450, "FFFFFF")],
            [("4. Prapemrosesan Data: ", True, 1500, "FF4B4B"), ("Panel 3.770 observasi (2014–2026), taksonomi 13 pos XBRL, neraca akuntansi, & capping X4 <= 3.0.", False, 1450, "FFFFFF")],
            [("5. Formulasi & Komputasi: ", True, 1500, "FF4B4B"), ("Detail matematis Altman Z'', re-estimasi koefisien Fisher BEI, & arsitektur pohon XGBoost.", False, 1450, "FFFFFF")],
            [("6. Evaluasi & Validasi Model: ", True, 1500, "FF4B4B"), ("Hold-out 754 sampel (Akurasi 96,42%, ROC-AUC 0,9400) & Stratified 3-Fold CV (Akurasi 97,35%).", False, 1450, "FFFFFF")],
            [("7. Implementasi Sistem & Kesimpulan: ", True, 1500, "FF4B4B"), ("Dasbor web Streamlit, validasi ahli (94,50%), pengujian UAT (88,60%), & rekomendasi.", False, 1450, "FFFFFF")]
        ], default_space_after=350)
t2.write(s2_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 2.")

# Process Slide 3
s3_path = os.path.join(TEMP_DIR, "ppt/slides/slide3.xml")
t3 = ET.parse(s3_path)
spTree3 = t3.find(".//p:spTree", {"p": P_NS})
for sp in spTree3.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("LATAR BELAKANG & URGENSI PENELITIAN", True, 2800, "FFFFFF")]])
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [
                ("• Peran Strategis Industri Manufaktur BEI: ", True, 1550, "FFD700"),
                ("Sebagai tulang punggung PDB nasional yang berkarakteristik padat modal (capital intensive) dengan siklus kas panjang, sektor manufaktur sangat rentan terhadap guncangan makroekonomi, lonjakan harga bahan baku, dan fluktuasi suku bunga.", False, 1500, "FFFFFF")
            ],
            [
                ("• Ancaman Krisis Financial Distress: ", True, 1550, "FF4B4B"),
                ("Penurunan likuiditas dan pelemahan laba operasi yang tidak diantisipasi dini dapat bereskalasi menjadi gagal bayar utang, restrukturisasi PKPU di pengadilan niaga, suspensi perdagangan, hingga delisting paksa (forced delisting).", False, 1500, "FFFFFF")
            ],
            [
                ("• Asimetri Informasi & Dampak Kerugian Investor: ", True, 1550, "FFD700"),
                ("Kegagalan mendeteksi kebangkrutan menimbulkan direct capital default loss yang fatal bagi investor dan kreditur perbankan. Kerugian akibat Type II Error (gagal deteksi) jauh lebih masif dibanding Type I Error (false alarm).", False, 1500, "FFFFFF")
            ],
            [
                ("• Kebutuhan Early Warning System Otomatis: ", True, 1550, "00E5FF"),
                ("Dibutuhkan instrumen Sistem Pendukung Keputusan (DSS) cerdas yang objektif, real-time, dan mampu mengintegrasikan data bursa untuk memberikan sinyal peringatan dini kesehatan finansial emiten.", False, 1500, "FFFFFF")
            ]
        ], default_space_after=450)
t3.write(s3_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 3.")

# Process Slide 4
s4_path = os.path.join(TEMP_DIR, "ppt/slides/slide4.xml")
t4 = ET.parse(s4_path)
spTree4 = t4.find(".//p:spTree", {"p": P_NS})
for sp in spTree4.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("GAP PERANCANGAN & RUMUSAN MASALAH", True, 2800, "FFFFFF")]])
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [
                ("1. Keterbatasan Linearitas Model Klasik: ", True, 1550, "FF4B4B"),
                ("Formula Altman dan MDA konvensional mengasumsikan hubungan aditif linear dan normalitas multivariat, padahal interaksi risiko finansial di pasar negara berkembang bersifat non-linear, asimetris, dan dinamis.", False, 1450, "FFFFFF")
            ],
            [
                ("2. Masalah Ketimpangan Kelas Ekstrem (Severe Class Imbalance): ", True, 1550, "FFD700"),
                ("Pada bursa BEI, emiten sehat jauh mendominasi emiten bangkrut dengan rasio ketimpangan mencapai 1 : 11,40. Model tanpa pembobotan menghasilkan bias mayoritas tinggi dan meloloskan banyak kasus kebangkrutan (False Negative).", False, 1450, "FFFFFF")
            ],
            [
                ("3. Kesenjangan Relevansi Koefisien Asing: ", True, 1550, "00E5FF"),
                ("Koefisien Altman asli (1968/1995) diturunkan dari karakteristik pasar modal Amerika Serikat. Diperlukan kalibrasi empiris koefisien MDA yang mencerminkan profil struktur permodalan emiten manufaktur BEI.", False, 1450, "FFFFFF")
            ],
            [
                ("4. Kesenjangan Teoretis ke Implementasi Praktis: ", True, 1550, "00FF7F"),
                ("Kajian akademis sering terisolasi pada rumus manual statis; praktisi bursa membutuhkan Decision Support System (DSS) berbasis web interaktif dengan pipeline otomatis dari pembacaan laporan XBRL/PDF hingga simulasi restrukturisasi What-If.", False, 1450, "FFFFFF")
            ]
        ], default_space_after=450)
t4.write(s4_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 4.")

# Process Slide 5
s5_path = os.path.join(TEMP_DIR, "ppt/slides/slide5.xml")
t5 = ET.parse(s5_path)
spTree5 = t5.find(".//p:spTree", {"p": P_NS})
for sp in spTree5.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("SOLUSI: SINERGI TIGA PENDEKATAN KOMPARATIF", True, 2800, "FFFFFF")]])
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [
                ("• Komparasi 3 Pilar Metodologi Finansial & AI: ", True, 1550, "FFD700"),
                ("Menyandingkan secara simultan (1) Altman Z''-Score 1995 (baseline emerging market), (2) MDA Fisher Koefisien Baru BEI hasil re-estimasi empiris, dan (3) XGBoost Classifier sebagai model adaptif non-linear.", False, 1450, "FFFFFF")
            ],
            [
                ("• 4 Rasio Keuangan Fundamental Pembentuk Model (Altman Framework): ", True, 1550, "00E5FF"),
                ("\n  - X1 (WCTA): Likuiditas bersih modal kerja terhadap total aset.", False, 1400, "FFFFFF"),
                ("\n  - X2 (RETA): Akumulasi laba ditahan (profitabilitas kumulatif & usia produktif emiten).", False, 1400, "FFFFFF"),
                ("\n  - X3 (EBITTA): Produktivitas operasional murni aset sebelum beban bunga dan pajak.", False, 1400, "FFFFFF"),
                ("\n  - X4 (CETL): Solvabilitas struktur permodalan (Ekuitas Saham / Total Liabilitas).", False, 1400, "FFFFFF")
            ],
            [
                ("• Keunggulan Extreme Gradient Boosting (XGBoost): ", True, 1550, "FF4B4B"),
                ("Mampu menangkap interaksi non-linear kompleks antar rasio, dilengkapi regularisasi penalti kompleksitas pohon (L1/L2), dan pembobotan kelas minoritas otomatis (scale_pos_weight = 11,38) untuk menekan Type II Error.", False, 1450, "FFFFFF")
            ],
            [
                ("• Mekanisme Stabilisasi Rasio (Capping X4 <= 3.0): ", True, 1550, "00FF7F"),
                ("Menerapkan pembatasan nilai ekuitas/liabilitas maksimum 3.0 untuk meredam distorsi skor semu pada emiten dengan liabilitas mendekati nol.", False, 1450, "FFFFFF")
            ]
        ], default_space_after=400)
t5.write(s5_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 5.")

# Process Slide 6
s6_path = os.path.join(TEMP_DIR, "ppt/slides/slide6.xml")
t6 = ET.parse(s6_path)
spTree6 = t6.find(".//p:spTree", {"p": P_NS})
for sp in spTree6.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("ALUR IMPLEMENTASI & PIPELINE KOMPUTASI", True, 2800, "FFFFFF")]])
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [
                ("1. Prapemrosesan & Normalisasi Data: ", True, 1550, "FF4B4B"),
                ("Parsing multi-sumber (XBRL IDX, Excel, PDF, Yahoo Finance API), konversi Rupiah penuh, penyeimbangan neraca otomatis (Aset = Liabilitas + Ekuitas), dan pembatasan ekstrem capping X4 <= 3.0.", False, 1450, "FFFFFF")
            ],
            [
                ("2. Pipeline Altman Z''-Score (1995): ", True, 1550, "FFD700"),
                ("Perhitungan rasio X1-X4, pembobotan formula Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4, dan pemetaan 3 zona kesehatan (Safe > 2.60, Grey 1.10 - 2.60, Distress <= 1.10).", False, 1450, "FFFFFF")
            ],
            [
                ("3. Pipeline MDA Fisher Koefisien Baru BEI: ", True, 1550, "00E5FF"),
                ("Estimasi matriks kovarians gabungan pooled (Sw), invers matriks (Sw^-1), pembentukan koefisien empiris BEI, dan klasifikasi objektif titik potong centroid Fisher (Cut-off = 0.3844).", False, 1450, "FFFFFF")
            ],
            [
                ("4. Pipeline Machine Learning XGBoost: ", True, 1550, "00FF7F"),
                ("Pembagian Stratified Hold-out 80:20 & 3-Fold CV, pembobotan gradien-hessian loss logistik, ensemble decision trees regularisasi, dan inferensi probabilitas sigmoid p = 1 / (1 + e^-y).", False, 1450, "FFFFFF")
            ]
        ], default_space_after=450)
t6.write(s6_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 6.")

# Process Slide 7
s7_path = os.path.join(TEMP_DIR, "ppt/slides/slide7.xml")
t7 = ET.parse(s7_path)
spTree7 = t7.find(".//p:spTree", {"p": P_NS})
for sp in spTree7.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("PRAPEMROSESAN DATA: DATASET PANEL BEI", True, 2800, "FFFFFF")]])
    elif name == "TextBox 15":
        set_shape_text(sp, [
            [
                ("• Dataset Panel Empiris: ", True, 1300, "FFD700"),
                ("3.770 observasi laporan keuangan (2014–2026) mencakup 290 emiten manufaktur Bursa Efek Indonesia. | ", False, 1250, "FFFFFF"),
                ("13 Pos Keuangan Baku: ", True, 1300, "00E5FF"),
                ("EBIT, Interest, TA, CA, TL, CL, CE, RE, WC, CFO, Revenue, Net Income, Debt.", False, 1250, "FFFFFF")
            ]
        ], default_space_after=100)
t7.write(s7_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 7.")

# Process Slide 8
s8_path = os.path.join(TEMP_DIR, "ppt/slides/slide8.xml")
t8 = ET.parse(s8_path)
spTree8 = t8.find(".//p:spTree", {"p": P_NS})
for sp in spTree8.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("REKAYASA FITUR & MEKANISME CAPPING RASIO", True, 2800, "FFFFFF")]])

card8 = create_textbox_shape(
    shape_id=208,
    shape_name="Card Flow Explanation",
    x=711340, y=2750000, cx=10769320, cy=3500000,
    paragraphs_runs=[
        [
            ("1. Ekstraksi & Penyesuaian Format: ", True, 1500, "FFD700"),
            ("Mengonversi laporan keuangan dari multi-format (XBRL IDX, CSV, Excel, PDF laporan tahunan, dan Yahoo Finance API) ke dalam nilai Rupiah penuh terstandarisasi.", False, 1400, "FFFFFF")
        ],
        [
            ("2. Pembersihan & Persamaan Akuntansi: ", True, 1500, "00E5FF"),
            ("Mengisi otomatis pos yang hilang via persamaan neraca baku: Modal Kerja = Aset Lancar - Liabilitas Lancar; dan Total Liabilitas = Aset - Ekuitas, mencegah hilangnya baris data.", False, 1400, "FFFFFF")
        ],
        [
            ("3. Mekanisme Capping X4 <= 3.0 (Aturan Edward I. Altman): ", True, 1500, "FF4B4B"),
            ("Rasio X4 = Ekuitas / Total Liabilitas. Jika suatu emiten memiliki utang sangat kecil (liabilitas mendekati 0), nilai X4 dapat melonjak liar (15.0 hingga 50.0). Tanpa pembatasan, emiten tersebut otomatis masuk Zona Aman semu meskipun kinerja operasionalnya sedang rugi berat (EBIT < 0). Altman menetapkan batas 3.0 untuk menstabilkan model.", False, 1400, "FFFFFF")
        ],
        [
            ("4. Strukturisasi & Standarisasi Fitur: ", True, 1500, "00FF7F"),
            ("Menghasilkan 4 variabel rasio terkalibrasi (X1-X4) yang siap diumpankan ke model diskriminan parametrik (Altman & MDA) serta algoritma machine learning (XGBoost).", False, 1400, "FFFFFF")
        ]
    ],
    bg_color="181B22",
    border_color="FF4B4B",
    default_space_after=350
)
spTree8.append(card8)
t8.write(s8_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 8.")

# Process Slide 9
s9_path = os.path.join(TEMP_DIR, "ppt/slides/slide9.xml")
t9 = ET.parse(s9_path)
spTree9 = t9.find(".//p:spTree", {"p": P_NS})
for sp in spTree9.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("FORMULASI MODEL ALTMAN Z''-SCORE (1995)", True, 2800, "FFFFFF")]])

card9 = create_textbox_shape(
    shape_id=209,
    shape_name="Card Altman Formula",
    x=711340, y=1650000, cx=10769320, cy=4600000,
    paragraphs_runs=[
        [
            ("Persamaan Altman Z''-Score Modifikasi Emerging Market (1995):", True, 1700, "FFD700")
        ],
        [
            ("Z'' = 6.56 × X1 + 3.26 × X2 + 6.72 × X3 + 1.05 × X4", True, 2000, "00E5FF")
        ],
        [
            ("Definisi Empat Rasio Keuangan Pembentuk Model:", True, 1550, "FFFFFF")
        ],
        [
            ("• X1 = Working Capital / Total Assets : ", True, 1450, "FFD700"),
            ("Mengukur likuiditas modal kerja bersih relatif terhadap total kapasitas aset.", False, 1400, "FFFFFF")
        ],
        [
            ("• X2 = Retained Earnings / Total Assets : ", True, 1450, "FFD700"),
            ("Mengukur profitabilitas kumulatif yang ditahan serta mencerminkan usia produktif emiten.", False, 1400, "FFFFFF")
        ],
        [
            ("• X3 = EBIT / Total Assets : ", True, 1450, "FFD700"),
            ("Mengukur produktivitas aset riil dalam menghasilkan laba operasional murni sebelum beban bunga dan pajak.", False, 1400, "FFFFFF")
        ],
        [
            ("• X4 = Common Stock Equity / Total Liabilities : ", True, 1450, "FFD700"),
            ("Mengukur solvabilitas dan daya tahan modal pemilik dalam melindungi utang (Dibatasi Maksimum 3.0).", False, 1400, "FFFFFF")
        ],
        [
            ("Kriteria Ambang Batas Zonasi Finansial Klasik:", True, 1550, "FFFFFF")
        ],
        [
            ("• Z'' <= 1.10 : ", True, 1500, "FF4B4B"),
            ("Zona Distress (Risiko Sangat Tinggi Kebangkrutan / Tekanan Solvabilitas Kritis)", False, 1400, "FFFFFF")
        ],
        [
            ("• 1.10 < Z'' < 2.60 : ", True, 1500, "FFD700"),
            ("Zona Abu-Abu (Grey Area / Kondisi Rentan yang Memerlukan Pemantauan Intensif)", False, 1400, "FFFFFF")
        ],
        [
            ("• Z'' >= 2.60 : ", True, 1500, "00FF7F"),
            ("Zona Aman (Safe Zone / Struktur Permodalan Sehat, Likuid, dan Solven)", False, 1400, "FFFFFF")
        ],
        [
            ("Catatan Metodologi: ", True, 1350, "AAAAAA"),
            ("Variabel X5 (Sales/TA) dari model 1968 sengaja dieliminasi oleh Altman agar model adil diterapkan pada industri manufaktur padat modal di negara berkembang (emerging market).", False, 1300, "AAAAAA")
        ]
    ],
    bg_color="181B22",
    border_color="00E5FF",
    default_space_after=220
)
spTree9.append(card9)
t9.write(s9_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 9.")

# Process Slide 10
s10_path = os.path.join(TEMP_DIR, "ppt/slides/slide10.xml")
t10 = ET.parse(s10_path)
spTree10 = t10.find(".//p:spTree", {"p": P_NS})
for sp in spTree10.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("SIMULASI PERHITUNGAN ALTMAN Z'' (KASUS EMITEN AALI)", True, 2800, "FFFFFF")]])
    elif name == "TextBox 16":
        set_shape_text(sp, [[("Tabel Hasil Perhitungan Rasio X pada PT Astra Agro Lestari Tbk (Kode: AALI)", True, 1450, "FFD700")]])
    elif name == "TextBox 15":
        set_shape_text(sp, [
            [
                ("• Hasil Evaluasi: ", True, 1500, "00FF7F"),
                ("Emiten AALI terklasifikasi sebagai NON-DISTRESS (Kondisi Sangat Sehat).", True, 1500, "FFFFFF")
            ],
            [
                ("• Perbandingan Capping: ", True, 1450, "FFD700"),
                ("Tanpa capping Z'' = 13,00; dengan capping X4 = 3,0 menghasilkan Z'' = 7,59. Keduanya jauh melampaui cut-off 2,60 (Safe Zone). Capping membuktikan model stabil tanpa mengubah esensi klasifikasi.", False, 1350, "FFFFFF")
            ]
        ], default_space_after=250)
t10.write(s10_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 10.")

# Process Slide 11
s11_path = os.path.join(TEMP_DIR, "ppt/slides/slide11.xml")
t11 = ET.parse(s11_path)
spTree11 = t11.find(".//p:spTree", {"p": P_NS})
for sp in spTree11.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("MULTIPLE DISCRIMINANT ANALYSIS (MDA) FISHER BEI", True, 2800, "FFFFFF")]])

card11 = create_textbox_shape(
    shape_id=211,
    shape_name="Card MDA Explanation",
    x=726941, y=2500000, cx=10626859, cy=3800000,
    paragraphs_runs=[
        [
            ("1. Metodologi Rekalibrasi Empiris Fisher BEI: ", True, 1550, "FFD700"),
            ("Membagi sampel data panel menjadi dua kelompok: Distress (N1 = 63) dan Non-Distress (N2 = 639), kemudian menghitung matriks kovarians gabungan (pooled covariance matrix Sw) dan vektor selisih rata-rata (d = mean1 - mean2).", False, 1400, "FFFFFF")
        ],
        [
            ("2. Formula Baru Hasil Re-estimasi Empiris BEI:", True, 1550, "00E5FF")
        ],
        [
            ("Z' = 6.1120 × X1 + 3.2776 × X2 + 4.8373 × X3 + 0.0430 × X4", True, 1850, "00FF7F")
        ],
        [
            ("3. Titik Potong Objektif (Centroid Cut-off Fisher): ", True, 1550, "FFD700"),
            ("Cut-off = (Z_distress_mean + Z_nondistress_mean) / 2 = (-2.4502 + 3.2189) / 2 = ", False, 1400, "FFFFFF"),
            ("0.3844", True, 1500, "FF4B4B")
        ],
        [
            ("   • Jika Z' < 0.3844 -> Terindikasi FINANCIAL DISTRESS | Jika Z' >= 0.3844 -> NON-DISTRESS (SEHAT).", True, 1400, "FFFFFF")
        ],
        [
            ("4. Temuan Empiris Finansial Pasar Modal Indonesia: ", True, 1550, "FF4B4B"),
            ("Koefisien X1 (6.1120) dan X3 (4.8373) memiliki bobot diskriminasi paling dominan, membuktikan bahwa modal kerja likuid dan produktivitas laba operasional riil merupakan bantalan penyelamat paling krusial bagi emiten manufaktur di Indonesia.", False, 1400, "FFFFFF")
        ]
    ],
    bg_color="181B22",
    border_color="00E5FF",
    default_space_after=280
)
spTree11.append(card11)
t11.write(s11_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 11.")

# Process Slide 12
s12_path = os.path.join(TEMP_DIR, "ppt/slides/slide12.xml")
t12 = ET.parse(s12_path)
spTree12 = t12.find(".//p:spTree", {"p": P_NS})
for sp in spTree12.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("PEMODELAN MACHINE LEARNING XGBOOST CLASSIFIER", True, 2800, "FFFFFF")]])

card12 = create_textbox_shape(
    shape_id=212,
    shape_name="Card XGBoost Explanation",
    x=561645, y=2450000, cx=11068710, cy=3850000,
    paragraphs_runs=[
        [
            ("1. Arsitektur Gradient Tree Boosting Adaptif: ", True, 1550, "FFD700"),
            ("Membangun ensemble decision trees secara sekuensial dengan meminimalkan fungsi loss logistik biner ter-regularisasi melalui ekspansi deret Taylor orde kedua (gradien gi dan hessian hi pada setiap iterasi pembentukan split pohon).", False, 1400, "FFFFFF")
        ],
        [
            ("2. Penanganan Severe Class Imbalance (1 : 11,40): ", True, 1550, "FF4B4B"),
            ("Menerapkan pembobotan kelas minoritas otomatis scale_pos_weight = 11,38. Bobot ini memaksa algoritma memprioritaskan sensitivitas deteksi distress sehingga secara drastis menekan Type II Error (False Negative).", False, 1400, "FFFFFF")
        ],
        [
            ("3. Hyperparameter Optimal Hasil Validasi Silang: ", True, 1550, "00E5FF"),
            ("n_estimators = 100, max_depth = 3 (mencegah pohon terlalu kompleks/overfitting), learning_rate = 0.08 (langkah koreksi stabil), subsample = 0.85, colsample_bytree = 0.85.", False, 1400, "FFFFFF")
        ],
        [
            ("4. Feature Importance & Kecepatan Komputasi Riil: ", True, 1550, "00FF7F"),
            ("Fitur X2 (Retained Earnings/TA, 44,2%) dan X3 (EBIT/TA, 28,1%) terbukti menjadi prediktor paling signifikan. Menghasilkan latensi inferensi ultra-ringan hanya 0,85 milidetik per sampel emiten, sangat optimal untuk skrining massal pasar modal.", False, 1400, "FFFFFF")
        ]
    ],
    bg_color="181B22",
    border_color="FF4B4B",
    default_space_after=280
)
spTree12.append(card12)
t12.write(s12_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 12.")

# Process Slide 13
s13_path = os.path.join(TEMP_DIR, "ppt/slides/slide13.xml")
t13 = ET.parse(s13_path)
spTree13 = t13.find(".//p:spTree", {"p": P_NS})
for sp in spTree13.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("EVALUASI MODEL & BENCHMARK MULTI-MODEL", True, 2800, "FFFFFF")]])

# Populate Table 5 on Slide 13
tbl = spTree13.find(".//a:tbl", {"a": A_NS})
if tbl is not None:
    rows = tbl.findall("a:tr", {"a": A_NS})
    table_data = [
        [("Model Finansial", True, 1400, "FFD700"), ("F1-Score", True, 1400, "FFD700"), ("Macro F1", True, 1400, "FFD700"), ("Weighted F1", True, 1400, "FFD700"), ("Youden’s J", True, 1400, "FFD700"), ("Akurasi", True, 1400, "FFD700"), ("ROC-AUC", True, 1400, "FFD700")],
        [("Altman Z''-Score (1995)", True, 1300, "FFFFFF"), ("74,60%", False, 1300, "FFFFFF"), ("86,14%", False, 1300, "FFFFFF"), ("95,82%", False, 1300, "FFFFFF"), ("0,7445", False, 1300, "FFFFFF"), ("95,76%", False, 1300, "FFFFFF"), ("0,9000", False, 1300, "FFFFFF")],
        [("MDA Fisher (Koef. Baru BEI)", True, 1300, "00E5FF"), ("76,56%", False, 1300, "00E5FF"), ("87,19%", False, 1300, "00E5FF"), ("96,11%", False, 1300, "00E5FF"), ("0,7773", False, 1300, "00E5FF"), ("96,02%", False, 1300, "00E5FF"), ("0,9167", False, 1300, "00E5FF")],
        [("XGBoost Classifier (Champion)", True, 1350, "FF4B4B"), ("78,40%", True, 1350, "00FF7F"), ("88,22%", True, 1350, "00FF7F"), ("96,46%", True, 1350, "00FF7F"), ("0,7816", True, 1350, "00FF7F"), ("96,42%", True, 1350, "00FF7F"), ("0,9400", True, 1350, "00FF7F")]
    ]
    for r_idx, r_data in enumerate(table_data):
        row_elem = rows[r_idx]
        tcs = row_elem.findall("a:tc", {"a": A_NS})
        for c_idx, cell_data in enumerate(r_data):
            tc = tcs[c_idx]
            txBody = tc.find(f"{{{A_NS}}}txBody")
            for p in list(txBody.findall(f"{{{A_NS}}}p")):
                txBody.remove(p)
            text, bold, size, color = cell_data
            txBody.append(make_p([(text, bold, size, color)], align="ctr" if c_idx > 0 else "l", space_after=100))

card13 = create_textbox_shape(
    shape_id=213,
    shape_name="Card KFold3 Evaluation",
    x=838200, y=4400000, cx=10515596, cy=1850000,
    paragraphs_runs=[
        [
            ("• Superioritas XGBoost Classifier (Champion Model): ", True, 1450, "FF4B4B"),
            ("Meraih performa tertinggi pada seluruh metrik utama evaluasi (Akurasi 96,42%, ROC-AUC 0,9400, F1-Score 78,40%, dan Youden's J 0,7816) serta paling efektif menekan False Negative (hanya 12 kasus pada data uji 754 sampel).", False, 1350, "FFFFFF")
        ],
        [
            ("• Validasi Silang Stratified 3-Fold Cross Validation (K=3):", True, 1450, "FFD700")
        ],
        [
            ("   - Rata-rata Akurasi: ", True, 1350, "00E5FF"), ("97,35% ± 0,24%  |  ", False, 1350, "FFFFFF"),
            ("Rata-rata ROC-AUC: ", True, 1350, "00E5FF"), ("0,9681 ± 0,0107  |  ", False, 1350, "FFFFFF"),
            ("Rata-rata Recall (Sensitivitas): ", True, 1350, "00E5FF"), ("91,46% ± 2,79%", False, 1350, "FFFFFF")
        ],
        [
            ("   - Rata-rata F1-Score: ", True, 1350, "00FF7F"), ("84,75% ± 1,45%  |  ", False, 1350, "FFFFFF"),
            ("Selisih Rata-rata Akurasi Latih (97,94%) vs Uji (97,35%): ", True, 1350, "FFD700"), ("hanya 0,59% (Terbukti Bebas Overfitting)", True, 1350, "00FF7F")
        ]
    ],
    bg_color="181B22",
    border_color="FFD700",
    default_space_after=180
)
spTree13.append(card13)
t13.write(s13_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 13.")

# Process Slide 14
s14_path = os.path.join(TEMP_DIR, "ppt/slides/slide14.xml")
t14 = ET.parse(s14_path)
spTree14 = t14.find(".//p:spTree", {"p": P_NS})
for sp in spTree14.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("KESIMPULAN, VALIDASI SISTEM & PENUTUP", True, 2600, "FFFFFF")]])
    elif name == "Subtitle 2":
        set_shape_text(sp, [
            [
                ("1. XGBoost Sebagai Champion Model: ", True, 1400, "00FF7F"),
                ("Terbukti paling unggul memetakan risiko non-linear pasar modal BEI (F1 78,40%, ROC-AUC 0,9400, Akurasi 96,42%) serta paling aman bagi investor karena menekan Type II Error (False Negative) secara maksimal.", False, 1300, "FFFFFF")
            ],
            [
                ("2. Keberhasilan Rekalibrasi Empiris MDA Fisher BEI: ", True, 1400, "00E5FF"),
                ("Koefisien diskriminan baru ber-cut-off 0.3844 terbukti lebih presisi (F1 76,56%) dibanding formula Altman klasik (F1 74,60%) untuk emiten di pasar modal Indonesia.", False, 1300, "FFFFFF")
            ],
            [
                ("3. Kinerja Sistem Pendukung Keputusan Berbasis Web (Streamlit): ", True, 1400, "FFD700"),
                ("Menyediakan integrasi multi-sumber, dekomposisi pemicu krisis, checklist peringatan dini, dan simulator What-If titik impas restrukturisasi.", False, 1300, "FFFFFF")
            ],
            [
                ("   • Skor Validasi Ahli: ", True, 1350, "FFD700"), ("94,50% (Sangat Layak)  |  ", False, 1300, "FFFFFF"),
                ("Skor Pengujian Penerimaan Pengguna (UAT): ", True, 1350, "00FF7F"), ("88,60% (Sangat Baik)", False, 1300, "FFFFFF")
            ],
            [
                ("Terima kasih atas perhatian Dewan Penguji & Dosen Pembimbing.", True, 1400, "FFFFFF")
            ],
            [
                ("Wahyu Pamungkas (NIM: 535220037) | Pembimbing: Pak Tony & Pak Arnold Kaudin | Universitas Tarumanagara", False, 1200, "AAAAAA")
            ]
        ], default_space_after=200)
t14.write(s14_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 14.")

# Post-processing: Ensure 100% Arial across all slides and fix remaining equation typos
import re
for i in range(1, 15):
    slide_file = os.path.join(TEMP_DIR, f"ppt/slides/slide{i}.xml")
    if os.path.exists(slide_file):
        with open(slide_file, "r", encoding="utf-8") as f:
            content = f.read()
        if i == 9:
            content = content.replace("𝐶𝑢𝑟𝑟𝑟𝑒𝑛𝑡", "𝐶𝑢𝑟𝑟𝑒𝑛𝑡")
            content = content.replace("𝐶𝑎𝑚𝑚𝑜𝑛", "𝐶𝑜𝑚𝑚𝑜𝑛")
            content = content.replace("𝐸𝑞𝑢𝑡𝑦", "𝐸𝑞𝑢𝑖𝑡𝑦")
            content = content.replace("Currrrent", "Current")
            content = content.replace("Cammon", "Common")
            content = content.replace("Equty", "Equity")
        content = re.sub(r'typeface="(?!(?:Arial))[^"]+"', 'typeface="Arial"', content)
        with open(slide_file, "w", encoding="utf-8") as f:
            f.write(content)

print("Enforced 100% Arial font and fixed mathematical typography.")

# Repack into PPTX using proper forward-slash zip entry names
with zipfile.ZipFile(PPTX_PATH, 'w', zipfile.ZIP_DEFLATED) as z_out:
    for root, dirs, files in os.walk(TEMP_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            arcname = os.path.relpath(full_path, TEMP_DIR).replace('\\', '/')
            z_out.write(full_path, arcname)

print(f"Successfully repacked {PPTX_PATH}!")
