import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ET.register_namespace('w', W_NS)

DOCX_IN = 'update5 (AutoRecovered).docx'
BACKUP_PATH = 'update5_backup_before_revision.docx'

temp_dir = 'temp_docx_update5_full'
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

with zipfile.ZipFile(DOCX_IN, 'r') as zin:
    zin.extractall(temp_dir)

doc_xml_path = os.path.join(temp_dir, 'word', 'document.xml')
doc_tree = ET.parse(doc_xml_path)
body = doc_tree.getroot().find(f"{{{W_NS}}}body")
children = list(body)

print(f"Total elemen body awal: {len(children)}")

# Helper to create styled paragraph
def create_p(text, font_name="Calibri", sz="24", bold=False, italic=False, jc="both", line="480", space_before="0", space_after="120", heading_level=None):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    
    if heading_level == 1:
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", "Heading1")
        jc = "center"
        bold = True
        space_before = "240"
        space_after = "120"
    elif heading_level == 2:
        pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
        pStyle.set(f"{{{W_NS}}}val", "Heading2")
        jc = "left"
        bold = True
        space_before = "180"
        space_after = "60"
        
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
        new_text = "Populasi dalam perancangan sistem ini mencakup seluruh perusahaan manufaktur yang terdaftar di Bursa Efek Indonesia (BEI) selama 13 tahun periode pengamatan (2014–2026), yang membentuk dataset panel komprehensif sebanyak 3.770 observasi dari 290 emiten. Untuk mendapatkan representasi data yang akurat, penarikan sampel menerapkan teknik purposive sampling berdasarkan kriteria kelengkapan publikasi laporan keuangan tahunan yang telah diaudit. Variabel masukan yang digunakan mengadopsi indikator rasio keuangan model Altman Z''-Score revisi 1995 untuk pasar berkembang (emerging market), yaitu: rasio modal kerja terhadap total aset (X1), laba ditahan terhadap total aset (X2), laba sebelum bunga dan pajak terhadap total aset (X3), serta nilai buku ekuitas terhadap total liabilitas (X4). Sementara itu, variabel target diklasifikasikan secara biner menjadi kategori mengalami kesulitan keuangan (Distress, Y = 1) dan kondisi sehat (Non-Distress, Y = 0) berdasarkan indikator laba bersih negatif dua tahun berturut-turut, defisit modal kerja, dan defisit ekuitas operasional."
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

