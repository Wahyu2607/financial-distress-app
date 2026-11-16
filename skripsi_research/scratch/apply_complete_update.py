import zipfile
import xml.etree.ElementTree as ET
import os
import shutil

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.microsoft.com/office/word/2010/wordml"
ET.register_namespace('w', W_NS)
ET.register_namespace('w14', M_NS)

from setup_ready import make_p, make_caption, build_table
from build_tables import tbl_4_8, tbl_4_9

# Read update4.docx
source_file = 'update4.docx'
target_file = 'update4.docx'

with zipfile.ZipFile(source_file, 'r') as zin:
    xml_content = zin.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': W_NS}
body = root.find('w:body', ns)

elements = list(body)

# Identify the exact positions
# 1. Subab 4.2.10 starts at element 786 (Heading 'Validasi Ahli dan Hasil Kuesioner Pengguna')
# Previously:
# 786: Heading
# 787: Intro to Expert Validation
# 788: Caption Table 4.8
# 789: Table 4.8
# 790: Intro to User Acceptance Test
# 791: Caption Table 4.9
# 792: Table 4.9
# 793: Concluding paragraph
# 794: Heading 'Pembahasan'
#
# 2. In Pembahasan:
# 815: Heading 'Pembahasan Validasi Ahli dan Kuesioner Responden'
# 816: Expert validation discussion
# 817: User questionnaire discussion
# 818: Concluding discussion

# Verify element 786 text
t786 = ''.join([n.text for n in elements[786].iter(f"{{{W_NS}}}t") if n.text])
print("Element 786:", t786)
assert "Validasi Ahli" in t786

# Verify element 794 text
t794 = ''.join([n.text for n in elements[794].iter(f"{{{W_NS}}}t") if n.text])
print("Element 794:", t794)
assert "Pembahasan" in t794

# Verify element 815 text
t815 = ''.join([n.text for n in elements[815].iter(f"{{{W_NS}}}t") if n.text])
print("Element 815:", t815)
assert "Pembahasan Validasi Ahli" in t815

# Prepare new elements for 4.2.10 (to be inserted between 786 and 794)
p_intro_pakar = make_p(
    "Pengujian validasi substansi dan penerimaan sistem dilakukan secara komprehensif melalui dua pendekatan, yaitu pengujian validasi oleh pakar (expert judgment) dan pengujian penerimaan pengguna lapangan (User Acceptance Testing/UAT). Validasi ahli dilakukan oleh praktisi dan analis keuangan pasar modal menggunakan instrumen lembar evaluasi User Acceptance Test terstruktur. Pengujian ini bertujuan untuk memvalidasi kelayakan parameter akuntansi, ketepatan formula rasio diskriminan (X1 - X5), fleksibilitas alur ekstraksi multi-sumber data, konsistensi hasil klasifikasi tiga model (Altman Z''-Score, MDA Fisher BEI, dan Machine Learning XGBoost), ketajaman deteksi dini (early warning system), serta kepatuhan terhadap klausul batasan hukum (disclaimer) bahwa sistem berfungsi sebagai instrumen pendukung keputusan (Decision Support System) skrining risiko awal dan bukan merupakan vonis kepailitan formal pengadilan niaga. Hasil pengujian UAT oleh pakar keuangan disajikan pada Tabel 4.8.",
    style="paragraf"
)

caption_4_8 = make_caption("Tabel 4.8 Hasil Pengujian User Acceptance Test (UAT) oleh Pakar Analisis Keuangan")

p_eval_pakar = make_p(
    "Berdasarkan hasil pengujian pada Tabel 4.8, seluruh 10 butir pengujian fungsional dan substansial yang diujikan kepada pakar dinyatakan memenuhi standar kelayakan (100% berstatus OK). Validator ahli keuangan memberikan catatan positif bahwa formula rasio keuangan dan aturan capping telah selaras dengan literatur Altman (1995/2017), penyandingan tiga model klasifikasi berjalan konsisten dan objektif, visualisasi gauge meter komunikatif, modul early warning logis, serta penegasan klausul disclaimer DSS dicantumkan secara proporsional. Pada lembar pengesahan UAT, pakar memberikan keputusan akhir bahwa aplikasi sistem web ini dinyatakan LAYAK untuk diimplementasikan.",
    style="paragraf"
)

