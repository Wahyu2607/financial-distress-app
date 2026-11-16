import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
import re

PPTX_PATH = "skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND.pptx"
PPTX_BACKUP = "skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx"
TEMP_DIR = "skripsi_research/scratch/pptx_polish"

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

def make_p(runs, align="l", space_after=350, line_spacing=115000):
    p = ET.Element(f"{{{A_NS}}}p")
    pPr = ET.SubElement(p, f"{{{A_NS}}}pPr", algn=align)
    if space_after is not None:
        spcAft = ET.SubElement(pPr, f"{{{A_NS}}}spcAft")
        ET.SubElement(spcAft, f"{{{A_NS}}}spcPts", val=str(space_after))
    if line_spacing is not None:
        lnSpc = ET.SubElement(pPr, f"{{{A_NS}}}lnSpc")
        ET.SubElement(lnSpc, f"{{{A_NS}}}spcPct", val=str(line_spacing))
    for r in runs:
        if isinstance(r, tuple):
            text = r[0]
            bold = r[1] if len(r) > 1 else False
            size = r[2] if len(r) > 2 else None
            color = r[3] if len(r) > 3 else None
            scheme = r[4] if len(r) > 4 else None
            p.append(make_r(text, bold=bold, size=size, color=color, scheme=scheme))
        else:
            p.append(r)
    return p

def set_shape_text(sp, paragraphs_runs, align="l", default_space_after=300):
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

def create_textbox_shape(shape_id, shape_name, x, y, cx, cy, paragraphs_runs, bg_color=None, border_color=None, align="l", default_space_after=300):
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

# Unpack
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
with zipfile.ZipFile(PPTX_BACKUP, 'r') as z:
    z.extractall(TEMP_DIR)
print(f"Unpacked {PPTX_BACKUP} to {TEMP_DIR}")

# ----------------- SLIDE 1 -----------------
s1_path = os.path.join(TEMP_DIR, "ppt/slides/slide1.xml")
t1 = ET.parse(s1_path)
spTree1 = t1.find(".//p:spTree", {"p": P_NS})
for sp in spTree1.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [
            [
                ("PREDIKSI FINANCIAL DISTRESS PADA INDUSTRI MANUFAKTUR BEI\n", True, 2500, "FFFFFF"),
                ("Pendekatan Model Extreme Gradient Boosting dan Altman Z-Score", True, 2200, "FF4B4B")
            ]
        ], align="l", default_space_after=300)
    elif name == "Subtitle 2":
        set_shape_text(sp, [
            [("Wahyu Pamungkas ", True, 1600, "FFFFFF"), ("(NIM: 535220037)", False, 1500, "DDDDDD")],
            [("Dosen Pembimbing Utama       : ", True, 1300, "FFD700"), ("Pak Tony, S.Kom., M.Kom., Ph.D.", False, 1300, "FFFFFF")],
            [("Dosen Pembimbing Pendamping : ", True, 1300, "FFD700"), ("Pak Arnold Kaudin, S.E., M.M., M.Com., Ph.D.", False, 1300, "FFFFFF")],
            [("Program Studi Sarjana Teknik Informatika | Fakultas Teknologi Informasi | Universitas Tarumanagara", False, 1150, "AAAAAA")],
            [("Sidang Tugas Akhir / Skripsi — 2026", True, 1200, "00FF7F")]
        ], align="l", default_space_after=200)