# 2. Update Subbab 4.2.10: P#696, P#697, P#698 (Table 4.9), P#699, P#700, P#701
for p in body.iter(f"{{{W_NS}}}p"):
    p_text = "".join(p.itertext())
    if "Selain validasi pakar, pengujian penerimaan pengguna (User Acceptance Testing) dilakukan kepada" in p_text:
        new_text = "Selain validasi pakar, pengujian penerimaan pengguna (User Acceptance Testing / UAT) dilakukan kepada 35 responden lapangan dengan beragam latar belakang profesi, meliputi praktisi industri dan karyawan swasta (31,4%), akademisi, dosen, dan mahasiswa ekonomi/bisnis/informatika (25,7%), pengembang perangkat lunak dan data scientist (5,7%), analis keuangan pasar modal dan akuntan publik (2,9%), serta kelompok pengguna umum dan profesional lainnya (34,3%). Dari sisi rentang usia, responden didominasi oleh kelompok usia produktif 25–30 tahun (54,3%) dan 20–25 tahun (40,0%). Pengujian menggunakan instrumen kuesioner skala Likert 5 poin (1: Sangat Tidak Setuju hingga 5: Sangat Setuju) yang mengukur dua dimensi evaluasi utama: (1) Aspek Kemudahan dan Antarmuka Aplikasi (System Usability / UI & UX, 10 butir pernyataan) yang mengadopsi struktur System Usability Scale (SUS), dan (2) Relevansi Output dan Kinerja Fitur Sistem Pendukung Keputusan (Decision Support System / DSS, 9 butir pernyataan). Hasil rekapitulasi data kuesioner dari seluruh 35 responden dirangkum pada Tabel 4.9."
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
        print("Updated UAT introductory paragraph P#696 with 35 respondents and demographics.")

    elif "Rekapitulasi Hasil Kuesioner Akseptansi Pengguna" in p_text and "Tabel 4." in p_text:
        new_text = "Tabel 4.9 Rekapitulasi Hasil Kuesioner Akseptansi Pengguna (n = 35 Responden)"
        for r in list(p):
            if r.tag.endswith('r'): p.remove(r)
        r = ET.SubElement(p, f"{{{W_NS}}}r")
        rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
        rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rf.set(f"{{{W_NS}}}ascii", "Calibri")
        rf.set(f"{{{W_NS}}}hAnsi", "Calibri")
        sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
        sz.set(f"{{{W_NS}}}val", "22")
        ET.SubElement(rPr, f"{{{W_NS}}}b")
        t = ET.SubElement(r, f"{{{W_NS}}}t")
        t.text = new_text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        print("Updated Tabel 4.9 Caption to n = 35 Responden.")

    elif "Tanda asterisk (*) pada butir pernyataan A.2, A.4, A.6, A.8, dan A.9 menunjukkan pernyataan berorientasi negatif" in p_text:
        new_text = "Tanda asterisk (*) pada butir pernyataan A.2, A.4, A.6, A.8, dan A.9 menunjukkan butir pernyataan berorientasi negatif yang mengadopsi standar baku System Usability Scale (SUS). Pada perhitungan Subtotal Dimensi A dan analisis penerimaan kepuasan pengguna, skor mentah pada butir-butir negatif tersebut telah dikonversi secara terbalik (reverse-coded: 6 - skor mentah) agar searah dengan orientasi kepuasan sistem. Berdasarkan rekapitulasi empiris pada Tabel 4.9, Dimensi Kemudahan dan Antarmuka Aplikasi memperoleh total skor terkonversi sebesar 1.294 dari skor maksimal 1.750, yang menghasilkan rata-rata skor sebesar 3,70 dari 5,00 (tingkat ketercapaian 73,94% dengan kategori 'Baik'). Responden memberikan penilaian sangat tinggi pada daya tarik visual, kejelasan grafik radar, dan indikator speedometer gauge (86,29%), kemudahan operasional sistem (85,71%), susunan tata letak menu navigasi yang logis (84,00%), serta persepsi positif bahwa alur kerja aplikasi tidak terlalu rumit (76,57%). Berdasarkan formulasi standar System Usability Scale (SUS) pada skala 0 hingga 100, sistem ini meraih rata-rata skor SUS sebesar 67,43 (kategori 'Acceptable' / Marginal High, Grade C+ menuju B-), yang membuktikan bahwa antarmuka sistem web Streamlit telah memenuhi ambang batas kelayakan interaksi manusia dan komputer."
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
        print("Updated UAT Dimensi A analysis P#699 with exact 35 respondents and SUS 67.43.")

    elif "Pada Dimensi Relevansi Output dan Kinerja Fitur Sistem Pendukung Keputusan (DSS), sistem mencatatkan performa luar biasa" in p_text:
        new_text = "Pada Dimensi Relevansi Output dan Kinerja Fitur Sistem Pendukung Keputusan (DSS), sistem mencatatkan performa superior dengan total skor sebesar 1.363 dari skor maksimal 1.575, menghasilkan rata-rata skor sebesar 4,33 dari 5,00 (tingkat akseptansi 86,54% dengan kategori 'Sangat Baik'). Seluruh 9 butir pernyataan pada dimensi fitur DSS secara konsisten meraih kategori 'Sangat Baik' dengan persentase di atas 85%. Responden memberikan skor tertinggi pada relevansi keseluruhan sistem sebagai instrumen pendukung keputusan deteksi dini kebangkrutan manufaktur BEI (88,57%), keandalan kanal input data multi-sumber dan pintasan API emiten (87,43%), transparansi komparasi tri-model (87,43%), serta kegunaan ringkasan memo eksekutif dan fitur ekspor laporan (87,43%). Pada analisis umpan balik kualitatif pertanyaan terbuka, mayoritas responden menetapkan 'Dashboard Prediksi dan Visualisasi Tingkat Risiko' sebagai fitur yang paling bermanfaat karena menyajikan indikator status kebangkrutan dan probabilitas risiko XGBoost secara tegas tanpa mengharuskan pengguna menghitung rasio secara manual. Di samping itu, responden menyampaikan saran konstruktif untuk pengembangan sistem ke depan, antara lain: penyederhanaan tata letak dashboard agar tidak terlalu padat informasi bagi pengguna pemula, penyesuaian kontras warna visualisasi, serta usulan penambahan fitur peramalan tren keuangan tahun berikutnya (multi-year forward forecasting)."
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
        print("Updated UAT Dimensi B analysis P#700 with exact 35 respondents (86.54% Sangat Baik).")

    elif "Secara keseluruhan, hasil pengujian validasi ahli dengan tingkat kelayakan 100%" in p_text:
        new_text = "Secara keseluruhan, hasil pengujian validasi pakar keuangan yang mencatatkan tingkat kelayakan 100% (seluruh 10 butir berstatus OK dan dinyatakan Sangat Layak) dipadukan dengan tingkat akseptansi responden pengguna sebesar 86,54% pada dimensi fitur DSS (kategori 'Sangat Baik') serta skor agregat seluruh butir sebesar 79,91% (kategori 'Baik' / Layak Diimplementasikan) membuktikan bahwa sistem pendukung keputusan prediksi financial distress yang dibangun telah tervalidasi secara akademis, fungsional, dan operasional. Sistem ini terbukti memiliki nilai guna praktis yang tinggi dan siap diimplementasikan sebagai instrumen skrining dan mitigasi risiko finansial pada industri manufaktur di Bursa Efek Indonesia."
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
        print("Updated UAT overall summary P#701.")

    # 3. Update Subbab 4.3.6: P#725 and P#726
    elif "Sejalan dengan validasi pakar, hasil evaluasi akseptansi pengguna (User Acceptance Test) yang melibatkan" in p_text:
        new_text = "Sejalan dengan validasi pakar, hasil evaluasi akseptansi pengguna (User Acceptance Testing / UAT) yang melibatkan 35 responden lapangan dari berbagai kalangan analis pasar modal, akademisi, praktisi IT, dan pelaku industri menghasilkan rata-rata skor akseptansi agregat sebesar 79,91% dengan kategori 'Baik / Layak Diimplementasikan', di mana pada Dimensi Relevansi Output dan Kinerja Fitur DSS capaiannya menembus 86,54% (kategori 'Sangat Baik'). Responden menilai bahwa antarmuka web Streamlit yang dirancang memiliki tata letak navigasi yang logis dan modern. Fitur visualisasi speedometer (gauge meter) probabilitas risiko XGBoost, diagram radar 4 rasio, dan kartu status komparasi tri-model dinilai sangat mempermudah pemahaman kondisi emiten secara cepat tanpa harus menafsirkan angka-angka statistik yang rumit secara manual. Skor System Usability Scale (SUS) yang mencapai 67,43 mengonfirmasi bahwa aplikasi dapat diterima dengan baik (acceptable) oleh pengguna dari berbagai latar belakang kompetensi."
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
        print("Updated Subbab 4.3.6 P#725 with 35 respondents discussion.")

    elif "Tingginya skor penerimaan dari para responden dan pengakuan kelayakan dari pakar keuangan membuktikan bahwa sistem" in p_text:
        new_text = "Tingginya skor penerimaan dari 35 responden lapangan (86,54% pada kinerja fitur DSS) dan pengakuan kelayakan mutlak dari pakar keuangan (100% status OK) membuktikan bahwa sistem pendukung keputusan prediksi financial distress ini berhasil menjembatani kesenjangan antara kecanggihan algoritma machine learning di ranah akademis dan kebutuhan praktis di industri pasar modal Indonesia. Sistem terbukti tidak hanya andal sebagai alat deteksi dini (early warning system), tetapi juga berdaya guna tinggi sebagai instrumen formulasi kebijakan restrukturisasi modal dan utang perusahaan manufaktur."
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
        print("Updated Subbab 4.3.6 P#726.")

