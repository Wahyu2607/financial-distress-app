import zipfile
import xml.etree.ElementTree as ET

try:
    with zipfile.ZipFile('../Formulir Uji Program FTI.docx', 'r') as docx:
        xml_content = docx.read('word/document.xml')
    root = ET.fromstring(xml_content)
    texts = [node.text for node in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
    print('Length of text:', len(texts))
    print('\n'.join(texts[:100]))
except Exception as e:
    print('Error:', e)
