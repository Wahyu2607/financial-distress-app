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
            
            p_jc = ET.SubElement(pPr, f"{{{W_NS}}}jc")
            if idx == 0 and len(str(cell_text)) < 25:
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
        if "tampilan user interface" in full_text.lower():
            target_idx = idx
            break

    if target_idx == -1:
        print("Error: Subbab 'Tampilan user interface' not found in document.")
        return

    print(f"Found 'Tampilan user interface' at index {target_idx}")

    elements_to_insert = []

    # Paragraf 1: Konsep Desain Antarmuka Streamlit
    p1 = (
        "Perancangan antarmuka pengguna (user interface) pada sistem pendukung keputusan ini dikembangkan menggunakan framework "
        "Streamlit berbasis Python yang dipadukan dengan manipulasi style lembar gaya bertingkat (Cascading Style Sheets / CSS) "
        "kustom. Antarmuka dirancang dengan pendekatan desain eksekutif modern bernuansa korporat (glassmorphism financial theme) "
        "yang memadukan tata letak lebar penuh (wide layout), tipografi profesional, dan indikator warna visual tiga zona risiko "
        "operasional: hijau emerald (#10b981) untuk Safe Zone, kuning amber (#f59e0b) untuk Grey Area, dan merah crimson (#f43f5e) "
        "untuk Distress Zone. Arsitektur antarmuka dibangun ke dalam pola aplikasi satu halaman (Single Page Application / SPA) "
        "dengan navigasi dinamis berbasis bilah samping (sidebar) dan multi-tabulasi yang menyajikan pengalaman pengguna yang "
        "intuitif, cepat, dan terstruktur bagi analis keuangan, auditor, maupun manajemen emiten."
    )
    elements_to_insert.append(create_p(p1))

    # Paragraf 2: Modul Autentikasi Pengguna & RBAC
    p2 = (
        "Tahap awal interaksi pengguna diwadahi oleh modul autentikasi dan registrasi akun yang menerapkan konsep kartu geser "
        "ganda (spacer sliding theme). Modul ini mengintegrasikan protokol otentikasi ganda yang mendukung koneksi basis data cloud "
        "Supabase Auth maupun basis data relasional lokal SQLite terenkripsi. Sistem menerapkan pengendalian akses berbasis peran "
        "(Role-Based Access Control / RBAC) yang membedakan hak akses antara peran Administrator (Administrator Role) dan peran "
        "Pengguna Biasa (User / Financial Analyst Role). Pengguna dengan peran Administrator memiliki hak istimewa untuk mengonfigurasi "
        "ambang batas model, meninjau dan menyetujui akun baru, mengakses log audit, serta mengelola basis data histori diagnosis. "
        "Sebaliknya, peran analis keuangan diarahkan pada fitur analisis data keuangan emiten, simulasi skenario penyelamatan, dan "
        "pengunduhan memorandum analisis eksekutif. Guna mencegah registrasi publik tanpa otorisasi, formulir pendaftaran dilengkapi "
        "verifikasi kode akses instansi (registration passcode) yang wajib divalidasi sebelum akun pengguna diaktifkan."
    )
    elements_to_insert.append(create_p(p2))

    # Paragraf 3: Pengantar Tabel 3.6
    p3 = (
        "Struktur tata kelola antarmuka sistem web pendukung keputusan ini terbagi ke dalam enam modul fungsional utama yang saling "
        "terintegrasi. Setiap modul dirancang untuk menjalankan tanggung jawab spesifik dalam siklus analisis prediksi kondisi "
        "keuangan perusahaan. Rincian struktur navigasi dan modul antarmuka pengguna tersebut dirangkum pada Tabel 3.6."
    )
    elements_to_insert.append(create_p(p3))

    # Judul Tabel 3.6
    elements_to_insert.append(create_caption("Tabel 3.6 Struktur Navigasi dan Modul Antarmuka Sistem Web Streamlit"))
    nav_headers = ["Modul Antarmuka", "Komponen Visual / Formulir", "Fungsi dan Alur Operasional Sistem"]
    nav_rows = [
        ["Autentikasi & Registrasi", "Sliding container (Sign In / Sign Up), input kredensial, passcode verifikasi.", "Mengotentikasi identitas pengguna, validasi peran RBAC, dan registrasi akun baru terproteksi."],
        ["Input Data Multi-Sumber", "Pintasan emiten BEI, pengunggah berkas Excel/PDF, form manual 9 akun fundamental.", "Menerima dan mengekstraksi data laporan keuangan tahunan emiten dari berbagai format masukan."],
        ["Validasi Akuntansi", "Banner audit keseimbangan neraca, deteksi inkonsistensi skala nominal, audit capping X4.", "Memeriksa validitas persamaan akuntansi (Aset = Liabilitas + Ekuitas) sebelum pemodelan."],
        ["Dashboard Diagnosis Tri-Model", "3 kartu ringkasan eksekutif, gauge meter risiko XGBoost, radar konvergensi, pemicu krisis.", "Menyandingkan hasil prediksi simultan model Altman Z'', MDA Baru, dan XGBoost secara interaktif."],
        ["Simulator What-If & Breakeven", "Slider interaktif penambahan modal kerja/ekuitas, kalkulator titik impas finansial.", "Menghitung target penambahan nominal likuiditas/ekuitas agar emiten keluar dari zona distress."],
        ["Histori Prediksi & Laporan", "Tabel riwayat tersimpan, kotak pencarian kode emiten, ekspor CSV/Excel, memorandum PDF.", "Menyimpan seluruh catatan diagnosis ke basis data serta memfasilitasi pencetakan laporan eksekutif."]
    ]
    elements_to_insert.append(create_table(nav_headers, nav_rows, widths=["2000", "2800", "3700"]))

    # Paragraf 4: Modul Masukan Data Keuangan Multi-Sumber
    p4 = (
        "Keunggulan teknis dari antarmuka sistem yang dirancang terletak pada fleksibilitas modul penerimaan data keuangan. Pengguna "
        "disediakan empat kanal masukan alternatif yang disesuaikan dengan ketersediaan berkas pengguna. Kanal pertama menyediakan "
        "pintasan cepat (Quick Load Benchmark) untuk memuat data laporan keuangan historis enam emiten manufaktur BEI (ADES, ICBP, "
        "KICI, ANDI, ALTO, AISA) tahun buku 2020 hingga 2024 secara instan tanpa perlu pengunggahan berkas manual. Kanal kedua "
        "mendukung pengunggahan berkas lembar kerja Excel (.xlsx atau .xls) format taksonomi resmi BEI/IDX, di mana sistem secara "
        "otomatis memetakan lembar posisi keuangan konsolidasian dan lembar laba rugi melalui pustaka openpyxl. Kanal ketiga memfasilitasi "
        "pengunggahan berkas dokumen PDF laporan tahunan resmi (Annual Report), di mana pustaka pypdf dan regular expression mengekstrak "
        "hierarki baris angka neraca dan laba rugi. Kanal keempat menyediakan formulir isian terstruktur sembilan pos keuangan inti "
        "bagi pengguna yang ingin melakukan pengujian angka secara manual."
    )
    elements_to_insert.append(create_p(p4))

    # Paragraf 5: Validasi Keseimbangan Akuntansi
    p5 = (
        "Sebelum data diteruskan ke mesin kalkulasi model, modul antarmuka secara otomatis menjalankan lapisan pemeriksaan validitas "
        "akuntansi (Accounting Validation Guardrail). Sistem menghitung selisih matematis antara total aset dengan penjumlahan total "
        "liabilitas dan ekuitas pemegang saham. Apabila ditemukan disparitas nominal akibat perbedaan satuan masukan (misalnya total "
        "aset diinput dalam satuan Rupiah penuh triliunan sementara saldo laba diinput dalam satuan ribuan rupiah), antarmuka menampilkan "
        "banner peringatan kuning dan melakukan penyelarasan skala secara otomatis. Selain itu, rasio ekuitas terhadap total liabilitas "
        "(X4) diaudit secara visual untuk memastikan pematuhan aturan pemotongan (capping) maksimum 3,00 sesuai landasan teoritis skripsi. "
        "Spesifikasi keempat kanal masukan data keuangan tersebut dirinci pada Tabel 3.7."
    )
    elements_to_insert.append(create_p(p5))

    # Judul Tabel 3.7
    elements_to_insert.append(create_caption("Tabel 3.7 Spesifikasi Komponen Input Data Keuangan Multi-Sumber"))
    in_headers = ["Kanal Masukan", "Format Sumber Data", "Cakupan Pos Akuntansi", "Mekanisme Validasi & Parsing"]
    in_rows = [
        ["Pintasan Benchmark BEI", "Basis Data Kamus Internal (.json / Python dict)", "Total Aset, Liabilitas, Ekuitas, Modal Kerja, Saldo Laba, EBIT, Pendapatan.", "Inisialisasi instan nilai fundamental terverifikasi dari emiten acuan BEI."],
        ["Impor Lembar Kerja Excel", "Berkas .xlsx / .xls taksonomi XBRL resmi BEI", "Lembar neraca (balance sheet) dan lembar laba rugi (income statement).", "Parsing otomatis multi-sheet, pemindaian teks multi-bahasa, auto-detect skala."],
        ["Ekstraksi Berkas PDF", "Laporan tahunan resmi emiten (.pdf)", "Laporan posisi keuangan dan laba rugi komprehensif konsolidasian.", "Ekstraksi teks hierarkis layout via pypdf dan pencocokan pola regex angka moneter."],
        ["Formulir Manual Interaktif", "Form input numerik Streamlit (st.number_input)", "9 akun fundamental (CA, TA, CL, TL, RE, EBIT, Equity, Revenue, Interest).", "Pemeriksaan relasi akuntansi: TA = TL + Equity dan WC = CA - CL secara real-time."]
    ]
    elements_to_insert.append(create_table(in_headers, in_rows, widths=["1800", "2200", "2400", "2100"]))

    # Paragraf 6: Dashboard Diagnosis Tri-Model
    p6 = (
        "Bagian inti dari tampilan antarmuka sistem adalah Dashboard Diagnosis Komparatif Tri-Model. Pada halaman ini, hasil evaluasi "
        "dari ketiga metode disajikan secara berdampingan melalui tiga kartu eksekutif interaktif. Kartu pertama menampilkan skor Altman "
        "Z''-Score beserta lencana status zona (Safe Zone, Grey Area, atau Distress Zone). Kartu kedua menyajikan skor Multivariate "
        "Discriminant Analysis (MDA) hasil re-estimasi empiris Fisher berkoefisien baru BEI bersanding dengan titik potong pemisah 0,3844. "
        "Kartu ketiga menampilkan estimasi probabilitas kebangkrutan yang dihasilkan oleh model XGBoost (0% hingga 100%) yang dilengkapi "
        "visualisasi speedometer interaktif (gauge meter). Visualisasi gauge meter ini secara dinamis mengarahkan jarum indikator ke dalam "
        "tiga gradien zona risiko (hijau untuk probabilitas di bawah 35%, kuning untuk rentang waspada 35% hingga 65%, dan merah untuk "
        "probabilitas di atas 65%), sehingga pengguna dapat menangkap tingkat risiko perusahaan secara seketika."
    )
    elements_to_insert.append(create_p(p6))

    # Paragraf 7: Dekomposisi Pemicu Krisis & Simulator Breakeven
    p7 = (
        "Untuk memberikan kedalaman analisis manajerial, dashboard dilengkapi dengan panel Dekomposisi Faktor Pemicu Risiko (Financial "
        "Distress Drivers). Panel ini menyajikan diagram batang horizontal yang memperlihatkan kontribusi masing-masing rasio keuangan "
        "terhadap pembentukan skor risiko, memisahkan antara faktor pendorong kesehatan finansial (positive drivers) dan faktor penekan "
        "likuiditas (negative drivers). Melengkapi diagnosis tersebut, antarmuka menghadirkan Simulator Skenario 'What-If' dan Kalkulator "
        "Titik Impas Finansial (Break-Even Distress Point Calculator). Melalui simulator ini, pengguna dapat menggeser kendali slider "
        "untuk menyimulasikan penambahan modal kerja atau restrukturisasi utang, di mana sistem secara otomatis menghitung jumlah nominal "
        "rupiah yang dibutuhkan oleh emiten agar dapat keluar dari zona bahaya (Distress Zone) menuju zona aman operasional."
    )
    elements_to_insert.append(create_p(p7))

    # Paragraf 8: Modul Evaluasi Model & Statistik Komparatif
    p8 = (
        "Bagi keperluan analisis teknis dan akademis, antarmuka menyediakan halaman Evaluasi Model yang memuat perbandingan kinerja "
        "antar-algoritma secara komprehensif. Halaman ini menyajikan visualisasi grafis interaktif kurva Receiver Operating Characteristic "
        "(ROC-AUC) yang memperlihatkan disparitas daya pemisahan antara XGBoost (AUC = 0,9426), MDA Empiris BEI (AUC = 0,9124), dan "
        "Altman Z''-Score klasik (AUC = 0,8320). Selain itu, ditampilkan visualisasi matriks konfusi (confusion matrix) pada data pengujian "
        "141 sampel observasi serta diagram batang tingkat kepentingan fitur (gain feature importance) XGBoost yang membuktikan dominasi "
        "rasio retained earnings (X2 = 36,20%) dan rasio profitabilitas operasional (X3 = 28,15%) dalam penentuan kelangsungan hidup emiten."
    )
    elements_to_insert.append(create_p(p8))

    # Paragraf 9: Modul Riwayat Analisis & Pelaporan Eksekutif
    p9 = (
        "Modul terakhir pada antarmuka sistem adalah halaman Riwayat Analisis dan Ekspor Laporan Eksekutif. Seluruh hasil pengujian "
        "yang dilakukan oleh pengguna secara otomatis disimpan ke dalam tabel basis data yang mencatat identitas emiten, tanggal analisis, "
        "nilai rasio keuangan X1 hingga X4, serta hasil klasifikasi dari ketiga model. Pengguna dapat melakukan pencarian data berdasarkan "
        "kode emiten, menyaring riwayat berdasarkan kategori zona risiko, atau mengunduh ringkasan riwayat dalam format spreadsheet "
        "Excel (.xlsx) maupun CSV. Antarmuka juga dilengkapi fitur pencetakan Memorandum Analisis Eksekutif terformat yang siap dicetak "
        "atau diunduh sebagai berkas PDF resmi untuk keperluan pelaporan manajerial dan pemenuhan dokumentasi tata kelola perusahaan."
    )
    elements_to_insert.append(create_p(p9))

    # Insert into body right after target_idx
    current_idx = target_idx + 1
    for elem in elements_to_insert:
        body.insert(current_idx, elem)
        current_idx += 1

    new_xml = ET.tostring(tree, encoding='utf-8', xml_declaration=True)

    temp_docx = "535220037_wahyu_temp_ui.docx"
    with zipfile.ZipFile(temp_docx, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for fname, fcontent in all_files.items():
            if fname == 'word/document.xml':
                zout.writestr(fname, new_xml)
            else:
                zout.writestr(fname, fcontent)

    shutil.move(temp_docx, doc_path)
    print(f"Successfully injected Subbab 3.3 into {doc_path}!")
    print(f"Total elements inserted: {len(elements_to_insert)}")

if __name__ == "__main__":
    main()