# 4. Update Table 4.9 cell values directly
table_4_9 = None
for tbl in body.iter(f"{{{W_NS}}}tbl"):
    tbl_text = "".join(tbl.itertext())
    if "Dimensi Kemudahan dan Antarmuka Aplikasi" in tbl_text and "Dimensi Relevansi Output" in tbl_text:
        table_4_9 = tbl
        break

if table_4_9 is not None:
    print("Found Table 4.9. Updating cell values for 35 respondents...")
    row_updates = {
        2:  ("150", "175", "4.29", "85.71%", "Sangat Baik"),
        3:  ("134", "175", "3.83", "76.57%", "Baik"),
        4:  ("147", "175", "4.20", "84.00%", "Sangat Baik"),
        5:  ("118", "175", "3.37", "67.43%", "Baik"),
        6:  ("151", "175", "4.31", "86.29%", "Sangat Baik"),
        7:  ("121", "175", "3.46", "69.14%", "Baik"),
        8:  ("134", "175", "3.83", "76.57%", "Baik"),
        9:  ("111", "175", "3.17", "63.43%", "Baik"),
        10: ("95",  "175", "2.71", "54.29%", "Cukup Baik"),
        11: ("133", "175", "3.80", "76.00%", "Baik"),
        12: ("1294", "1750", "3.70", "73.94%", "Baik"), # Subtotal A
        14: ("153", "175", "4.37", "87.43%", "Sangat Baik"),
        15: ("151", "175", "4.31", "86.29%", "Sangat Baik"),
        16: ("149", "175", "4.26", "85.14%", "Sangat Baik"),
        17: ("150", "175", "4.29", "85.71%", "Sangat Baik"),
        18: ("153", "175", "4.37", "87.43%", "Sangat Baik"),
        19: ("150", "175", "4.29", "85.71%", "Sangat Baik"),
        20: ("149", "175", "4.26", "85.14%", "Sangat Baik"),
        21: ("153", "175", "4.37", "87.43%", "Sangat Baik"),
        22: ("155", "175", "4.43", "88.57%", "Sangat Baik"),
        23: ("1363", "1575", "4.33", "86.54%", "Sangat Baik"), # Subtotal B
        24: ("2657", "3325", "4.00", "79.91%", "Baik / Layak") # Total Agregat
    }
    
    tr_elements = table_4_9.findall(f"{{{W_NS}}}tr")
    for r_idx, (tot, maks, rata, pct, kat) in row_updates.items():
        if r_idx < len(tr_elements):
            tc_elements = tr_elements[r_idx].findall(f"{{{W_NS}}}tc")
            if len(tc_elements) >= 7:
                def set_tc_text(tc, new_val, is_bold=False):
                    p_el = tc.find(f"{{{W_NS}}}p")
                    if p_el is None: p_el = ET.SubElement(tc, f"{{{W_NS}}}p")
                    for r_child in list(p_el):
                        if r_child.tag.endswith('r'): p_el.remove(r_child)
                    r_el = ET.SubElement(p_el, f"{{{W_NS}}}r")
                    rPr = ET.SubElement(r_el, f"{{{W_NS}}}rPr")
                    rf = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
                    rf.set(f"{{{W_NS}}}ascii", "Calibri")
                    rf.set(f"{{{W_NS}}}hAnsi", "Calibri")
                    sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
                    sz.set(f"{{{W_NS}}}val", "20") # 10pt
                    if is_bold: ET.SubElement(rPr, f"{{{W_NS}}}b")
                    t_el = ET.SubElement(r_el, f"{{{W_NS}}}t")
                    t_el.text = new_val
                    t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

                bold_row = (r_idx in [12, 23, 24])
                set_tc_text(tc_elements[2], tot, bold_row)
                set_tc_text(tc_elements[3], maks, bold_row)
                set_tc_text(tc_elements[4], rata, bold_row)
                set_tc_text(tc_elements[5], pct, bold_row)
                set_tc_text(tc_elements[6], kat, bold_row)
                
                if r_idx == 24:
                    set_tc_text(tc_elements[1], "Rekapitulasi Skor Akseptansi Pengguna Sistem Web Streamlit (n = 35 Responden)", True)

    print("Table 4.9 cell values successfully updated to 35 respondents!")

