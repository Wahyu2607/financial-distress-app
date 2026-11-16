import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)

elements = []
for child in body:
    tag = child.tag.split('}')[-1]
    if tag == 'p':
        text = ''.join([node.text for node in child.iter(f"{{{ns['w']}}}t") if node.text])
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

with open('scratch/elements_780_825.txt', 'w', encoding='utf-8') as out:
    for i in range(780, min(len(elements), 825)):
        el_type, data = elements[i]
        if el_type == 'p':
            out.write(f"[ELEMENT {i}] P: {data}\n")
        elif el_type == 'tbl':
            out.write(f"[ELEMENT {i}] TABLE ({len(data)} rows):\n")
            for r in data:
                out.write(f"   | {' | '.join(r)} |\n")

print("Dumped 780-825.")
