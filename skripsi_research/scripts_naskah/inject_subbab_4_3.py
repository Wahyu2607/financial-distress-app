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

def create_heading3(text):
    p = ET.Element(f"{{{W_NS}}}p")
    pPr = ET.SubElement(p, f"{{{W_NS}}}pPr")
    pStyle = ET.SubElement(pPr, f"{{{W_NS}}}pStyle")
    pStyle.set(f"{{{W_NS}}}val", "heading30")
    numPr = ET.SubElement(pPr, f"{{{W_NS}}}numPr")
    ilvl = ET.SubElement(numPr, f"{{{W_NS}}}ilvl")
    ilvl.set(f"{{{W_NS}}}val", "0")
    numId = ET.SubElement(numPr, f"{{{W_NS}}}numId")
    numId.set(f"{{{W_NS}}}val", "36")
    spacing = ET.SubElement(pPr, f"{{{W_NS}}}spacing")
    spacing.set(f"{{{W_NS}}}line", "480")
    spacing.set(f"{{{W_NS}}}lineRule", "auto")
    spacing.set(f"{{{W_NS}}}before", "120")
    spacing.set(f"{{{W_NS}}}after", "60")
    rPr_p = ET.SubElement(pPr, f"{{{W_NS}}}rPr")
    rFonts_p = ET.SubElement(rPr_p, f"{{{W_NS}}}rFonts")
    rFonts_p.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts_p.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    b_p = ET.SubElement(rPr_p, f"{{{W_NS}}}b")
    sz_p = ET.SubElement(rPr_p, f"{{{W_NS}}}sz")
    sz_p.set(f"{{{W_NS}}}val", "24")
    
    r = ET.SubElement(p, f"{{{W_NS}}}r")
    rPr = ET.SubElement(r, f"{{{W_NS}}}rPr")
    rFonts = ET.SubElement(rPr, f"{{{W_NS}}}rFonts")
    rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
    rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    b = ET.SubElement(rPr, f"{{{W_NS}}}b")
    sz = ET.SubElement(rPr, f"{{{W_NS}}}sz")
    sz.set(f"{{{W_NS}}}val", "24")
    t = ET.SubElement(r, f"{{{W_NS}}}t")
    t.set(f"{{{XML_NS}}}space", "preserve")
    t.text = text
    return p

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

    target_idx = -1
    for idx, child in enumerate(body):
        txt = get_text(child).lower()
        if txt == "pembahasan":
            target_idx = idx
            break

    if target_idx == -1:
        print("Error: Heading 'Pembahasan' not found in document.")
        return

    print(f"Found 'Pembahasan' at index {target_idx}")

    elements_to_insert = []

    # Pengantar 4.3 Pembahasan
    p_intro = (
        "Pada bagian pembahasan ini, peneliti menguraikan interpretasi teoretis, analisis komparatif, dan implikasi "
        "manajerial dari keseluruhan temuan empiris yang diperoleh pada tahap pengujian. Pembahasan difokuskan pada pemaknaan "
        "ilmiah atas karakteristik data pasar modal Indonesia, hubungan antar-rasio fundamental keuangan, evaluasi keunggulan "
        "komputasi algoritma XGBoost dibandingkan model statistik diskriminan konvensional, stabilitas model dalam validasi "
        "silang, keandalan fungsional antarmuka sistem web Streamlit, serta konfirmasi kelayakan operasional berdasarkan penilaian "
        "ahli keuangan dan responden pengguna."
    )
    elements_to_insert.append(create_p(p_intro))

    # 4.3.1 Pembahasan Distribusi Kelas dan Korelasi Data
    elements_to_insert.append(create_heading3("4.3.1 Pembahasan Distribusi Kelas dan Korelasi Data"))
    p_4_3_1_a = (
        "Hasil pengujian distribusi variabel target menunjukkan adanya ketidakseimbangan kelas (class imbalance) yang nyata pada "
        "industri manufaktur di Bursa Efek Indonesia, di mana dari 704 data observasi laporan keuangan tahunan yang dihimpun, "
        "sebanyak 574 observasi (81,53%) merupakan emiten sehat (Non-Distress) dan 130 observasi (18,47%) tergolong ke dalam emiten "
        "yang mengalami kesulitan keuangan (Distress). Kondisi asimetris ini secara empiris sangat logis dan merefleksikan keadaan riil "
        "perekonomian nasional pasca-pemulihan ekonomi, di mana sebagian besar emiten manufaktur publik mampu mempertahankan operasional "
        "dan struktur modalnya, sementara emiten yang mengalami krisis likuiditas dan defisit saldo laba merupakan kelompok minoritas."
    )
    elements_to_insert.append(create_p(p_4_3_1_a))

    p_4_3_1_b = (
        "Dari perspektif pembelajaran mesin (machine learning), disparitas rasio kelas sebesar 1 : 4,41 ini menghadirkan tantangan "
        "metodologis yang kritis. Apabila algoritma dilatih tanpa mekanisme pembobotan khusus, model cenderung mengalami bias "
        "ke arah kelas mayoritas (perusahaan sehat) dan mengabaikan kelas minoritas (perusahaan krisis), yang berujung pada tingginya "
        "kesalahan tipe II (False Negative). Penerapan parameter penyeimbang bobot kelas scale_pos_weight = 4,41 pada model XGBoost "
        "terbukti berhasil mengoreksi asimetri tersebut secara proporsional. Dengan mengalikan penalti fungsi kerugian gradien pada "
        "sampel kelas distress, algoritma dipaksa untuk memberikan perhatian matematis yang setara dalam mengenali sinyal kebangkrutan, "
        "sehingga menghasilkan sensitivitas deteksi krisis yang sangat tinggi tanpa merusak spesifisitas kelas perusahaan sehat."
    )
    elements_to_insert.append(create_p(p_4_3_1_b))

    p_4_3_1_c = (
        "Selain distribusi kelas, hasil matriks korelasi Pearson membuktikan bahwa seluruh pasangan variabel rasio keuangan independen "
        "(X1 hingga X4) terbebas dari ancaman multikolinearitas. Nilai korelasi linear tertinggi yang tercatat hanya sebesar r = +0,4812 "
        "antara rasio modal kerja (X1) dan rasio saldo laba ditahan (X2), serta r = +0,4231 antara rasio saldo laba (X2) dan rasio laba "
        "operasional EBIT (X3). Nilai-nilai korelasi ini berada jauh di bawah ambang batas kritis multikolinearitas (r < 0,85). Secara "
        "teoretis akuntansi, korelasi moderat antara modal kerja dan saldo laba sangat wajar karena perusahaan yang secara konsisten "
        "mencatatkan akumulasi laba bersih positif umumnya memiliki kapasitas likuiditas operasional lancar yang lebih solid. Rendahnya "
        "korelasi antar-fitur lainnya menegaskan bahwa masing-masing rasio membawa dimensi informasi risiko fundamental yang independen "
        "dan saling melengkapi dalam memprediksi kondisi keuangan emiten."
    )
    elements_to_insert.append(create_p(p_4_3_1_c))

    # 4.3.2 Pembahasan Hasil Evaluasi Model dan Peminimalan Type II Error
    elements_to_insert.append(create_heading3("4.3.2 Pembahasan Hasil Evaluasi Model dan Peminimalan Type II Error"))
    p_4_3_2_a = (
        "Hasil evaluasi komparatif pada data pengujian independen (testing set n = 141) memperlihatkan keunggulan signifikan algoritma "
        "Extreme Gradient Boosting (XGBoost) dibandingkan model diskriminan parametrik konvensional Altman Z''-Score maupun model "
        "re-estimasi empiris Multivariate Discriminant Analysis (MDA) Fisher. Model XGBoost mencatatkan nilai Akurasi tertinggi "
        "sebesar 91,49% dan nilai Area Under ROC Curve (ROC-AUC) sebesar 0,9426, melampaui model MDA Fisher (Akurasi 87,94%, AUC 0,9124) "
        "serta model Altman Z''-Score klasik (Akurasi 80,85%, AUC 0,8320)."
    )
    elements_to_insert.append(create_p(p_4_3_2_a))

    p_4_3_2_b = (
        "Kelemahan mendasar dari formula Altman Z''-Score klasik (1995/2017) dalam penelitian ini terletak pada rendahnya nilai Sensitivitas "
        "atau Recall (hanya 72,73%) dan Presisi (hanya 43,24%). Kegagalan formula klasik ini berakar pada asumsi dasar analisis diskriminan "
        "linear yang mensyaratkan hubungan aditif linear antar-rasio serta distribusi normal multivariat dengan matriks kovarians homogen. "
        "Pada kenyataan empiris pasar modal negara berkembang seperti Indonesia, data rasio keuangan emiten sering kali memiliki distribusi "
        "asimetris, kemencengan (skewness) tinggi, dan pola interaksi risiko yang non-linear. Akibatnya, bobot koefisien standar Altman "
        "yang diestimasi dari data perusahaan Amerika Serikat beberapa dekade lalu tidak lagi sepenuhnya presisi untuk memetakan "
        "karakteristik struktur modal emiten manufaktur di BEI."
    )
    elements_to_insert.append(create_p(p_4_3_2_b))

    p_4_3_2_c = (
        "Sebaliknya, model MDA Fisher berkoefisien baru yang dikalibrasi ulang khusus pada 704 sampel BEI terbukti mampu meningkatkan "
        "akurasi sebesar 7,09% dan menaikkan sensitivitas sebesar 9,09% dibandingkan formula Altman klasik. Hal ini mengonfirmasi "
        "relevansi kalibrasi lokal, di mana penyusutan bobot rasio solvabilitas X4 sebesar 95,9% dan penyesuaian titik potong objektif "
        "0,3844 mencerminkan realitas bahwa emiten manufaktur Indonesia lebih rentan bangkrut akibat defisit saldo laba (X2) dan "
        "kerugian operasional (X3) daripada sekadar rasio utang terhadap ekuitas."
    )
    elements_to_insert.append(create_p(p_4_3_2_c))

    p_4_3_2_d = (
        "Keunggulan paling krusial dari model XGBoost terletak pada kemampuannya menekan kesalahan tipe II (False Negative) hingga "
        "hanya tersisa 2 sampel (1,42% dari total pengujian), jauh lebih unggul dibandingkan model Altman yang mencatatkan 6 kasus "
        "False Negative dan model MDA yang mencatatkan 4 kasus. Dalam manajemen risiko kredit perbankan dan portofolio investasi pasar "
        "modal, kerugian finansial akibat Type I Error (salah memprediksi perusahaan sehat sebagai distress) hanyalah opportunity loss "
        "atau kehilangan peluang keuntungan bunga. Sebaliknya, konsekuensi dari Type II Error (gagal mendeteksi perusahaan yang akan "
        "mengalami default dan mengiranya aman) adalah direct capital loss berupa hilangnya seluruh pokok pinjaman atau kerugian total "
        "investasi saham. Oleh karena itu, kemampuan XGBoost dalam mencapai nilai Sensitivitas 90,91% dan F1-Score 76,92% menjadikannya "
        "model yang paling andal dan berdaya guna tinggi bagi para pengambil keputusan keuangan."
    )
    elements_to_insert.append(create_p(p_4_3_2_d))

    # 4.3.3 Pembahasan Hasil 5-Fold Cross Validation dan Waktu Komputasi
    elements_to_insert.append(create_heading3("4.3.3 Pembahasan Hasil 5-Fold Cross Validation dan Waktu Komputasi"))
    p_4_3_3_a = (
        "Hasil pengujian Stratified 5-Fold Cross Validation pada keseluruhan dataset membuktikan bahwa performa unggul dari model "
        "XGBoost bersifat konsisten melintasi berbagai partisi data dan bukan merupakan akibat dari kebetulan pembagian data latih "
        "dan uji (sampling bias). Rata-rata akurasi yang dicapai sebesar 91,48% dengan standar deviasi yang sangat sempit (+/- 1,03%), "
        "serta rata-rata skor ROC-AUC sebesar 0,9426 dengan standar deviasi +/- 0,0098, membuktikan bahwa model memiliki ketahanan "
        "(robustness) yang prima dan daya generalisasi yang teruji secara statistik."
    )
    elements_to_insert.append(create_p(p_4_3_3_a))

    p_4_3_3_b = (
        "Kestabilan performa ini didukung oleh konfigurasi hiperparameter yang optimal, terutama pembatasan kedalaman pohon keputusan "
        "(max_depth = 2) dan tingkat regularisasi L2 (ridge penalty). Pembatasan max_depth = 2 secara efektif mencegah algoritma "
        "membangun percabangan pohon yang terlampau rumit yang hanya menghafal derau (noise) pada data latih, sekaligus memastikan bahwa "
        "setiap pohon pembelajar lemah (weak learner) fokus menangkap interaksi bivariat antar-rasio fundamental yang paling esensial. "
        "Dipadukan dengan subsampling baris (0,85) dan subsampling fitur (0,85), XGBoost berhasil meredam korelasi antar-pohon sehingga "
        "menghasilkan ansambel yang stabil dan terhindar dari overfitting."
    )
    elements_to_insert.append(create_p(p_4_3_3_b))

    p_4_3_3_c = (
        "Dari dimensi efisiensi komputasi, hasil pengujian mencatat waktu inferensi rata-rata model XGBoost sebesar 0,85 milidetik per "
        "sampel observasi. Meskipun sedikit lebih tinggi dibandingkan model rumus linear sederhana Altman Z'' (0,12 ms) dan MDA (0,14 ms) "
        "karena melibatkan proses evaluasi sekuensial pada 50 pohon keputusan, latensi di bawah 1 milidetik ini tetap sangat gegas "
        "dan berada ratusan kali lipat di bawah ambang batas toleransi sistem web interaktif (1.000 milidetik). Hal ini membuktikan "
        "bahwa arsitektur model XGBoost yang dibangun sangat efisien dan siap melayani inferensi berkecepatan tinggi pada sistem produksi."
    )
    elements_to_insert.append(create_p(p_4_3_3_c))

    # 4.3.4 Pembahasan Pemilihan Model Terbaik
    elements_to_insert.append(create_heading3("4.3.4 Pembahasan Pemilihan Model Terbaik"))
    p_4_3_4_a = (
        "Berdasarkan komparasi multikriteria yang mencakup akurasi agregat, sensitivitas deteksi distress, luas area kurva ROC-AUC, "
        "peminimalan False Negative, dan stabilitas validasi silang, penelitian ini secara tegas menetapkan model Extreme Gradient "
        "Boosting (XGBoost) sebagai model terbaik (champion model) untuk diintegrasikan sebagai mesin inferensi inti pada sistem "
        "pendukung keputusan prediksi financial distress emiten manufaktur BEI."
    )
    elements_to_insert.append(create_p(p_4_3_4_a))

    p_4_3_4_b = (
        "Analisis transparansi model melalui metrik tingkat kepentingan fitur (gain feature importance) memberikan wawasan manajerial "
        "yang sangat berharga mengenai dinamika kegagalan usaha di pasar modal Indonesia. Rasio saldo laba ditahan terhadap total aset (X2) "
        "terbukti memberikan kontribusi terbesar (36,20%), diikuti oleh rasio profitabilitas operasional EBIT terhadap total aset (X3) "
        "sebesar 28,15%. Fakta empiris ini membuktikan bahwa faktor penentu utama kebangkrutan emiten manufaktur di BEI berakar pada "
        "ketidakmampuan perusahaan menghasilkan laba operasional dan akumulasi kerugian masa lalu yang menggerus ekuitas (defisit saldo "
        "laba). Sebaliknya, rasio modal kerja (X1 = 18,45%) dan rasio solvabilitas utang (X4 = 17,20%) berperan sebagai indikator "
        "sekunder. Temuan ini menegaskan bahwa restrukturisasi permodalan saja tidak cukup menyelamatkan emiten tanpa adanya pemulihan "
        "efisiensi operasional dan perbaikan margin laba bersih."
    )
    elements_to_insert.append(create_p(p_4_3_4_b))

    # 4.3.5 Pembahasan Black Box Testing Sistem Web Streamlit
    elements_to_insert.append(create_heading3("4.3.5 Pembahasan Black Box Testing Sistem Web Streamlit"))
    p_4_3_5_a = (
        "Hasil pengujian kotak hitam (Black Box Testing) terhadap 15 skenario fungsional sistem web Streamlit yang mencatatkan tingkat "
        "keberhasilan 100% (seluruh pengujian berstatus Valid) membuktikan bahwa perangkat lunak yang dikembangkan telah memenuhi seluruh "
        "spesifikasi kebutuhan teknis yang dirancang pada Bab III. Sistem terbukti andal dalam menangani berbagai variasi masukan "
        "pengguna, mulai dari autentikasi kredensial, registrasi akun terproteksi passcode, hingga pengolahan laporan keuangan multi-kanal."
    )
    elements_to_insert.append(create_p(p_4_3_5_a))

    p_4_3_5_b = (
        "Secara khusus, pengujian membuktikan keandalan lapisan pelindung akuntansi (Accounting Validation Guardrail) yang mampu "
        "mendeteksi dan memberikan peringatan otomatis apabila neraca masukan tidak seimbang (Aset != Liabilitas + Ekuitas) serta "
        "menyelaraskan disparitas skala satuan nominal secara deterministik. Fitur pemotongan nilai ekstrem (capping) rasio X4 <= 3,00 "
        "juga beroperasi dengan sempurna, sehingga mencegah terjadinya lonjakan skor diskriminan semu pada emiten yang memiliki utang "
        "sangat kecil. Keberhasilan pengujian fungsionalitas ini memastikan bahwa sistem siap digunakan secara stabil oleh pengguna akhir "
        "tanpa risiko kegagalan sistem (system crash)."
    )
    elements_to_insert.append(create_p(p_4_3_5_b))

    # 4.3.6 Pembahasan Validasi Ahli dan Kuesioner Responden
    elements_to_insert.append(create_heading3("4.3.6 Pembahasan Validasi Ahli dan Kuesioner Responden"))
    p_4_3_6_a = (
        "Hasil pengujian validasi substansi oleh dua orang pakar (expert judgment) yang terdiri dari praktisi Analis Keuangan Pasar Modal "
        "dan Akuntan Publik menghasilkan skor rata-rata sebesar 94,50% dengan kategori 'Sangat Layak'. Penilaian tinggi dari para pakar "
        "menegaskan bahwa metodologi penyandingan tiga model (Tri-Model Diagnosis: Altman Z'', MDA Baru, dan XGBoost) memiliki landasan "
        "teoretis akuntansi dan statistika yang kuat. Para ahli secara khusus memberikan apresiasi positif terhadap integrasi fitur "
        "Dekomposisi Pemicu Krisis (Financial Distress Drivers) dan Simulator Skenario 'What-If' Titik Impas Finansial (Breakeven Point "
        "Calculator). Keberadaan simulator tersebut dinilai mentransformasikan sistem dari sekadar alat klasifikasi biner pasif menjadi "
        "sistem pendukung keputusan (Decision Support System) preskriptif yang mampu memberikan rekomendasi kuantitatif mengenai jumlah "
        "modal atau restrukturisasi utang yang diperlukan untuk menyelamatkan emiten dari krisis."
    )
    elements_to_insert.append(create_p(p_4_3_6_a))

    p_4_3_6_b = (
        "Sejalan dengan validasi pakar, hasil evaluasi akseptansi pengguna (User Acceptance Test) yang melibatkan 20 responden analis, "
        "investor, dan akademisi menghasilkan skor rata-rata sebesar 88,60% dengan kategori 'Sangat Baik'. Responden menilai bahwa antarmuka "
        "web Streamlit yang dirancang memiliki tata letak yang bersih, modern, dan intuitif. Fitur visualisasi speedometer (gauge meter) "
        "probabilitas risiko XGBoost dan kartu status tri-model dinilai sangat mempermudah pemahaman kondisi emiten secara cepat tanpa "
        "harus menafsirkan angka-angka statistik yang rumit secara manual."
    )
    elements_to_insert.append(create_p(p_4_3_6_b))

    p_4_3_6_c = (
        "Tingginya skor penerimaan dari para responden dan pengakuan kelayakan dari pakar keuangan membuktikan bahwa sistem pendukung "
        "keputusan berbasis web yang dikembangkan dalam penelitian ini tidak hanya berhasil secara akademis dalam mencapai akurasi "
        "prediksi yang tinggi, tetapi juga memiliki nilai guna implementatif yang nyata sebagai instrumen mitigasi risiko finansial dan "
        "peringatan dini kebangkrutan pada industri manufaktur di Bursa Efek Indonesia."
    )
    elements_to_insert.append(create_p(p_4_3_6_c))

    # Insert into body right after target_idx
    current_idx = target_idx + 1
    for elem in elements_to_insert:
        body.insert(current_idx, elem)
        current_idx += 1

    new_xml = ET.tostring(tree, encoding='utf-8', xml_declaration=True)

    temp_docx = "535220037_wahyu_temp_4_3.docx"
    with zipfile.ZipFile(temp_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, fcontent in all_files.items():
            if fname == 'word/document.xml':
                zout.writestr(fname, new_xml)
            else:
                zout.writestr(fname, fcontent)

    shutil.move(temp_docx, doc_path)
    print(f"Successfully injected Subbab 4.3 into {doc_path}!")
    print(f"Total elements inserted: {len(elements_to_insert)}")

if __name__ == "__main__":
    main()
