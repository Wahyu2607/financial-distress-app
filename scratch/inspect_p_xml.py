import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)
elements = list(body)

for i in [786, 787, 788, 790, 791, 793]:
    print(f"=== ELEMENT {i} ===")
    print(ET.tostring(elements[i], encoding='utf-8').decode('utf-8'))