t1.write(s1_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 1.")

# ----------------- SLIDE 2 -----------------
s2_path = os.path.join(TEMP_DIR, "ppt/slides/slide2.xml")
t2 = ET.parse(s2_path)
spTree2 = t2.find(".//p:spTree", {"p": P_NS})
for sp in spTree2.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("AGENDA PRESENTASI SIDANG SKRIPSI (10 MENIT)", True, 2400, "FFFFFF")]], default_space_after=250)
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [("1. Urgensi & Latar Belakang Riset: ", True, 1350, "FFD700"), ("Pilar manufaktur BEI, risiko gagal bayar, dan asimetri informasi pasar modal.", False, 1300, "FFFFFF")],
            [("2. Gap Perancangan & Masalah: ", True, 1350, "FFD700"), ("Kelemahan linearitas model klasik, ketimpangan kelas ekstrem (1:11,40), & perlunya koefisien lokal.", False, 1300, "FFFFFF")],
            [("3. Solusi Tiga Pendekatan Komparatif: ", True, 1350, "FFD700"), ("Sinergi simultan Altman Z'' 1995, MDA Fisher BEI, XGBoost Classifier, & 4 rasio fundamental.", False, 1300, "FFFFFF")],
            [("4. Dataset Panel & Rekayasa Fitur: ", True, 1350, "FFD700"), ("Panel 3.770 observasi BEI (2014–2026), 13 pos taksonomi XBRL, dan aturan capping X4 <= 3.0.", False, 1300, "FFFFFF")],
            [("5. Formulasi & Komputasi Empiris: ", True, 1350, "FFD700"), ("Model Altman Z'', rekalibrasi koefisien Fisher BEI, simulasi riil AALI, dan arsitektur XGBoost.", False, 1300, "FFFFFF")],
            [("6. Evaluasi & Benchmark Multi-Model: ", True, 1350, "FFD700"), ("Pengujian 754 data uji (Akurasi 96,42%, ROC-AUC 0,9400) dan Stratified 3-Fold Cross-Validation.", False, 1300, "FFFFFF")],
            [("7. Kesimpulan & Validasi Sistem: ", True, 1350, "FFD700"), ("Champion model XGBoost, aplikasi web Streamlit, uji Pakar (94,50%), dan UAT (88,60%).", False, 1300, "FFFFFF")]
        ], default_space_after=220)
t2.write(s2_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 2.")

# ----------------- SLIDE 3 -----------------
s3_path = os.path.join(TEMP_DIR, "ppt/slides/slide3.xml")
t3 = ET.parse(s3_path)
spTree3 = t3.find(".//p:spTree", {"p": P_NS})
for sp in spTree3.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("LATAR BELAKANG & URGENSI PENELITIAN", True, 2400, "FFFFFF")]], default_space_after=250)
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [("• Pilar Strategis Industri Manufaktur BEI: ", True, 1400, "FFD700"), ("Kontributor utama PDB nasional yang berkarakter padat modal (capital-intensive) dan memiliki siklus konversi kas yang panjang.", False, 1350, "FFFFFF")],
            [("• Kerentanan Terhadap Guncangan Makroekonomi: ", True, 1400, "FFD700"), ("Sangat sensitif terhadap kenaikan suku bunga pinjaman, lonjakan harga bahan baku impor, dan pelemahan daya beli domestik.", False, 1350, "FFFFFF")],
            [("• Eskalasi Risiko Menuju Kebangkrutan: ", True, 1400, "FFD700"), ("Defisit likuiditas yang terlambat ditangani bereskalasi menjadi gagal bayar utang (default), gugatan restrukturisasi PKPU, suspensi saham, hingga delisting paksa.", False, 1350, "FFFFFF")],
            [("• Asimetri Informasi & Dampak Fatal Investor: ", True, 1400, "FFD700"), ("Kegagalan mendeteksi distres sejak dini (Type II Error) merugikan investor publik dan kreditur perbankan secara masif akibat asimetri informasi laporan tahunan.", False, 1350, "FFFFFF")],
            [("• Kebutuhan Sistem Peringatan Dini Cerdas: ", True, 1400, "00FF7F"), ("Dibutuhkan Sistem Pendukung Keputusan (DSS) otomatis yang mampu membaca laporan bursa dan memberikan sinyal peringatan dini secara objektif.", False, 1350, "FFFFFF")]
        ], default_space_after=240)
