import os
import shutil
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
WP_NS = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'
PIC_NS = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
R_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL_PKG_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'

ET.register_namespace('w', W_NS)

DOCX_IN = 'update4.docx'
BACKUP_PATH = 'update4_backup_before_colab_overhaul.docx'
shutil.copy2(DOCX_IN, BACKUP_PATH)
print(f"Cadangan aman berhasil dibuat: {BACKUP_PATH}")

SRC_IMG_DIR = 'reports/gambar_google_colab'

# List of 21 images and their metadata
IMAGES_META = [
    # Subbab 3.2.2 (Tahap 1 s.d. 4)
    {"file": "colab_3_2_2_1_parse_financial_number.png", "media_name": "image_colab_1.png", "r_id": "rId25", "id": 1001, "cap": "Gambar 3.1 Tampilan Hasil Eksekusi Pembersihan Angka Finansial pada Google Colab"},
    {"file": "colab_3_2_2_2_complete_financial_values.png", "media_name": "image_colab_2.png", "r_id": "rId26", "id": 1002, "cap": "Gambar 3.2 Tampilan Hasil Eksekusi Rekonsiliasi Neraca pada Google Colab"},
    {"file": "colab_3_2_2_3_build_features_from_financials.png", "media_name": "image_colab_3.png", "r_id": "rId27", "id": 1003, "cap": "Gambar 3.3 Tampilan Hasil Eksekusi Ekstraksi Fitur Rasio Keuangan pada Google Colab"},
    {"file": "colab_3_2_2_4_clean_and_cap_ratios.png", "media_name": "image_colab_4.png", "r_id": "rId28", "id": 1004, "cap": "Gambar 3.4 Tampilan Hasil Eksekusi Capping Nilai Ekstrem Rasio pada Google Colab"},
    
    # Subbab 3.2.3 (Bagian 1 s.d. 5)
    {"file": "colab_3_2_3_1_kalkulasi_altman_zscore.png", "media_name": "image_colab_5.png", "r_id": "rId29", "id": 1005, "cap": "Gambar 3.5 Tampilan Hasil Eksekusi Kalkulasi Skor Altman Z''-Score dan Klasifikasi 3 Zona pada Google Colab"},
    {"file": "colab_3_2_3_2_komparasi_altman_1968_vs_1995.png", "media_name": "image_colab_6.png", "r_id": "rId30", "id": 1006, "cap": "Gambar 3.6 Tampilan Hasil Eksekusi Komparasi Model Altman 1968 vs 1995 pada Google Colab"},
    {"file": "colab_3_2_3_3_diagnostik_aisa_simulasi_andi.png", "media_name": "image_colab_7.png", "r_id": "rId31", "id": 1007, "cap": "Gambar 3.7 Tampilan Hasil Eksekusi Diagnostik Pemicu Distress dan Simulasi Titik Impas pada Google Colab"},
    
    # Subbab 3.2.4 (Bagian 1 & 2)
    {"file": "colab_3_2_4_1_pengujian_mda_fisher_bei.png", "media_name": "image_colab_8.png", "r_id": "rId32", "id": 1008, "cap": "Gambar 3.8 Tampilan Hasil Eksekusi Komparasi Diagnostik MDA Fisher BEI pada Google Colab"},
    {"file": "colab_3_2_4_2_visualisasi_3panel_mda_fisher.png", "media_name": "image_colab_9.png", "r_id": "rId33", "id": 1009, "cap": "Gambar 3.9 Tampilan Kanvas Visualisasi 3-Panel Evaluasi Model MDA Fisher BEI pada Google Colab"},
    
    # Subbab 3.2.5 (Bagian 1 & 2)
    {"file": "colab_3_2_5_1_pengujian_inferensi_xgboost.png", "media_name": "image_colab_10.png", "r_id": "rId34", "id": 1010, "cap": "Gambar 3.10 Tampilan Hasil Eksekusi Inferensi Model XGBoost pada Google Colab"},
    {"file": "colab_3_2_5_2_visualisasi_4panel_kinerja_xgboost.png", "media_name": "image_colab_11.png", "r_id": "rId35", "id": 1011, "cap": "Gambar 3.11 Tampilan Kanvas Visualisasi 4-Panel Kinerja Komprehensif XGBoost pada Google Colab"},
    
    # Bab 4.1 (Sel 4.1.1 s.d. 4.1.10)
    {"file": "01_colab_4_1_1_persiapan_fitur_target.png", "media_name": "image_colab_12.png", "r_id": "rId36", "id": 1012, "cap": "Gambar 4.1 Tampilan Hasil Eksekusi Persiapan Data dan Distribusi Kelas pada Google Colab"},
    {"file": "02_colab_4_1_2_heatmap_korelasi_pearson.png", "media_name": "image_colab_13.png", "r_id": "rId37", "id": 1013, "cap": "Gambar 4.2 Tampilan Hasil Eksekusi Heatmap Korelasi Pearson pada Google Colab"},
    {"file": "03_colab_4_1_3_evaluasi_detail_dan_cm.png", "media_name": "image_colab_14.png", "r_id": "rId38", "id": 1014, "cap": "Gambar 4.3 Tampilan Hasil Eksekusi Fungsi Evaluasi Biner pada Google Colab"},
    {"file": "04_colab_4_1_4_eksperimen_altman_zscore.png", "media_name": "image_colab_15.png", "r_id": "rId39", "id": 1015, "cap": "Gambar 4.4 Tampilan Hasil Eksekusi Eksperimen Model Altman Z'' pada Google Colab"},
    {"file": "05_colab_4_1_5_eksperimen_xgboost_classifier.png", "media_name": "image_colab_16.png", "r_id": "rId40", "id": 1016, "cap": "Gambar 4.5 Tampilan Hasil Eksekusi Eksperimen Model XGBoost pada Google Colab"},
    {"file": "06_colab_4_1_6_stratified_5fold_cv.png", "media_name": "image_colab_17.png", "r_id": "rId41", "id": 1017, "cap": "Gambar 4.6 Tampilan Hasil Eksekusi 5-Fold Cross Validation pada Google Colab"},
    {"file": "07_colab_4_1_7_ringkasan_multi_model.png", "media_name": "image_colab_18.png", "r_id": "rId42", "id": 1018, "cap": "Gambar 4.7 Tampilan Hasil Eksekusi Konsolidasi Multi-Model pada Google Colab"},
    {"file": "08_colab_4_1_8_boxplot_perbandingan_algoritma.png", "media_name": "image_colab_19.png", "r_id": "rId43", "id": 1019, "cap": "Gambar 4.8 Tampilan Hasil Eksekusi Boxplot Perbandingan Algoritma pada Google Colab"},
    {"file": "09_colab_4_1_9_seleksi_model_terbaik.png", "media_name": "image_colab_20.png", "r_id": "rId44", "id": 1020, "cap": "Gambar 4.9 Tampilan Hasil Eksekusi Seleksi Model Terbaik pada Google Colab"},
    {"file": "10_colab_4_1_10_latih_ulang_serialisasi_json.png", "media_name": "image_colab_21.png", "r_id": "rId45", "id": 1021, "cap": "Gambar 4.10 Tampilan Hasil Eksekusi Serialisasi Artefak Model JSON pada Google Colab"}
]