p_intro_responden = make_p(
    "Selain validasi pakar, pengujian penerimaan pengguna (User Acceptance Testing) dilakukan kepada 13 responden lapangan dengan beragam latar belakang profesi, meliputi akademisi/mahasiswa ekonomi dan bisnis, analis keuangan/praktisi pasar modal, praktisi IT/data science, pegawai, dan pengguna umum. Pengujian menggunakan instrumen kuesioner skala Likert 5 poin (1: Sangat Tidak Setuju hingga 5: Sangat Setuju) yang mengukur dua dimensi evaluasi utama: (1) Aspek Kemudahan dan Antarmuka Aplikasi (System Usability / UI & UX, 10 butir pernyataan) dan (2) Relevansi Output dan Kinerja Fitur Sistem Pendukung Keputusan (Decision Support System, 9 butir pernyataan). Hasil rekapitulasi data kuesioner dari seluruh 13 responden dirangkum pada Tabel 4.9.",
    style="paragraf"
)

caption_4_9 = make_caption("Tabel 4.9 Rekapitulasi Hasil Kuesioner Akseptansi Pengguna Sistem Web Streamlit (n = 13 Responden)")

p_eval_dim1 = make_p(
    "Tanda asterisk (*) pada butir pernyataan A.2, A.4, A.6, A.8, dan A.9 menunjukkan pernyataan berorientasi negatif yang mengadopsi standar baku System Usability Scale (SUS). Pada perhitungan Subtotal Dimensi A dan analisis penerimaan positif, skor mentah pada butir-butir negatif tersebut telah dikonversi secara terbalik (reverse-coded: 6 - skor mentah) agar searah dengan orientasi kepuasan sistem. Berdasarkan rekapitulasi Tabel 4.9, Dimensi Kemudahan dan Antarmuka Aplikasi memperoleh rata-rata skor sebesar 3,58 dari 5,00 (tingkat akseptansi 71,69% dengan kategori 'Baik'). Responden memberikan penilaian sangat tinggi pada daya tarik visual, kejelasan grafik radar, dan indikator speedometer gauge (86,15%), susunan tata letak menu navigasi yang logis (84,62%), kemudahan pengoperasian aplikasi (83,08%), serta kelayakan sistem untuk digunakan oleh analis dan investor (83,08%). Sementara itu, perolehan pada butir alur dan kebutuhan panduan teknis mengindikasikan bahwa responden non-teknis memerlukan sedikit adaptasi awal terhadap alur pengolahan pos laporan keuangan.",
    style="paragraf"
)

p_eval_dim2 = make_p(
    "Pada Dimensi Relevansi Output dan Kinerja Fitur Sistem Pendukung Keputusan (DSS), sistem mencatatkan performa luar biasa dengan rata-rata skor sebesar 4,32 dari 5,00 (tingkat akseptansi 86,32% dengan kategori 'Sangat Baik'). Seluruh 9 butir pernyataan fitur DSS memperoleh persentase ketercapaian di atas 84%. Responden memberikan skor tertinggi pada keandalan fitur input data multi-sumber (89,23%) dan kejelasan fitur komparasi tri-model (89,23%), disusul oleh kelengkapan metrik evaluasi model AI (87,69%), serta kejelasan zonasi risiko dan visualisasi gauge probabilitas XGBoost (86,15%). Umpan balik kualitatif responden secara konsisten menetapkan Dashboard Prediksi sebagai fitur yang paling bermanfaat karena menyajikan visualisasi risiko kebangkrutan yang jelas, tegas, dan mudah diinterpretasikan tanpa harus menghitung angka rasio secara manual. Responden juga memberikan saran konstruktif untuk pengembangan sistem ke depan, khususnya penambahan fitur peramalan tren tahun berikutnya (multi-year forward forecasting).",
    style="paragraf"
)

p_concl_4_2_10 = make_p(
    "Secara keseluruhan, hasil pengujian validasi ahli dengan tingkat kelayakan 100% (seluruh 10 butir berstatus OK dan dinyatakan LAYAK) yang dipadukan dengan tingkat akseptansi responden pengguna sebesar 86,32% pada dimensi fitur DSS (kategori 'Sangat Baik') serta skor agregat 78,62% (kategori 'Baik') membuktikan bahwa sistem pendukung keputusan prediksi financial distress yang dibangun telah tervalidasi secara akademis, fungsional, dan operasional. Sistem ini terbukti memiliki nilai guna praktis yang tinggi dan siap diimplementasikan sebagai instrumen skrining dan mitigasi risiko finansial pada industri manufaktur di Bursa Efek Indonesia.",
    style="paragraf"
)

new_4_2_10_elements = [
    p_intro_pakar,
    caption_4_8,
    tbl_4_8,
    p_eval_pakar,
    p_intro_responden,
    caption_4_9,
    tbl_4_9,
    p_eval_dim1,
    p_eval_dim2,
    p_concl_4_2_10
]

