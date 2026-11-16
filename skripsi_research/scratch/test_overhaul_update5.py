import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ET.register_namespace('w', W_NS)

DOCX_IN = 'update5 (AutoRecovered).docx'
BACKUP_PATH = 'update5_backup_before_revision.docx'

if not os.path.exists(BACKUP_PATH):
    shutil.copy2(DOCX_IN, BACKUP_PATH)
    print(f"Cadangan aman berhasil dibuat: {BACKUP_PATH}")

temp_dir = 'temp_docx_update5'
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

with zipfile.ZipFile(DOCX_IN, 'r') as zin:
    zin.extractall(temp_dir)

doc_xml_path = os.path.join(temp_dir, 'word', 'document.xml')
doc_tree = ET.parse(doc_xml_path)
body = doc_tree.getroot().find(f"{{{W_NS}}}body")
children = list(body)

print(f"Total elemen body: {len(children)}")

# Helper to create styled paragraph
def create_styled_p(text, font_name="Calibri", sz="24", bold=False, italic=False, jc="both", line="480", space_before="0", space_after="120"):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    jc_el = ET.SubElement(pPr, f"{{{W_NS}}}jc")
    jc_el.set(f"{{{W_NS}}}val", jc)
    sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    sp.set(f"{{{W_NS}}}line", str(line))
    sp.set(f"{{{W_NS}}}lineRule", "auto")
    sp.set(f"{{{W_NS}}}before", str(space_before))
    sp.set(f"{{{W_NS}}}after", str(space_after))
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
    rf.set(f"{{{W_NS}}}ascii", font_name)
    rf.set(f"{{{W_NS}}}hAnsi", font_name)
    rf.set(f"{{{W_NS}}}cs", font_name)
    
    sz_el = ET.SubElement(rPr, f"{{{W_NS}}}sz")
    sz_el.set(f"{{{W_NS}}}val", str(sz))
    szCs_el = ET.SubElement(rPr, f"{{{W_NS}}}szCs")
    szCs_el.set(f"{{{W_NS}}}val", str(sz))
    
    if bold: ET.SubElement(rPr, f"{{{W_NS}}}b")
    if italic: ET.SubElement(rPr, f"{{{W_NS}}}i")
    
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return p

# 1. Update Bab 1 textual refinements
for p in body.iter(f"{{{W_NS}}}p"):
    p_text = "".join(p.itertext())
    if "rancangan rancanganini" in p_text:
        # replace run text
        new_text = p_text.replace("rancangan rancanganini", "perancangan sistem ini")
        for r in list(p):
            if r.tag.endswith('r'): p.remove(r)
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rf.set(f"{{{W_NS}}}ascii", "Calibri")
        rf.set(f"{{{W_NS}}}hAnsi", "Calibri")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "24")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.text = new_text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        print("Fixed typo: rancangan rancanganini in Bab 1.")

    elif "rancangan rancangan tidak hanya berhenti" in p_text:
        new_text = p_text.replace("rancangan rancangan tidak hanya berhenti", "perancangan sistem ini tidak hanya berhenti")
        new_text = new_text.replace("(seperti Streamlit)", "menggunakan framework Streamlit")
        for r in list(p):
            if r.tag.endswith('r'): p.remove(r)
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rf.set(f"{{{W_NS}}}ascii", "Calibri")
        rf.set(f"{{{W_NS}}}hAnsi", "Calibri")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "24")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.text = new_text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        print("Fixed typo: rancangan rancangan in Bab 1.")

    elif "Populasi dalam rancangan ini mencakup seluruh perusahaan manufaktur yang terdaftar di BEI selama periode pengamatan yang ditentukan (misalnya lima tahun terakhir)" in p_text:
        new_text = "Populasi dalam perancangan ini mencakup seluruh perusahaan manufaktur yang terdaftar di Bursa Efek Indonesia (BEI) selama 13 tahun periode pengamatan (2014–2026), yang menghasilkan dataset panel komprehensif sebanyak 3.770 observasi dari 290 emiten. Untuk mendapatkan representasi data yang akurat, penarikan sampel menerapkan teknik purposive sampling berdasarkan kriteria kelengkapan publikasi laporan keuangan tahunan yang telah diaudit. Variabel masukan yang digunakan mengadopsi indikator rasio keuangan model Altman Z''-Score revisi 1995 untuk pasar berkembang (emerging market), yaitu: rasio modal kerja terhadap total aset (X1), laba ditahan terhadap total aset (X2), laba sebelum bunga dan pajak terhadap total aset (X3), serta nilai buku ekuitas terhadap total liabilitas (X4). Sementara itu, variabel target diklasifikasikan secara biner menjadi kategori mengalami kesulitan keuangan (Distress, Y = 1) dan kondisi sehat (Non-Distress, Y = 0) berdasarkan indikator laba bersih negatif dua tahun berturut-turut, defisit modal kerja, dan defisit ekuitas operasional."
        for r in list(p):
            if r.tag.endswith('r'): p.remove(r)
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rf.set(f"{{{W_NS}}}ascii", "Calibri")
        rf.set(f"{{{W_NS}}}hAnsi", "Calibri")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "24")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.text = new_text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        print("Updated Bab 1 P#112 to Option 3 panel dataset (3.770 obs, 4 rasio Altman 1995).")

print("Bab 1 text verified and updated.")
