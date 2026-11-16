import zipfile
import xml.etree.ElementTree as ET

pptx_backup = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx'

with zipfile.ZipFile(pptx_backup, 'r') as z:
    for i in range(1, 15):
        s_data = z.read(f'ppt/slides/slide{i}.xml')
        s_root = ET.fromstring(s_data)
        # Check background or pics
        pics = []
        for pic in s_root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}pic'):
            blip = pic.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
            if blip is not None:
                r_embed = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                pics.append(r_embed)
        print(f"Slide {i:2d} pictures embedded: {pics}")