# Prepare new elements for Pembahasan 4.3.6
p_pem_pakar = make_p(
    "Hasil pengujian validasi substansi melalui lembar instrumen User Acceptance Test (UAT) oleh praktisi dan analis keuangan pasar modal menghasilkan tingkat keberhasilan 100%, di mana seluruh 10 butir skenario pengujian fungsional dan analitis berstatus OK sehingga aplikasi dinyatakan LAYAK. Penilaian penuh dari pakar menegaskan bahwa metodologi penyandingan tiga model (Tri-Model Diagnosis: Altman Z'', MDA Baru, dan XGBoost) memiliki landasan teoretis akuntansi dan statistika yang kuat serta parameter pembentukan rasio diskriminan X1-X5 yang akurat. Pakar secara khusus memberikan apresiasi positif terhadap integrasi fitur dekomposisi pemicu krisis (financial distress drivers), indikator peringatan dini (early warning), serta penegasan klausul batasan hukum (disclaimer) bahwa sistem berfungsi sebagai alat pendukung keputusan skrining risiko awal dan bukan merupakan opini audit akuntan publik atau vonis pailit hukum pengadilan niaga.",
    style="paragraf"
)

p_pem_responden = make_p(
    "Sejalan dengan validasi pakar, hasil evaluasi akseptansi pengguna lapangan (User Acceptance Testing) yang melibatkan 13 responden dengan latar belakang analis, investor, akademisi, praktisi IT, dan pegawai menghasilkan rata-rata skor sebesar 86,32% pada dimensi Relevansi Output dan Kinerja Fitur DSS (kategori 'Sangat Baik') serta skor agregat keseluruhan sebesar 78,62% (kategori 'Baik'). Responden menilai bahwa antarmuka web Streamlit yang dirancang memiliki estetika modern dan kemudahan navigasi yang solid. Visualisasi speedometer (gauge meter) probabilitas risiko XGBoost dan kartu konsensus tri-model dinilai sebagai komponen yang paling berdaya guna tinggi karena mempermudah interpretasi derajat kerentanan emiten secara cepat tanpa harus menafsirkan formula matematika yang rumit secara manual.",
    style="paragraf"
)

p_pem_concl = make_p(
    "Tingginya skor penerimaan dari responden lapangan serta konfirmasi kelayakan 100% dari pakar pasar modal membuktikan bahwa sistem pendukung keputusan berbasis web yang dikembangkan dalam penelitian ini tidak hanya unggul secara akademis dalam mencapai akurasi prediksi 96,42% dan recall 80,33%, tetapi juga memiliki nilai guna implementatif yang nyata sebagai instrumen mitigasi risiko finansial dan sistem peringatan dini kebangkrutan bagi para investor dan kreditur pada industri manufaktur di Bursa Efek Indonesia.",
    style="paragraf"
)

# Now, let's construct the new body list
# Find elements 786 and 794
body_children = list(body)
idx_786 = body_children.index(elements[786])
idx_794 = body_children.index(elements[794])
idx_815 = body_children.index(elements[815])
idx_818 = body_children.index(elements[818])

print(f"Indices: 786={idx_786}, 794={idx_794}, 815={idx_815}, 818={idx_818}")

# Create new list of children
new_body = []
for i, child in enumerate(body_children):
    if i <= idx_786:
        new_body.append(child)
        if i == idx_786:
            # Insert new 4.2.10 elements
            new_body.extend(new_4_2_10_elements)
    elif idx_786 < i < idx_794:
        # Skip old 4.2.10 elements (787 to 793)
        continue
    elif idx_794 <= i <= idx_815:
        new_body.append(child)
        if i == idx_815:
            # Insert new pembahasan elements
            new_body.append(p_pem_pakar)
            new_body.append(p_pem_responden)
            new_body.append(p_pem_concl)
    elif idx_815 < i <= idx_818:
        # Skip old pembahasan paragraphs (816, 817, 818)
        continue
    else:
        new_body.append(child)

# Clear body and append new_body
body.clear()
for item in new_body:
    body.append(item)

# Serialize root back to XML
new_xml = ET.tostring(root, encoding='utf-8', xml_declaration=True)

# Write to temp docx first
temp_docx = 'scratch/temp_update4.docx'
with zipfile.ZipFile(source_file, 'r') as zin:
    with zipfile.ZipFile(temp_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == 'word/document.xml':
                zout.writestr(item, new_xml)
            else:
                zout.writestr(item, zin.read(item.filename))

print("Temp docx written successfully. Verifying file size:", os.path.getsize(temp_docx))

# Replace original update4.docx
shutil.copyfile(temp_docx, target_file)
print("Successfully replaced update4.docx!")
