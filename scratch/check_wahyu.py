import zipfile
import xml.etree.ElementTree as ET

for fname in ['535220037 wahyu.docx']:
    try:
        with zipfile.ZipFile(fname, 'r') as docx:
            xml_content = docx.read('word/document.xml')
        root = ET.fromstring(xml_content)
        texts = [node.text for node in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
        full_text = ' '.join(texts)
        for term in ['kuesioner', 'UAT', 'User Acceptance Test', 'responden', 'Google Formulir']:
            count = full_text.count(term)
            print(f'{fname} count of "{term}": {count}')
    except Exception as e:
        print(f'Error reading {fname}: {e}')