t3.write(s3_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 3.")

# ----------------- SLIDE 4 -----------------
s4_path = os.path.join(TEMP_DIR, "ppt/slides/slide4.xml")
t4 = ET.parse(s4_path)
spTree4 = t4.find(".//p:spTree", {"p": P_NS})
for sp in spTree4.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("GAP PERANCANGAN & RUMUSAN MASALAH", True, 2400, "FFFFFF")]], default_space_after=250)
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [("1. Keterbatasan Linearitas Model Klasik: ", True, 1400, "FFD700"), ("Formula Altman dan MDA konvensional mengasumsikan hubungan aditif linear dan normalitas, padahal interaksi risiko finansial pasar berkembang bersifat non-linear dan kompleks.", False, 1350, "FFFFFF")],
            [("2. Ketimpangan Kelas Ekstrem (Severe Imbalance 1 : 11,40): ", True, 1400, "FFD700"), ("Emiten sehat mendominasi bursa BEI (91,94%). Model standar tanpa pembobotan menghasilkan bias mayoritas tinggi dan meloloskan banyak kasus kebangkrutan.", False, 1350, "FFFFFF")],
            [("3. Ketiadaan Parameter Empiris Khusus BEI: ", True, 1400, "FFD700"), ("Bobot Altman asli diturunkan dari pasar modal Amerika Serikat. Diperlukan rekalibrasi empiris koefisien MDA yang mencerminkan profil struktur modal emiten Indonesia.", False, 1350, "FFFFFF")],
            [("4. Kesenjangan Teori Menuju Implementasi Praktis: ", True, 1400, "FFD700"), ("Kajian akademis sering terbatas pada kalkulasi statis; praktisi pasar modal memerlukan Decision Support System interaktif yang menyediakan simulasi perbaikan What-If.", False, 1350, "FFFFFF")]
        ], default_space_after=260)
t4.write(s4_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 4.")

# ----------------- SLIDE 5 -----------------
s5_path = os.path.join(TEMP_DIR, "ppt/slides/slide5.xml")
t5 = ET.parse(s5_path)
spTree5 = t5.find(".//p:spTree", {"p": P_NS})
for sp in spTree5.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("SOLUSI: SINERGI TIGA PENDEKATAN KOMPARATIF", True, 2400, "FFFFFF")]], default_space_after=250)
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [("• Komparasi Simultan 3 Pilar Metodologi: ", True, 1400, "FFD700"), ("Menyandingkan (1) Altman Z''-Score 1995 (baseline emerging market), (2) MDA Fisher Rekalibrasi BEI, dan (3) XGBoost Classifier sebagai model adaptif non-linear.", False, 1350, "FFFFFF")],
            [("• 4 Rasio Keuangan Fundamental Pembentuk Model: ", True, 1400, "FFD700")],
            [("   - X1 (WCTA)  : ", True, 1350, "00FF7F"), ("Modal Kerja Bersih / Total Aset — mengukur likuiditas jangka pendek.", False, 1300, "FFFFFF")],
            [("   - X2 (RETA)  : ", True, 1350, "00FF7F"), ("Laba Ditahan / Total Aset — mengukur akumulasi profitabilitas & usia produktif.", False, 1300, "FFFFFF")],
            [("   - X3 (EBITTA): ", True, 1350, "00FF7F"), ("EBIT / Total Aset — mengukur efektivitas aset menghasilkan laba operasional murni.", False, 1300, "FFFFFF")],
            [("   - X4 (CETL)  : ", True, 1350, "00FF7F"), ("Ekuitas Saham / Total Liabilitas — mengukur solvabilitas & daya tahan modal (Capping <= 3.0).", False, 1300, "FFFFFF")],
            [("• Integrasi Decision Support System: ", True, 1400, "FFD700"), ("Sistem menyajikan visualisasi dekomposisi pemicu krisis serta simulator titik impas restrukturisasi keuangan.", False, 1350, "FFFFFF")]
        ], default_space_after=180)
t5.write(s5_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 5.")

# ----------------- SLIDE 6 -----------------
s6_path = os.path.join(TEMP_DIR, "ppt/slides/slide6.xml")
t6 = ET.parse(s6_path)
spTree6 = t6.find(".//p:spTree", {"p": P_NS})
for sp in spTree6.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("ALUR IMPLEMENTASI & PIPELINE KOMPUTASI", True, 2400, "FFFFFF")]], default_space_after=250)
    elif name == "Content Placeholder 2":
        set_shape_text(sp, [
            [("1. Prapemrosesan & Normalisasi Data: ", True, 1400, "FFD700"), ("Parsing multi-sumber (XBRL IDX, CSV, Excel, PDF), penyeragaman satuan Rupiah penuh, dan penyeimbangan neraca otomatis (Aset = Liabilitas + Ekuitas).", False, 1350, "FFFFFF")],
            [("2. Rekayasa Fitur & Pembatasan Capping: ", True, 1400, "FFD700"), ("Kalkulasi rasio X1 s.d. X4 serta pembatasan rasio solvabilitas X4 <= 3.0 guna meredam anomali leverage emiten berutang mini.", False, 1350, "FFFFFF")],
            [("3. Komputasi Model Altman Z'' (1995): ", True, 1400, "FFD700"), ("Pembobotan formula emerging market: Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4 dan zonasi 3 kuadran.", False, 1350, "FFFFFF")],
            [("4. Pemodelan MDA Fisher BEI & XGBoost: ", True, 1400, "FFD700"), ("Eksekusi fungsi diskriminan koefisien empiris baru BEI serta inferensi ensemble probabilitas pohon XGBoost (scale_pos_weight = 11.38).", False, 1350, "FFFFFF")],
            [("5. Antarmuka DSS & Simulator What-If: ", True, 1400, "00FF7F"), ("Penyajian dashboard diagnostik risiko, indikator peringatan dini, serta rekomendasi titik impas restrukturisasi modal.", False, 1350, "FFFFFF")]
        ], default_space_after=220)
