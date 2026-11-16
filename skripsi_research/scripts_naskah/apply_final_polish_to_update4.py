import zipfile
import shutil
import os
import xml.etree.ElementTree as ET

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ET.register_namespace('w', W_NS)

DOCX_PATH = 'update4.docx'
temp_dir = 'temp_docx_fix'
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

with zipfile.ZipFile(DOCX_PATH, 'r') as zin:
    zin.extractall(temp_dir)

doc_xml_path = os.path.join(temp_dir, 'word', 'document.xml')
doc_tree = ET.parse(doc_xml_path)
body = doc_tree.getroot().find(f"{{{W_NS}}}body")

for p in body.iter(f"{{{W_NS}}}p"):
    p_text = "".join(p.itertext())
    if "antarmuka menyediakan halaman Evaluasi Model" in p_text and "141 sampel observasi" in p_text:
        new_text = "Bagi keperluan analisis teknis dan akademis, antarmuka menyediakan halaman Evaluasi Model yang memuat perbandingan kinerja antar-algoritma secara komprehensif. Halaman ini menyajikan visualisasi grafis interaktif kurva Receiver Operating Characteristic (ROC-AUC) yang memperlihatkan disparitas daya pemisahan antara XGBoost (AUC = 0,9400), MDA Empiris BEI (AUC = 0,9200), dan Altman Z''-Score klasik (AUC = 0,8800). Selain itu, ditampilkan visualisasi matriks konfusi (confusion matrix) pada data pengujian 754 sampel observasi (hold-out 20%) serta diagram batang tingkat kepentingan fitur (gain feature importance) XGBoost yang membuktikan dominasi rasio retained earnings (X2 = 42,50%) dan rasio profitabilitas operasional (X3 = 31,80%) dalam penentuan kelangsungan hidup emiten."
        for r in list(p):
            if r.tag.endswith('r'):
                p.remove(r)
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
        print("Updated P#603 in document.")

    elif "Total observasi testing: 141 (26 Distress dan 115 Non-Distress)" in p_text:
        new_text = "Total observasi testing: 754 (61 Distress dan 693 Non-Distress)."
        for r in list(p):
            if r.tag.endswith('r'):
                p.remove(r)
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
        print("Updated P#1280 in Lampiran.")

    elif "Weighted F1: 26/141" in p_text:
        new_text = "Weighted F1: 61/754 * 0.784 + 693/754 * 0.980 = 0.063 + 0.901 = 0.964 (96.42%)"
        for r in list(p):
            if r.tag.endswith('r'):
                p.remove(r)
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
        print("Updated P#1286 in Lampiran.")

doc_tree.write(doc_xml_path, xml_declaration=True, encoding='utf-8')

with zipfile.ZipFile(DOCX_PATH, 'w', zipfile.ZIP_DEFLATED) as zout:
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, temp_dir)
            zout.write(abs_path, rel_path)

shutil.rmtree(temp_dir)
print("Fix successfully applied to update4.docx.")
