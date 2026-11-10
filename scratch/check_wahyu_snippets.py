import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('535220037 wahyu.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')
root = ET.fromstring(xml_content)

paragraphs = []
for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    t = ''.join([node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text])
    if t:
        paragraphs.append(t)

for i, p in enumerate(paragraphs):
    if any(k in p for k in ['UAT', 'kuesioner', 'User Acceptance Test', 'responden', '4.2.10', 'Validasi Ahli']):
        print(f"[{i}] {p[:200]}")
