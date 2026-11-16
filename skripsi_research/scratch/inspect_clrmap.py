import zipfile
import xml.etree.ElementTree as ET

pptx_backup = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx'

with zipfile.ZipFile(pptx_backup, 'r') as z:
    root = ET.fromstring(z.read('ppt/slideMasters/slideMaster1.xml'))
    clrMap = root.find('{http://schemas.openxmlformats.org/presentationml/2006/main}clrMap')
    print("clrMap attributes:")
    for k, v in clrMap.attrib.items():
        print(f"  {k} -> {v}")
