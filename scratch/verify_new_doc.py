import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)

elements = list(body)
print(f"Total elements in new docx: {len(elements)}")

for i, el in enumerate(elements):
    tag = el.tag.split('}')[-1]
    if tag == 'p':
        text = ''.join([n.text for n in el.iter(f"{{{ns['w']}}}t") if n.text])
        if any(k in text for k in ['Validasi Ahli', 'Tabel 4.8', 'Tabel 4.9', 'Pembahasan Validasi Ahli', 'Kuesioner Akseptansi']):
            print(f"[{i}] <p>: {text[:90]}")
    elif tag == 'tbl':
        rows = el.findall(f"{{{ns['w']}}}tr")
        # Check header
        h_row = rows[0]
        h_text = ' | '.join([''.join([n.text for n in tc.iter(f"{{{ns['w']}}}t") if n.text]) for tc in h_row.findall(f"{{{ns['w']}}}tc")])
        if any(k in h_text for k in ['Item Pengujian', 'Pernyataan Kuesioner', 'Skenario']):
            print(f"[{i}] <tbl> with {len(rows)} rows: {h_text}")
