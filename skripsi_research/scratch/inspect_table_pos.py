import zipfile
import xml.etree.ElementTree as ET

pptx_path = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND.pptx'

with zipfile.ZipFile(pptx_path, 'r') as z:
    root = ET.fromstring(z.read('ppt/slides/slide13.xml'))
    for gf in root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}graphicFrame'):
        for c in gf:
            print("Child:", c.tag)
            if c.tag.endswith('xfrm'):
                for sub in c:
                    print("  xfrm sub:", sub.tag, sub.attrib)
