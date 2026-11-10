import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)

elements = list(body)

for i in range(783, 796):
    el = elements[i]
    tag = el.tag.split('}')[-1]
    if tag == 'p':
        text = ''.join([n.text for n in el.iter(f"{{{ns['w']}}}t") if n.text])
        print(f"[{i}] P: {text}")
    elif tag == 'tbl':
        rows = []
        for tr in el.iter(f"{{{ns['w']}}}tr"):
            row = []
            for tc in tr.iter(f"{{{ns['w']}}}tc"):
                row.append(' '.join([''.join([n.text for n in p.iter(f"{{{ns['w']}}}t") if n.text]) for p in tc.iter(f"{{{ns['w']}}}p")]))
            rows.append(row)
        print(f"[{i}] TBL with {len(rows)} rows: header = {rows[0]}")
