import zipfile
import xml.etree.ElementTree as ET

pptx_backup = 'skripsi_research/docs/skripsi/2026-TEMPLATE-PPT-MOVEBEYOND_backup.pptx'

with zipfile.ZipFile(pptx_backup, 'r') as z:
    theme_xml = z.read('ppt/theme/theme1.xml')
    root = ET.fromstring(theme_xml)
    clrScheme = root.find('.//{http://schemas.openxmlformats.org/drawingml/2006/main}clrScheme')
    print('Theme Color Scheme Name:', clrScheme.attrib.get('name'))
    for child in clrScheme:
        tag = child.tag.split('}')[-1]
        color_elem = child[0]
        color_tag = color_elem.tag.split('}')[-1]
        val = color_elem.attrib.get('val') or color_elem.attrib.get('lastClr')
        print(f"  {tag}: {color_tag} = {val}")
        
    print("\n--- Inspect Original Text Colors Across Slides 1..14 ---")
    for i in range(1, 15):
        s_data = z.read(f'ppt/slides/slide{i}.xml')
        s_root = ET.fromstring(s_data)
        clrs = set()
        for c in s_root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}srgbClr'):
            clrs.add(f"srgb:{c.attrib.get('val')}")
        for c in s_root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}schemeClr'):
            clrs.add(f"scheme:{c.attrib.get('val')}")
        print(f"Slide {i:2d} colors: {list(clrs)}")
