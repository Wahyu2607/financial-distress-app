import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)
elements = list(body)

for i in range(815, 825):
    if i < len(elements):
        t = ''.join([n.text for n in elements[i].iter(f"{{{ns['w']}}}t") if n.text])
        print(f"[{i}] {elements[i].tag.split('}')[-1]}: {t[:100]}")