# 5. Insert BAB V KESIMPULAN DAN SARAN right before REAL DAFTAR PUSTAKA
children = list(body)
daftar_pustaka_idx = None
for idx in range(len(children) - 1, 500, -1):
    t = "".join(children[idx].itertext()).strip()
    if t == "DAFTAR PUSTAKA":
        daftar_pustaka_idx = idx
        break

print(f"REAL Index DAFTAR PUSTAKA: {daftar_pustaka_idx}")

if daftar_pustaka_idx is not None:
    bab5_elements = []
    
    # Page break spacer before Bab V
    p_break = create_p("", space_before="240", space_after="240")
    r_br = ET.SubElement(p_break, f"{{{W_NS}}}r")
    ET.SubElement(r_br, f"{{{W_NS}}}br").set(f"{{{W_NS}}}type", "page")
    bab5_elements.append(p_break)
    
    # BAB V Title
    p_title = create_p("BAB V KESIMPULAN DAN SARAN", font_name="Calibri", sz="28", bold=True, jc="center", line="480", space_before="240", space_after="180", heading_level=1)
    bab5_elements.append(p_title)
    
    # 5.1 Kesimpulan
    p_h51 = create_p("5.1 Kesimpulan", font_name="Calibri", sz="24", bold=True, jc="left", line="480", space_before="180", space_after="120", heading_level=2)
    bab5_elements.append(p_h51)
    
    p_k_intro = create_p("Berdasarkan keseluruhan tahapan perancangan arsitektur perangkat lunak, pembuatan modul komputasi, dan pengujian empiris yang telah dilakukan pada sistem pendukung keputusan (decision support system) prediksi financial distress industri manufaktur di Bursa Efek Indonesia (BEI), dapat ditarik beberapa kesimpulan utama sebagai berikut:", jc="both")
    bab5_elements.append(p_k_intro)
    
    kesimpulan_points = [
        "1. Sistem pendukung keputusan prediksi financial distress berhasil dirancang dan diimplementasikan secara utuh berbasis web menggunakan framework Streamlit dengan arsitektur perangkat lunak berlapis (layered architecture). Sistem mengintegrasikan pipeline ETL data multi-kanal (ekstraksi berkas XBRL Excel BEI, parsing laporan keuangan PDF, pengambilan data otomatis, dan koreksi manual) yang dilengkapi lapisan pengaman akuntansi (Accounting Validation Guardrail) untuk menjamin keseimbangan persamaan neraca fundamental (Aset = Liabilitas + Ekuitas) serta aturan winsorizing/capping rasio keuangan sebelum diproses oleh mesin inferensi.",
        "2. Algoritma Extreme Gradient Boosting (XGBoost) yang dikonfigurasi dengan pembobotan kompensasi ketidakseimbangan kelas (scale_pos_weight = 11,38) pada master dataset 3.770 observasi data panel (2014–2026) dari 290 emiten manufaktur terbukti secara empiris sebagai model terbaik (champion model). Pada data pengujian independen sebanyak 754 sampel (hold-out 20%), XGBoost mencatatkan performa klasifikasi tertinggi dengan Akurasi sebesar 96,42%, ROC-AUC sebesar 0,9400, PR-AUC sebesar 0,8558, Sensitivitas (Recall) sebesar 80,33%, Spesifisitas sebesar 97,84%, dan F1-Score sebesar 78,40%, secara konsisten mengungguli model re-estimasi empiris MDA Fisher BEI (Akurasi 96,02%, ROC-AUC 0,9200) serta model statistik klasik Altman Z''-Score 1995 (Akurasi 95,76%, ROC-AUC 0,8800).",
        "3. Keunggulan paling krusial model XGBoost terletak pada kemampuannya meminimalkan risiko Type II Error (False Negative) hingga tersisa hanya 12 kasus (1,59% dari total data uji), lebih unggul dibandingkan model Altman Z'' klasik yang meloloskan 14 kasus gagal bayar (default). Dalam konteks manajemen risiko perbankan dan investasi pasar modal, peminimalan False Negative memberikan perlindungan modal yang vital terhadap ancaman kerugian modal absolut (direct capital loss) akibat keterlambatan deteksi kebangkrutan emiten.",
        "4. Pengujian validasi silang berstrata (Stratified 5-Fold Cross Validation) pada keseluruhan 3.770 observasi membuktikan stabilitas dan ketahanan (robustness) generalisasi model XGBoost yang sangat prima dengan rata-rata Akurasi sebesar 96,42% (+/- 0,21%) dan skor ROC-AUC sebesar 0,9400 (+/- 0,0028). Dari dimensi efisiensi komputasi, model XGBoost membukukan waktu inferensi rata-rata sebesar 0,85 milidetik per sampel, membuktikan kesiapan sistem untuk melayani inferensi berkecepatan tinggi pada lingkungan web interaktif waktu-nyata.",
        "5. Pengujian keandalan perangkat lunak dan penerimaan pengguna mengonfirmasi validitas sistem secara menyeluruh. Pengujian kotak hitam (Black Box Testing) membukukan tingkat keberhasilan fungsional 100% pada 15 skenario operasional. Validasi substansi oleh praktisi ahli keuangan pasar modal (PT Mirae Asset Sekuritas) memperoleh penilaian 100% OK dengan predikat 'Sangat Layak'. Sementara itu, pengujian penerimaan pengguna (User Acceptance Testing / UAT) kepada 35 responden lapangan menghasilkan tingkat akseptansi sebesar 86,54% (kategori 'Sangat Baik') pada dimensi Relevansi Output dan Kinerja Fitur DSS serta skor agregat 79,91% (kategori 'Baik'). Fitur preskriptif dekomposisi pemicu krisis (financial distress drivers) dan simulator skenario titik impas (breakeven point) restrukturisasi terbukti mentransformasikan sistem menjadi instrumen pendukung keputusan strategis yang aplikatif bagi analis, kreditur, dan investor pasar modal."
    ]
    for pt in kesimpulan_points:
        bab5_elements.append(create_p(pt, jc="both"))
        
    # 5.2 Saran
    p_h52 = create_p("5.2 Saran", font_name="Calibri", sz="24", bold=True, jc="left", line="480", space_before="180", space_after="120", heading_level=2)
    bab5_elements.append(p_h52)
    
    p_s_intro = create_p("Berdasarkan temuan penelitian, hasil evaluasi empiris, serta masukan konstruktif yang diperoleh dari pengujian validasi ahli dan kuesioner pengguna lapangan, diajukan beberapa saran bagi pengembangan sistem di masa mendatang:", jc="both")
    bab5_elements.append(p_s_intro)
    
    saran_points = [
        "1. Pengembangan Fitur Peramalan Tren Keuangan Masa Depan (Multi-Year Forward Forecasting): Sistem disarankan untuk mengintegrasikan algoritma peramalan deret waktu (seperti Long Short-Term Memory / LSTM atau Temporal Fusion Transformer) guna memproyeksikan pergerakan rasio keuangan dan lintasan solvabilitas emiten 1 hingga 3 tahun ke depan, sehingga pengguna dapat mengantisipasi gejala krisis sebelum laporan keuangan tahunan resmi dipublikasikan.",
        "2. Otomatisasi Pipeline Pengambilan Data Real-Time Terintegrasi: Backend sistem disarankan untuk dihubungkan secara langsung melalui Application Programming Interface (API) resmi Bursa Efek Indonesia (IDX Data Feed) atau penyedia data pasar finansial global (seperti Yahoo Finance API atau Bloomberg Data License) guna mengotomatisasi pembaruan data laporan keuangan triwulanan dan tahunan secara berkesinambungan tanpa memerlukan proses pengunggahan manual.",
        "3. Penyederhanaan Tata Letak Antarmuka & Mode Fleksibel (Adaptive UI / Dual Mode): Untuk mengakomodasi umpan balik responden pengguna umum terkait kepadatan visual pada antarmuka dashboard, sistem disarankan menyediakan fitur mode ganda: 'Mode Ringkas / Pemula' yang menyajikan informasi status risiko dan speedometer probabilitas secara minimalis, serta 'Mode Lanjutan / Profesional' yang menyajikan metrik evaluasi teknis, visualisasi radar, dan rincian dekomposisi mendalam.",
        "4. Perluasan Pemodelan Prediksi ke Sektor Industri Non-Manufaktur: Penelitian lanjutan disarankan memperluas cakupan sistem ke sektor industri lain yang tercatat di BEI (seperti sektor perbankan, keuangan, properti, dan pertambangan) dengan mengadaptasi indikator rasio keuangan spesifik sektor (misalnya rasio kecukupan modal CAMELS untuk perbankan) agar menghasilkan model komparatif yang komprehensif bagi seluruh emiten di bursa efek.",
        "5. Pengembangan Aplikasi Berbasis Mobile Native / Progressive Web App (PWA): Untuk meningkatkan fleksibilitas dan aksesibilitas bagi investor individu dan analis lapangan, sistem disarankan untuk dikembangkan menjadi aplikasi mobile lintas platform (menggunakan framework Flutter atau React Native) yang dilengkapi fitur notifikasi peringatan dini (push notification) secara otomatis saat emiten yang dipantau mengalami pemburukan indikator keuangan."
    ]
    for pt in saran_points:
        bab5_elements.append(create_p(pt, jc="both"))
        
    bab5_elements.append(create_p("", space_before="120", space_after="120"))
    
    # Insert right at daftar_pustaka_idx
    for offset, el in enumerate(bab5_elements):
        body.insert(daftar_pustaka_idx + offset, el)
        
    print(f"BAB V KESIMPULAN DAN SARAN ({len(bab5_elements)} elemen) berhasil disisipkan di posisi P#{daftar_pustaka_idx} tepat sebelum DAFTAR PUSTAKA!")

# Save modified document.xml
doc_tree.write(doc_xml_path, xml_declaration=True, encoding='utf-8')
print("document.xml berhasil disimpan.")

# Repack into update5 (AutoRecovered).docx
output_docx = 'update5 (AutoRecovered).docx'
print(f"Mengemas ulang dokumen ke {output_docx}...")
with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as zout:
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, temp_dir)
            zout.write(abs_path, rel_path)

shutil.rmtree(temp_dir)
print(f"Revisi selesai! Dokumen tersimpan di: {output_docx}")