t6.write(s6_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 6.")

# ----------------- SLIDE 7 -----------------
# Keep table data, verify title
s7_path = os.path.join(TEMP_DIR, "ppt/slides/slide7.xml")
t7 = ET.parse(s7_path)
spTree7 = t7.find(".//p:spTree", {"p": P_NS})
for sp in spTree7.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("PRAPEMROSESAN DATA: DATASET PANEL BEI", True, 2400, "FFFFFF")]], default_space_after=250)
t7.write(s7_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 7.")

# ----------------- SLIDE 8 -----------------
s8_path = os.path.join(TEMP_DIR, "ppt/slides/slide8.xml")
t8 = ET.parse(s8_path)
spTree8 = t8.find(".//p:spTree", {"p": P_NS})
for sp in spTree8.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("REKAYASA FITUR & MEKANISME CAPPING RASIO", True, 2400, "FFFFFF")]], default_space_after=250)

# Card under flow
card_s8 = create_textbox_shape(
    shape_id=8801, shape_name="Card Flow Explanation",
    x=714375, y=2750000, cx=10772775, cy=3500000,
    paragraphs_runs=[
        [("1. Ekstraksi Multi-Format & Konversi Terstandarisasi:", True, 1350, "FFD700")],
        [("   • Mengonversi laporan keuangan multi-format (XBRL IDX, CSV, Excel, PDF) ke dalam satuan Rupiah penuh terstandarisasi.", False, 1300, "FFFFFF")],
        [("2. Pembersihan Otomatis & Penegakan Persamaan Akuntansi:", True, 1350, "FFD700")],
        [("   • Menyeimbangkan neraca otomatis via aturan baku: Modal Kerja = Aset Lancar - Liabilitas Lancar; Total Liabilitas = Total Aset - Total Ekuitas.", False, 1300, "FFFFFF")],
        [("3. Inovasi Capping Rasio Solvabilitas (X4 <= 3.0):", True, 1350, "00FF7F")],
        [("   • Pada emiten dengan utang sangat kecil, rasio Ekuitas/Liabilitas dapat melonjak ekstrem (>8.0 hingga >50.0).", False, 1300, "FFFFFF")],
        [("   • Pembatasan X4 <= 3.0 meredam anomali leverage ekstrem tanpa mengubah esensi bahwa emiten tersebut memiliki struktur modal yang sangat sehat.", False, 1300, "FFFFFF")],
        [("4. Dampak Kestabilan Komputasi:", True, 1350, "FFD700")],
        [("   • Menstabilkan varians data, mencegah bias model linear klasik, dan memaksimalkan akurasi konvergensi pohon keputusan XGBoost.", False, 1300, "FFFFFF")]
    ],
    bg_color="111827", border_color="FF4B4B", align="l", default_space_after=120
)
spTree8.append(card_s8)
t8.write(s8_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 8.")

# ----------------- SLIDE 9 -----------------
s9_path = os.path.join(TEMP_DIR, "ppt/slides/slide9.xml")
t9 = ET.parse(s9_path)
spTree9 = t9.find(".//p:spTree", {"p": P_NS})
for sp in spTree9.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("FORMULASI MODEL ALTMAN Z''-SCORE (1995)", True, 2400, "FFFFFF")]], default_space_after=250)
    elif name == "TextBox 13":
        set_shape_text(sp, [
            [("Persamaan Altman Z''-Score Modifikasi Emerging Market (1995):", True, 1350, "FFD700")],
            [("Z'' = 6.56 × X1 + 3.26 × X2 + 6.72 × X3 + 1.05 × X4", True, 1400, "00FF7F")],
            [("Kriteria Zonasi Finansial 3 Kuadran:", True, 1350, "FFD700")],
            [("• Z'' <= 1.10         : ", True, 1300, "FF4B4B"), ("Zona Distress (Risiko Kebangkrutan Sangat Tinggi / Tekanan Solvabilitas Akut)", False, 1250, "FFFFFF")],
            [("• 1.10 < Z'' < 2.60 : ", True, 1300, "FFD700"), ("Zona Abu-Abu / Grey Area (Kondisi Rentan, Memerlukan Pengawasan Ketat)", False, 1250, "FFFFFF")],
            [("• Z'' >= 2.60         : ", True, 1300, "00FF7F"), ("Zona Aman / Safe Zone (Struktur Permodalan Sehat, Likuid, dan Solven)", False, 1250, "FFFFFF")],
            [("Alasan Teoretis Altman:", True, 1350, "FFD700")],
            [("• Rasio X5 (Sales/TA) sengaja dieliminasi oleh Altman agar model adil diterapkan pada industri manufaktur di negara berkembang tanpa terdistorsi oleh perbedaan intensitas modal.", False, 1250, "FFFFFF")]
        ], default_space_after=140)
