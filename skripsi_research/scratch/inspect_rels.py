import zipfile
import xml.etree.ElementTree as ET

pptx_backup = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx'

with zipfile.ZipFile(pptx_backup, 'r') as z:
    for rel_name in ['ppt/slides/_rels/slide1.xml.rels', 'ppt/slides/_rels/slide2.xml.rels', 'ppt/slides/_rels/slide6.xml.rels']:
        data = z.read(rel_name)
        root = ET.fromstring(data)
        print(f"=== {rel_name} ===")
        for rel in root:
            print(f"  {rel.attrib.get('Id')}: {rel.attrib.get('Type').split('/')[-1]} -> {rel.attrib.get('Target')}")