# Calculate dimensions for each image in EMUs
for meta in IMAGES_META:
    p = os.path.join(SRC_IMG_DIR, meta['file'])
    im = Image.open(p)
    w, h = im.size
    cx = 5486400  # 6.0 inches
    cy = int(cx * (h / w))
    if cy > 6400800: # Cap at 7.0 inches
        ratio = 6400800 / cy
        cy = 6400800
        cx = int(cx * ratio)
    meta['cx'] = cx
    meta['cy'] = cy

def create_p(text, font_name="Calibri", sz="24", bold=False, italic=False, jc="both", line="480", space_after="0"):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    jc_el = ET.SubElement(pPr, f"{{{W_NS}}}jc")
    jc_el.set(f"{{{W_NS}}}val", jc)
    sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    sp.set(f"{{{W_NS}}}line", str(line))
    sp.set(f"{{{W_NS}}}lineRule", "auto")
    sp.set(f"{{{W_NS}}}after", str(space_after))
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
    rf.set(f"{{{W_NS}}}ascii", font_name)
    rf.set(f"{{{W_NS}}}hAnsi", font_name)
    rf.set(f"{{{W_NS}}}cs", font_name)
    rf.set(f"{{{W_NS}}}cstheme", "minorHAnsi")
    
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

def create_image_drawing_p(meta):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
    jc.set(f"{{{W_NS}}}val", "center")
    sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    sp.set(f"{{{W_NS}}}line", "240")
    sp.set(f"{{{W_NS}}}after", "120")
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    drawing_xml = f'''<w:drawing xmlns:w="{W_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}" xmlns:r="{R_NS}">
  <wp:inline distT="0" distB="0" distL="0" distR="0">
    <wp:extent cx="{meta['cx']}" cy="{meta['cy']}"/>
    <wp:effectExtent l="0" t="0" r="0" b="0"/>
    <wp:docPr id="{meta['id']}" name="{meta['media_name']}"/>
    <wp:cNvGraphicFramePr>
      <a:graphicFrameLocks noChangeAspect="1"/>
    </wp:cNvGraphicFramePr>
    <a:graphic>
      <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic>
          <pic:nvPicPr>
            <pic:cNvPr id="{meta['id']}" name="{meta['media_name']}"/>
            <pic:cNvPicPr/>
          </pic:nvPicPr>
          <pic:blipFill>
            <a:blip r:embed="{meta['r_id']}"/>
            <a:stretch>
              <a:fillRect/>
            </a:stretch>
          </pic:blipFill>
          <pic:spPr>
            <a:xfrm>
              <a:off x="0" y="0"/>
              <a:ext cx="{meta['cx']}" cy="{meta['cy']}"/>
            </a:xfrm>
            <a:prstGeom prst="rect">
              <a:avLst/>
            </a:prstGeom>
          </pic:spPr>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>'''
    drawing_el = ET.fromstring(drawing_xml)
    r.append(drawing_el)
    return p

def create_output_box_p(lines):
    # Formatted terminal output card with white background and thin border
    p_list = []
    for line in lines:
        p = ET.Element(f"{{{W_NS}}}p")
        pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
        jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
        jc.set(f"{{{W_NS}}}val", "left")
        sp = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
        sp.set(f"{{{W_NS}}}line", "220")
        sp.set(f"{{{W_NS}}}after", "0")
        
        # Subtle light background
        shd = ET.SubElement(pPr, f"{{{W_NS}}}shd")
        shd.set(f"{{{W_NS}}}val", "clear")
        shd.set(f"{{{W_NS}}}color", "auto")
        shd.set(f"{{{W_NS}}}fill", "F8F9FA")
        
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rf.set(f"{{{W_NS}}}ascii", "Consolas")
        rf.set(f"{{{W_NS}}}hAnsi", "Consolas")
        rf.set(f"{{{W_NS}}}cs", "Consolas")
        
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "18") # 9pt
        szCs = ET.SubElement(rPr, f"{{{W_NS}}}szCs")
        szCs.set(f"{{{W_NS}}}val", "18")
        
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.text = line
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        p_list.append(p)
    return p_list

print("Helper elements defined.")
