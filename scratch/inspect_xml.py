import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile('update4.docx', 'r') as docx:
    xml_content = docx.read('word/document.xml')

root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
body = root.find('w:body', ns)

elements = list(body)

# Let's inspect element 784 to 792 XML
for i in [784, 785, 786, 787, 788, 789, 790, 791]:
    el = elements[i]
    tag = el.tag.split('}')[-1]
    print(f"=== ELEMENT {i} ({tag}) ===")
    xml_str = ET.tostring(el, encoding='utf-8').decode('utf-8')
    print(xml_str[:500])
    print("...\n")
