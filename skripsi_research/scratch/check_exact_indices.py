import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)

elements = list(body)

print("--- ELEMENTS 785 to 795 ---")
for i in range(785, 796):
    el = elements[i]
    tag = el.tag.split('}')[-1]
    text = ''.join([n.text for n in el.iter(f"{{{ns['w']}}}t") if n.text])
    print(f"[{i}] <{tag}>: {text[:80]}")

print("\n--- ELEMENTS 812 to 818 ---")
for i in range(812, 819):
    el = elements[i]
    tag = el.tag.split('}')[-1]
    text = ''.join([n.text for n in el.iter(f"{{{ns['w']}}}t") if n.text])
    print(f"[{i}] <{tag}>: {text[:80]}")