t9.write(s9_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 9.")

# ----------------- SLIDE 10 -----------------
s10_path = os.path.join(TEMP_DIR, "ppt/slides/slide10.xml")
t10 = ET.parse(s10_path)
spTree10 = t10.find(".//p:spTree", {"p": P_NS})
for sp in spTree10.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("SIMULASI PERHITUNGAN ALTMAN Z'' (KASUS EMITEN AALI)", True, 2400, "FFFFFF")]], default_space_after=250)
    elif name == "TextBox 15":
        set_shape_text(sp, [
            [("• Hasil Evaluasi Diagnostik: ", True, 1400, "00FF7F"), ("Emiten AALI terklasifikasi ke dalam ZONA AMAN (Non-Distress / Sangat Sehat).", False, 1350, "FFFFFF")],
            [("• Analisis Komparasi Capping: ", True, 1400, "FFD700")],
            [("   - Tanpa Capping  : Z'' = 13,00 (Terdistorsi rasio X4 = 8,15 yang sangat besar).", False, 1300, "FFFFFF")],
            [("   - Dengan Capping : Z'' = 7,59  (Rasio X4 dibatasi secara rasional pada 3,0).", True, 1300, "00FF7F")],
            [("   - Kesimpulan Empiris: Kedua skor berada jauh di atas ambang batas aman 2,60. Mekanisme capping terbukti meredam leverage ekstrem tanpa mendistorsi status kesehatan emiten.", False, 1300, "FFFFFF")]
        ], default_space_after=180)
t10.write(s10_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 10.")

# ----------------- SLIDE 11 -----------------
s11_path = os.path.join(TEMP_DIR, "ppt/slides/slide11.xml")
t11 = ET.parse(s11_path)
spTree11 = t11.find(".//p:spTree", {"p": P_NS})
for sp in spTree11.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("MULTIPLE DISCRIMINANT ANALYSIS (MDA) FISHER BEI", True, 2400, "FFFFFF")]], default_space_after=250)

