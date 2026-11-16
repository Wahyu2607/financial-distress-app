import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# Let's inspect the body elements (paragraphs and tables)
body = root.find('w:body', ns)

elements = []
for child in body:
    tag = child.tag.split('}')[-1]
    if tag == 'p':
        text = ''.join([node.text for node in child.iter(f"{{{ns['w']}}}t") if node.text])
        if text.strip():
            elements.append(('p', text.strip()))
    elif tag == 'tbl':
        rows = []
        for tr in child.iter(f"{{{ns['w']}}}tr"):
            row = []
            for tc in tr.iter(f"{{{ns['w']}}}tc"):
                tc_text = ' '.join([''.join([node.text for node in p.iter(f"{{{ns['w']}}}t") if node.text]) for p in tc.iter(f"{{{ns['w']}}}p")])
                row.append(tc_text.strip())
            rows.append(row)
        elements.append(('tbl', rows))

with open('scratch/update4_sections_dump.txt', 'w', encoding='utf-8') as out:
    for i, (el_type, data) in enumerate(elements):
        if el_type == 'p':
            if any(k in data for k in ['4.2.10', 'Validasi Ahli', '4.3', 'Tabel 4.8', 'Tabel 4.9', 'Tabel 4.7', 'Black Box', 'DAFTAR PUSTAKA']):
                out.write(f"\n[ELEMENT {i}] P: {data}\n")
            elif 1450 <= i <= 1650:
                out.write(f"[ELEMENT {i}] P: {data}\n")
        elif el_type == 'tbl':
            if 1450 <= i <= 1650:
                out.write(f"[ELEMENT {i}] TABLE:\n")
                for r in data:
                    out.write(f"   | {' | '.join(r)} |\n")

print("Dumped elements.")
