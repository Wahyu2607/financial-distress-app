import zipfile
import xml.etree.ElementTree as ET

pptx_backup = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx'

with zipfile.ZipFile(pptx_backup, 'r') as z:
    for i in [1, 2, 7, 9, 10, 13]:
        root = ET.fromstring(z.read(f'ppt/slides/slide{i}.xml'))
        print(f"\n=== Original Slide {i} ===")
        for r in root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}r'):
            t = r.find('{http://schemas.openxmlformats.org/drawingml/2006/main}t')
            t_str = t.text if t is not None else ""
            rPr = r.find('{http://schemas.openxmlformats.org/drawingml/2006/main}rPr')
            c_str = ""
            if rPr is not None:
                for c in rPr.iter():
                    if 'Clr' in c.tag:
                        c_str += f"{c.tag.split('}')[-1]}:{c.attrib.get('val')} "
            if t_str.strip():
                print(f"  [{c_str.strip()}] {t_str.strip()[:40]}")