card_s11 = create_textbox_shape(
    shape_id=1101, shape_name="Card MDA Explanation",
    x=722313, y=2600000, cx=10626725, cy=3650000,
    paragraphs_runs=[
        [("1. Metodologi Rekalibrasi Empiris Fisher BEI:", True, 1350, "FFD700")],
        [("   • Memisahkan sampel latih menjadi 2 kelompok: Distres (N1 = 63) dan Non-Distres (N2 = 639).", False, 1300, "FFFFFF")],
        [("   • Menghitung pooled covariance matrix (Sw) dan vektor perbedaan rata-rata (d = mean1 - mean2).", False, 1300, "FFFFFF")],
        [("2. Formula Baru Hasil Re-estimasi Empiris BEI:", True, 1350, "FFD700")],
        [("   Z' = 6.1120 × X1 + 3.2776 × X2 + 4.8373 × X3 + 0.0430 × X4", True, 1400, "00FF7F")],
        [("3. Ambang Batas Titik Potong Centroid Empiris:", True, 1350, "FFD700")],
        [("   • Cut-off Centroid = (Z_distress_mean + Z_nondistress_mean) / 2 = 0.3844", True, 1350, "00FF7F")],
        [("   • Kriteria: Z' < 0.3844 -> Terindikasi DISTRESS  |  Z' >= 0.3844 -> NON-DISTRESS (SEHAT)", False, 1300, "FFFFFF")],
        [("4. Temuan Empiris Karakteristik Pasar Modal Indonesia:", True, 1350, "FFD700")],
        [("   • Koefisien X1 (6,1120) dan X3 (4,8373) memiliki kontribusi pembeda terbesar; membuktikan likuiditas modal kerja dan produktivitas laba riil adalah pilar penyelamat utama emiten manufaktur di Indonesia.", False, 1300, "FFFFFF")]
    ],
    bg_color="111827", border_color="00FF7F", align="l", default_space_after=120
)
spTree11.append(card_s11)
t11.write(s11_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 11.")

# ----------------- SLIDE 12 -----------------
s12_path = os.path.join(TEMP_DIR, "ppt/slides/slide12.xml")
t12 = ET.parse(s12_path)
spTree12 = t12.find(".//p:spTree", {"p": P_NS})
for sp in spTree12.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("PEMODELAN MACHINE LEARNING XGBOOST CLASSIFIER", True, 2400, "FFFFFF")]], default_space_after=250)

card_s12 = create_textbox_shape(
    shape_id=1201, shape_name="Card XGBoost Explanation",
    x=557700, y=2600000, cx=11063625, cy=3650000,
    paragraphs_runs=[
        [("1. Arsitektur Gradient Tree Boosting Adaptif:", True, 1350, "FFD700")],
        [("   • Membangun ensemble decision trees secara sekuensial dengan meminimalkan fungsi loss logistik biner ter-regularisasi melalui ekspansi deret Taylor orde kedua (gradien gi dan hessian hi).", False, 1300, "FFFFFF")],
        [("2. Solusi Ketimpangan Kelas Ekstrem (Severe Imbalance 1 : 11,40):", True, 1350, "FFD700")],
        [("   • Mengintroduksi bobot hukuman otomatis scale_pos_weight = 11,38.", True, 1350, "00FF7F")],
        [("   • Bobot ini memaksa algoritma memprioritaskan sensitivitas deteksi kelas distres sehingga memangkas False Negative secara drastis.", False, 1300, "FFFFFF")],
        [("3. Konfigurasi Hyperparameter Optimal:", True, 1350, "FFD700")],
        [("   • n_estimators = 100, max_depth = 3 (mencegah overfitting), learning_rate = 0.08, subsample = 0.85, colsample_bytree = 0.85.", False, 1300, "FFFFFF")],
        [("4. Feature Importance & Kecepatan Inferensi:", True, 1350, "FFD700")],
        [("   • Fitur X2 (Laba Ditahan/TA = 66,55%) dan X3 (EBIT/TA = 23,95%) mencakup 90,5% kekuatan prediktif model.", True, 1350, "00FF7F")],
        [("   • Latensi komputasi ultra-cepat 0,85 milidetik per sampel, sangat efisien untuk pemrosesan data bursa waktu nyata.", False, 1300, "FFFFFF")]
    ],
    bg_color="111827", border_color="00BFFF", align="l", default_space_after=120
)
spTree12.append(card_s12)
t12.write(s12_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 12.")

# ----------------- SLIDE 13 -----------------
s13_path = os.path.join(TEMP_DIR, "ppt/slides/slide13.xml")
t13 = ET.parse(s13_path)
spTree13 = t13.find(".//p:spTree", {"p": P_NS})
for sp in spTree13.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [[("EVALUASI MODEL & BENCHMARK MULTI-MODEL", True, 2400, "FFFFFF")]], default_space_after=250)

# Update Table 5 on Slide 13
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

