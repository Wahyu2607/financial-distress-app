import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)
elements = list(body)

print("--- ELEMENTS 786-794 ---")
for i in range(786, 795):
    t = ''.join([n.text for n in elements[i].iter(f"{{{ns['w']}}}t") if n.text])
    print(f"[{i}] {elements[i].tag.split('}')[-1]}: {t}")

print("\n--- ELEMENTS 815-819 ---")
for i in range(815, 819):
    t = ''.join([n.text for n in elements[i].iter(f"{{{ns['w']}}}t") if n.text])
    print(f"[{i}] {elements[i].tag.split('}')[-1]}: {t}")