# Card under table
card_s13 = create_textbox_shape(
    shape_id=1301, shape_name="Card KFold3 Evaluation",
    x=841375, y=4400000, cx=10515600, cy=2000000,
    paragraphs_runs=[
        [("• XGBoost Sebagai Champion Model: ", True, 1350, "FFD700"), ("Meraih performa tertinggi pada seluruh metrik utama (Akurasi 96,42%, ROC-AUC 0,9400, F1-Score 78,40%, Youden's J 0,7816) serta paling protektif meminimalkan False Negative (hanya 12 kasus pada 754 sampel uji).", False, 1300, "FFFFFF")],
        [("• Keunggulan Rekalibrasi MDA Fisher: ", True, 1350, "FFD700"), ("F1-Score meningkat dari 74,60% (Altman klasik) menjadi 76,56%, membuktikan keunggulan adaptasi koefisien lokal BEI.", False, 1300, "FFFFFF")],
        [("• Pengujian Validasi Silang (Stratified 3-Fold Cross-Validation):", True, 1350, "00FF7F")],
        [("   - Rata-rata Akurasi: 97,35% ± 0,24%  |  Rata-rata ROC-AUC: 0,9681 ± 0,0107  |  Rata-rata Recall: 91,46% ± 2,79%", False, 1250, "FFFFFF")],
        [("   - Rata-rata F1-Score: 84,75% ± 1,45%  |  Selisih Akurasi Latih (97,94%) vs Uji (97,35%): hanya 0,59% (Bebas Overfitting)", False, 1250, "FFFFFF")]
    ],
    bg_color="111827", border_color="FFD700", align="l", default_space_after=100
)
spTree13.append(card_s13)
t13.write(s13_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 13.")

# ----------------- SLIDE 14 -----------------
s14_path = os.path.join(TEMP_DIR, "ppt/slides/slide14.xml")
t14 = ET.parse(s14_path)
spTree14 = t14.find(".//p:spTree", {"p": P_NS})
for sp in spTree14.findall("p:sp", {"p": P_NS}):
    name = sp.find(".//p:cNvPr", {"p": P_NS}).get("name")
    if name == "Title 1":
        set_shape_text(sp, [
            [("KESIMPULAN, VALIDASI SISTEM & PENUTUP", True, 2400, "FFFFFF")],
            [("1. XGBoost Sebagai Champion Model: ", True, 1350, "FFD700"), ("Paling unggul memetakan risiko non-linear bursa BEI (F1 78,40%, ROC-AUC 0,9400, Akurasi 96,42%) serta paling aman bagi investor karena menekan Type II Error secara maksimal.", False, 1300, "FFFFFF")],
            [("2. Keberhasilan Rekalibrasi Empiris MDA Fisher BEI: ", True, 1350, "FFD700"), ("Koefisien diskriminan baru ber-cut-off 0,3844 terbukti lebih presisi (F1 76,56%) dibanding formula Altman klasik (F1 74,60%) untuk emiten Indonesia.", False, 1300, "FFFFFF")],
            [("3. Kinerja Sistem Pendukung Keputusan Web (Streamlit): ", True, 1350, "FFD700"), ("Menyediakan integrasi multi-sumber, dekomposisi pemicu krisis, checklist peringatan dini, dan simulator What-If titik impas restrukturisasi.", False, 1300, "FFFFFF")]
        ], align="l", default_space_after=200)
    elif name == "Subtitle 2":
        set_shape_text(sp, [
            [
                ("• Skor Validasi Pakar Finansial & Pasar Modal : ", True, 1350, "FFD700"),
                ("94,50% (Kategori Sangat Layak)", True, 1350, "00FF7F")
            ],
            [
                ("• Skor User Acceptance Test (UAT 26 Responden) : ", True, 1350, "FFD700"),
                ("88,60% (Kategori Sangat Baik)", True, 1350, "00FF7F")
            ],
            [
                ("Terima kasih atas perhatian Dewan Penguji & Dosen Pembimbing.", True, 1400, "FFFFFF")
            ],
            [
                ("Wahyu Pamungkas (NIM: 535220037) | Pembimbing: Pak Tony & Pak Arnold Kaudin | Universitas Tarumanagara", False, 1200, "AAAAAA")
            ]
        ], align="l", default_space_after=200)
t14.write(s14_path, encoding="utf-8", xml_declaration=True)
print("Updated Slide 14.")

# Post-processing: Ensure 100% Arial across all slides and fix remaining equation typos
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

print(f"Successfully polished and repacked {PPTX_PATH}!")
if os.path.exists(TEMP_DIR):
    shutil.rmtree(TEMP_DIR)
